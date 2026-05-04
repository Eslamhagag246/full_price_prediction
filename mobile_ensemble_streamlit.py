import pandas as pd
import numpy as np
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from datetime import timedelta
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# CONFIGURATION

MODEL_PATH = "mobile_ensemble_model.pkl"
LOOKBACK = 7

FEATURE_COLS = [
    'day_index', 'dayofweek', 'day_of_month', 'month',
    'current_price',
    'rolling_avg_3', 'rolling_avg_7',
    'rolling_std_3', 'rolling_std_7',
    'price_lag_1', 'price_lag_3', 'price_lag_7',
    'pct_change_1', 'pct_change_3',
    'gap_to_avg_3', 'gap_to_avg_7',
    'ram_normalized', 'storage_normalized', 'specs_score'
]

# FEATURE ENGINEERING
def engineer_features(pdf: pd.DataFrame, day_min: pd.Timestamp) -> pd.DataFrame:
    pdf = pdf.sort_values('date').copy()

    pdf['day_index'] = (pdf['date'] - day_min).dt.days
    pdf['dayofweek'] = pdf['date'].dt.dayofweek
    pdf['day_of_month'] = pdf['date'].dt.day
    pdf['month'] = pdf['date'].dt.month

    pdf['current_price'] = pdf['price']
    pdf['price_shift'] = pdf['price'].shift(1)

    pdf['rolling_avg_3'] = pdf['price_shift'].rolling(3).mean()
    pdf['rolling_avg_7'] = pdf['price_shift'].rolling(7).mean()
    pdf['rolling_std_3'] = pdf['price_shift'].rolling(3).std()
    pdf['rolling_std_7'] = pdf['price_shift'].rolling(7).std()

    pdf['price_lag_1'] = pdf['price'].shift(1)
    pdf['price_lag_3'] = pdf['price'].shift(3)
    pdf['price_lag_7'] = pdf['price'].shift(7)

    pdf['pct_change_1'] = pdf['price_shift'].pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
    pdf['pct_change_3'] = pdf['price_shift'].pct_change(3).replace([np.inf, -np.inf], np.nan).fillna(0)

    pdf['ram_normalized'] = pdf['ram_gb'] / 16.0
    pdf['storage_normalized'] = pdf['storage_gb'] / 1024.0
    pdf['specs_score'] = (pdf['ram_gb'] / 4.0) + (pdf['storage_gb'] / 128.0)

    pdf['gap_to_avg_3'] = pdf['current_price'] - pdf['rolling_avg_3']
    pdf['gap_to_avg_7'] = pdf['current_price'] - pdf['rolling_avg_7']

    return pdf

# ENSEMBLE HELPERS

def build_models():
    model_lgb = LGBMRegressor(
        n_estimators=500,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42
    )

    model_xgb = XGBRegressor(
        n_estimators=500,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42,
        objective='reg:squarederror'
    )

    return model_lgb, model_xgb

def apply_weights(pred_lgb, pred_xgb, weights):
    return (
        weights['lightgbm'] * pred_lgb +
        weights['xgboost'] * pred_xgb
    )

# LOAD MODEL 

def load_global_model():
    
    artifact = joblib.load(MODEL_PATH)
    print(f" Loaded mobile ensemble model from {MODEL_PATH}")
    return artifact

# FORECAST PRODUCT 
def forecast_product(product_df, days_ahead=7, model=None):
    
    model_lgb = model["lightgbm"]
    model_xgb = model["xgboost"]
    weights = model["weights"]
    global_day_min = model["global_day_min"]

    pdf = product_df.copy().sort_values('date')

    pdf['date'] = pd.to_datetime(pdf['date'])
    pdf['price'] = pd.to_numeric(pdf['price'], errors='coerce')
    pdf = pdf.dropna(subset=['date', 'price']).copy()

    actual_last_price = float(pdf['price'].iloc[-1])
    last_date = pd.to_datetime(pdf['date'].iloc[-1])
    last_ram = float(pdf['ram_gb'].iloc[-1])
    last_storage = float(pdf['storage_gb'].iloc[-1])

    min_price = float(pdf['price'].min())
    max_price = float(pdf['price'].max())
    avg_price = float(pdf['price'].mean())

    pdf_fe = engineer_features(pdf.copy(), global_day_min)
    pdf['rolling_avg_7'] = pdf_fe['rolling_avg_7']

    forecast_prices = []
    forecast_dates = []
    context = pdf.tail(LOOKBACK).copy()
    rolling_price = actual_last_price

    for i in range(1, days_ahead + 1):
        next_date = last_date + timedelta(days=i)

        new_row = pd.DataFrame({
            'date': [next_date],
            'price': [actual_last_price],
            'ram_gb': [last_ram],
            'storage_gb': [last_storage]
        })

        temp_df = pd.concat([context, new_row], ignore_index=True)
        temp_fe = engineer_features(temp_df, global_day_min)
        X_pred = temp_fe.iloc[[-1]][FEATURE_COLS]

        pred_lgb = float(model_lgb.predict(X_pred)[0])
        pred_xgb = float(model_xgb.predict(X_pred)[0])
        predicted_price = float(apply_weights(pred_lgb, pred_xgb, weights))

        forecast_prices.append(predicted_price)
        forecast_dates.append(next_date)

        new_row['price'] = predicted_price
        context = pd.concat([context.iloc[1:], new_row], ignore_index=True)
        rolling_price = predicted_price 

    if len(pdf_fe) > 1:
        pdf_fe['target'] = pdf_fe['price'].shift(-1)
        pdf_fe_val = pdf_fe.dropna(subset=['target'] + FEATURE_COLS)

        if len(pdf_fe_val) > 0:
            X_val = pdf_fe_val[FEATURE_COLS]
            y_val = pdf_fe_val['target']
            pred_lgb_val = model_lgb.predict(X_val)
            pred_xgb_val = model_xgb.predict(X_val)
            y_pred = apply_weights(pred_lgb_val, pred_xgb_val, weights)
            mae = float(mean_absolute_error(y_val, y_pred))
        else:
            mae = avg_price * 0.05
    else:
        mae = avg_price * 0.05

    if avg_price > 0 and mae / avg_price < 0.05:
        confidence = "High"
    elif avg_price > 0 and mae / avg_price < 0.10:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        'forecast_dates': forecast_dates,
        'forecast_prices': forecast_prices,
        'last_price': actual_last_price,
        'min_price': min_price,
        'max_price': max_price,
        'avg_price': avg_price,
        'mae': mae,
        'confidence': confidence,
        'n_obs': len(pdf),
        'pdf': pdf
    }
# TRAINING FUNCTION 

def train_global_model():
    from supabase import create_client, Client

    SUPABASE_URL = "https://ryiqzurrmvaftbnpiopx.supabase.co"
    SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ5aXF6dXJybXZhZnRibnBpb3B4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzcwMDY5NywiZXhwIjoyMDg5Mjc2Njk3fQ.7uVZj7t93AWOZd3CsU__AZTXQyNDUxM3IN3VWurzG04'


    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def fetch_all(table_name):
        all_data, offset, limit = [], 0, 1000
        while True:
            res = supabase.table(table_name).select("*").range(offset, offset + limit - 1).execute()
            data = res.data
            if not data:
                break
            all_data.extend(data)
            if len(data) < limit:
                break
            offset += limit
        return pd.DataFrame(all_data)

    def load_training_data():
        products = fetch_all('products')
        prices = fetch_all('price_history')

        products = products[(products['category'] == 'mobile') & (products['is_active'] == True)]
        prices = prices[prices['product_id'].isin(products['id'])]

        df = prices.merge(
            products[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='inner'
        )

        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df = df.dropna(subset=['price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['date'] = pd.to_datetime(df['timestamp'].dt.date)

        df['product_key'] = (
            df['name'].str.lower().fillna('unknown') + '_' +
            df['ram_gb'].astype(str) + '_' +
            df['storage_gb'].astype(str)
        )

        return (
            df.groupby(['product_key', 'date'])
            .agg({'price': 'mean', 'ram_gb': 'first', 'storage_gb': 'first'})
            .reset_index()
            .sort_values(['product_key', 'date'])
        )

    def add_targets_train(df):
        df = df.sort_values(['product_key', 'date']).copy()
        df['target'] = df.groupby('product_key')['price'].shift(-1)
        df['target_date'] = df.groupby('product_key')['date'].shift(-1)
        return df.dropna(subset=['target', 'target_date']).copy()

    def compute_metrics(y_true, y_pred):
        return {
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'r2': float(r2_score(y_true, y_pred)),
        }

    # Fixed weights
    weights = {
        'lightgbm': 0.85,
        'xgboost': 0.15,
    }

    print("📊 Loading mobile data from Supabase...")
    df = add_targets_train(load_training_data())

    day_min = df['date'].min()

    train_fe = engineer_features(df.copy(), day_min)
    train_fe = train_fe.dropna(subset=FEATURE_COLS + ['target'])

    X_train = train_fe[FEATURE_COLS]
    y_train = train_fe['target']

    print(" Training final deployment model on full dataset...")
    model_lgb, model_xgb = build_models()
    model_lgb.fit(X_train, y_train)
    model_xgb.fit(X_train, y_train)

    pred_lgb_train = model_lgb.predict(X_train)
    pred_xgb_train = model_xgb.predict(X_train)
    y_train_pred = apply_weights(pred_lgb_train, pred_xgb_train, weights)

    train_metrics = compute_metrics(y_train, y_train_pred)

    artifact = {
        "lightgbm": model_lgb,
        "xgboost": model_xgb,
        "weights": weights,
        "feature_cols": FEATURE_COLS,
        "global_day_min": day_min,
        "last_train_date": df['date'].max(),
        "mode": "final_deployment"
    }
    joblib.dump(artifact, MODEL_PATH)

    print("\n" + "=" * 60)
    print(" MOBILE ENSEMBLE FINAL DEPLOYMENT MODEL")
    print("=" * 60)
    print("Training used: FULL AVAILABLE DATASET")
    print(f"Train MAE     : {train_metrics['mae']:,.2f}")
    print(f"Train RMSE    : {train_metrics['rmse']:,.2f}")
    print(f"Train R²      : {train_metrics['r2']:.4f}")
    print(f"Weights       : LGB={weights['lightgbm']:.4f}, XGB={weights['xgboost']:.4f}")
    print(f"Last train date: {df['date'].max()}")
    print(f"💾 Saved model: {MODEL_PATH}")

    return artifact

# MAIN 
if __name__ == "__main__":
    print("=" * 60)
    print(" TRAINING GLOBAL MOBILE ENSEMBLE MODEL")
    print("=" * 60)
    train_global_model()
