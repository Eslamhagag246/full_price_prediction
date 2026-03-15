import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from datetime import timedelta
import joblib
import os
import warnings
warnings.filterwarnings('ignore')


# ═══════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════

def load_and_preprocess_data(filepath='tablets_cleaned_continuous.csv'):
    """Load and preprocess tablet data - FIXED default filepath"""
    
    df = pd.read_csv(filepath)

    # Clean price
    df['price'] = df['price'].astype(str)
    df['price'] = df['price'].str.replace('EGP', '', regex=False)
    df['price'] = df['price'].str.replace(',', '', regex=False)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])

    # Parse dates
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['date'] = df['timestamp'].dt.date
    df['date'] = pd.to_datetime(df['date'])

    # Create product key
    df['product_key'] = (
        df['name'].str.lower().str.strip() + ' ' +
        df['website'].str.lower() + ' ' +
        df['ram_gb'].astype(str) + ' ' +
        df['storage_gb'].astype(str)
    )

    # Daily aggregation
    df_daily = df.groupby(['product_key', 'date']).agg({
        'price': 'mean',
        'name': 'first',
        'brand': 'first',
        'website': 'first',
        'ram_gb': 'first',
        'storage_gb': 'first',
        'URL': 'last',
        'timestamp': 'first'
    }).reset_index()

    df_daily = df_daily.sort_values(['product_key', 'date'])

    return df_daily


# ═══════════════════════════════════════════════════════════
# FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════

def engineer_features(pdf):
    """Engineer features for ML model"""
    
    pdf = pdf.sort_values('date').copy()

    # Time features
    pdf['day_index'] = (pdf['date'] - pdf['date'].min()).dt.days
    pdf['dayofweek'] = pdf['date'].dt.dayofweek
    pdf['day_of_month'] = pdf['date'].dt.day
    pdf['month'] = pdf['date'].dt.month

    # Rolling features (shifted to avoid data leakage)
    pdf['rolling_avg_3'] = pdf['price'].rolling(3, min_periods=1).mean().shift(1)
    pdf['rolling_avg_7'] = pdf['price'].rolling(7, min_periods=1).mean().shift(1)
    pdf['rolling_std_3'] = pdf['price'].rolling(3, min_periods=1).std().shift(1)

    # Lag features
    pdf['price_lag_1'] = pdf['price'].shift(1)
    pdf['price_lag_3'] = pdf['price'].shift(3)
    pdf['price_lag_7'] = pdf['price'].shift(7)
    
    # Change features - CREATE BEFORE DROPNA!
    pdf['pct_change_1'] = pdf['price'].pct_change().fillna(0)
    pdf['pct_change_3'] = pdf['price'].pct_change(3).fillna(0)
    
    # Drop NaN rows AFTER creating all features
    pdf = pdf.dropna()

    # Device specs
    pdf['ram_normalized'] = pdf['ram_gb'] / 16.0
    pdf['storage_normalized'] = pdf['storage_gb'] / 1024.0
    pdf['specs_score'] = (pdf['ram_gb'] / 4.0) + (pdf['storage_gb'] / 128.0)

    return pdf


# ═══════════════════════════════════════════════════════════
# GLOBAL MODEL TRAINING
# ═══════════════════════════════════════════════════════════

FEATURE_COLS = [
    'day_index', 'dayofweek', 'day_of_month', 'month',
    'rolling_avg_3', 'rolling_avg_7', 'rolling_std_3',
    'price_lag_1', 'price_lag_3', 'price_lag_7',
    'pct_change_1', 'pct_change_3',
    'ram_normalized', 'storage_normalized', 'specs_score'
]

MODEL_PATH = "tablet_price_model.pkl"


def train_global_model(filepath='tablets_cleaned_continuous.csv', min_obs=10, test_size=0.2):
    """
    Train a single global model on ALL products
    
    Benefits of global model:
    - Better generalization
    - More training data
    - Works for new products
    - Only one .pkl file to maintain
    """
    
    df = load_and_preprocess_data(filepath)

    X_train_list = []
    y_train_list = []
    X_test_list = []
    y_test_list = []

    print(f"\n📊 Processing products...")
    processed = 0

    for product_key in df['product_key'].unique():
        pdf = df[df['product_key'] == product_key].copy()

        if len(pdf) < min_obs:
            continue

        pdf = engineer_features(pdf)
        pdf = pdf.dropna()

        if len(pdf) < 5:  # Need at least 5 samples after feature engineering
            continue

        X = pdf[FEATURE_COLS]
        y = pdf['price']

        # Time-based split
        split_idx = int(len(pdf) * (1 - test_size))

        X_train_list.append(X.iloc[:split_idx])
        y_train_list.append(y.iloc[:split_idx])

        X_test_list.append(X.iloc[split_idx:])
        y_test_list.append(y.iloc[split_idx:])
        
        processed += 1
        if processed % 50 == 0:
            print(f"   Processed {processed} products...", end='\r')

    print(f"\n   ✅ Processed {processed} products")

    # Concatenate all data
    X_train = pd.concat(X_train_list)
    y_train = pd.concat(y_train_list)
    X_test = pd.concat(X_test_list)
    y_test = pd.concat(y_test_list)

    print(f"\n📈 Training global model...")
    print(f"   Training samples: {len(X_train):,}")
    print(f"   Testing samples: {len(X_test):,}")

    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    # Metrics
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

    print("\n" + "="*60)
    print("📊 GLOBAL MODEL PERFORMANCE")
    print("="*60)
    print("\nTRAINING PERFORMANCE")
    print(f"   MAE:  {train_mae:,.2f} EGP")
    print(f"   R²:   {train_r2:.4f}")
    print(f"   RMSE: {train_rmse:,.2f} EGP")
    print("\nTEST PERFORMANCE")
    print(f"   MAE:  {test_mae:,.2f} EGP")
    print(f"   R²:   {test_r2:.4f}")
    print(f"   RMSE: {test_rmse:,.2f} EGP")

    return model


def save_global_model(model):
    """Save the global model to disk"""
    joblib.dump(model, MODEL_PATH)
    print(f"\n💾 Model saved: {MODEL_PATH}")


def load_global_model():
    """Load the global model from disk"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


# ═══════════════════════════════════════════════════════════
# FORECASTING
# ═══════════════════════════════════════════════════════════

def forecast_product(pdf, days_ahead=7, model=None):
    """
    Generate price forecast using global model
    
    Args:
        pdf: Product dataframe
        days_ahead: Number of days to forecast
        model: Pre-loaded model (optional)
        
    Returns:
        Dictionary with forecast and metrics
    """
    
    pdf = engineer_features(pdf)

    X = pdf[FEATURE_COLS]
    y = pdf['price']

    # Load model if not provided
    if model is None:
        model = load_global_model()

    # Get history
    history_prices = list(pdf['price'].values)
    last_date = pdf['date'].iloc[-1]
    last_day_index = pdf['day_index'].iloc[-1]

    forecasts = []

    # Generate forecasts
    for i in range(days_ahead):
        future_date = last_date + timedelta(days=i+1)

        price_lag_1 = history_prices[-1]
        price_lag_3 = history_prices[-3] if len(history_prices) >= 3 else history_prices[0]
        price_lag_7 = history_prices[-7] if len(history_prices) >= 7 else history_prices[0]

        rolling_avg_3 = np.mean(history_prices[-3:])
        rolling_avg_7 = np.mean(history_prices[-7:])
        rolling_std_3 = np.std(history_prices[-3:])

        row = [[
            last_day_index+i+1,
            future_date.dayofweek,
            future_date.day,
            future_date.month,
            rolling_avg_3,
            rolling_avg_7,
            rolling_std_3,
            price_lag_1,
            price_lag_3,
            price_lag_7,
            0,  # pct_change_1
            0,  # pct_change_3
            pdf['ram_normalized'].iloc[-1],
            pdf['storage_normalized'].iloc[-1],
            pdf['specs_score'].iloc[-1]
        ]]

        pred = model.predict(row)[0]
        forecasts.append(pred)
        history_prices.append(pred)

    forecast_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]

    # Calculate metrics
    y_pred = model.predict(X)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)

    # Confidence
    n = len(pdf)
    if n >= 30:
        confidence = "High"
    elif n >= 15:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        'pdf': pdf,
        'forecast_dates': forecast_dates,
        'forecast_prices': np.array(forecasts),
        'mae': mae,
        'r2': r2,
        'last_price': float(pdf['price'].iloc[-1]),
        'avg_price': float(pdf['price'].mean()),
        'min_price': float(pdf['price'].min()),
        'max_price': float(pdf['price'].max()),
        'n_obs': n,
        'confidence': confidence,
        'model_type': 'Global Linear Regression'
    }


# ═══════════════════════════════════════════════════════════
# MAIN - TRAIN MODEL
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*70)
    print("🚀 TRAINING GLOBAL TABLET PRICE MODEL")
    print("="*70)

    # For local training, use your local path
    # For Streamlit Cloud, use relative path
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Try local path first, fall back to relative
        local_path = r"C:\projects\final_project\full_price_prediction\tablets_cleaned_continuous.csv"
        if os.path.exists(local_path):
            filepath = local_path
        else:
            filepath = 'tablets_cleaned_continuous.csv'

    print(f"\n📁 Using data file: {filepath}")

    model = train_global_model(filepath)
    save_global_model(model)

    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE")
    print("="*70)
    print(f"\n💡 To use in Streamlit:")
    print(f"   1. Copy {MODEL_PATH} to your Streamlit app directory")
    print(f"   2. The app will automatically load it")
    print("="*70)
