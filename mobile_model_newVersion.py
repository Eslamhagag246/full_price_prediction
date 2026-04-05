import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from supabase import create_client, Client 
from supabase_loader import load_and_preprocess_data
from datetime import timedelta ,datetime , time
import joblib
import os
import warnings
warnings.filterwarnings('ignore')



SUPABASE_URL = "https://ryiqzurrmvaftbnpiopx.supabase.co"
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ5aXF6dXJybXZhZnRibnBpb3B4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzcwMDY5NywiZXhwIjoyMDg5Mjc2Njk3fQ.7uVZj7t93AWOZd3CsU__AZTXQyNDUxM3IN3VWurzG04'

MODEL_PATH = "mobile_price_model.pkl"
LOOKBACK = 7

FEATURE_COLS = [
    'day_index', 'dayofweek', 'day_of_month', 'month',
    'rolling_avg_3', 'rolling_avg_7', 'rolling_std_3',
    'price_lag_1', 'price_lag_3', 'price_lag_7',
    'ram_normalized', 'storage_normalized', 'specs_score',
]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# FETCH DATA
# =========================
def fetch_all(table_name: str) -> pd.DataFrame:
    all_data = []
    limit = 1000
    offset = 0

    while True:
        response = (
            supabase.table(table_name)
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )

        data = response.data
        if not data:
            break

        all_data.extend(data)

        if len(data) < limit:
            break

        offset += limit

    return pd.DataFrame(all_data)


# =========================
# PREPROCESS
# =========================
def load_and_preprocess_data() -> pd.DataFrame:
    products_df = fetch_all('products')
    prices_df   = fetch_all('price_history')

    products_df = products_df[
        (products_df['category'] == 'mobile') &
        (products_df['is_active'] == True)
    ]

    prices_df = prices_df[prices_df['product_id'].isin(products_df['id'])]

    df = prices_df.merge(
        products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb']],
        left_on='product_id', right_on='id', how='left',
    )

    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = pd.to_datetime(df['timestamp'].dt.date)

    df['product_key'] = (
        df['name'].str.lower().str.strip() + ' ' +
        df['website'].str.lower() + ' ' +
        df['ram_gb'].astype(str) + ' ' +
        df['storage_gb'].astype(str)
    )

    df_daily = (
        df.groupby(['product_key', 'date'])
        .agg(
            price=('price', 'mean'),
            ram_gb=('ram_gb', 'first'),
            storage_gb=('storage_gb', 'first'),
        )
        .reset_index()
        .sort_values(['product_key', 'date'])
    )

    return df_daily


# =========================
# FEATURE ENGINEERING
# =========================
def engineer_features(pdf: pd.DataFrame, day_min: pd.Timestamp) -> pd.DataFrame:
    pdf = pdf.sort_values('date').copy()

    pdf['day_index'] = (pdf['date'] - day_min).dt.days
    pdf['dayofweek'] = pdf['date'].dt.dayofweek
    pdf['day_of_month'] = pdf['date'].dt.day
    pdf['month'] = pdf['date'].dt.month

    pdf['rolling_avg_3'] = pdf['price'].rolling(3, min_periods=1).mean()
    pdf['rolling_avg_7'] = pdf['price'].rolling(7, min_periods=1).mean()
    pdf['rolling_std_3'] = pdf['price'].rolling(3, min_periods=1).std().fillna(0)

    pdf['price_lag_1'] = pdf['price'].shift(1).fillna(pdf['price'].iloc[0])
    pdf['price_lag_3'] = pdf['price'].shift(3).fillna(pdf['price'].iloc[0])
    pdf['price_lag_7'] = pdf['price'].shift(7).fillna(pdf['price'].iloc[0])

    pdf['ram_normalized'] = pdf['ram_gb'] / 16.0
    pdf['storage_normalized'] = pdf['storage_gb'] / 1024.0
    pdf['specs_score'] = (pdf['ram_gb'] / 4.0) + (pdf['storage_gb'] / 128.0)

    return pdf


# =========================
# TRAIN
# =========================
def train_model():
    df = load_and_preprocess_data()
    global_day_min = df['date'].min()

    X_list, y_list = [], []

    for key in df['product_key'].unique():
        pdf = df[df['product_key'] == key].copy()

        if len(pdf) < 10:
            continue

        pdf['target'] = pdf['price'].shift(-1)
        pdf = pdf.dropna()

        pdf = engineer_features(pdf, global_day_min)

        X_list.append(pdf[FEATURE_COLS])
        y_list.append(pdf['target'])

    X = pd.concat(X_list)
    y = pd.concat(y_list)

    model = LinearRegression()
    model.fit(X, y)

    # ✅ SAVE AS DICT (IMPORTANT)
    artifact = {
        "model": model,
        "global_day_min": global_day_min
    }

    joblib.dump(artifact, MODEL_PATH)
    print("✅ Model saved!")


# =========================
# LOAD MODEL (FIXED)
# =========================
def load_model():
    artifact = joblib.load(MODEL_PATH)

    # ✅ IMPORTANT FIX HERE
    model = artifact["model"]
    global_day_min = artifact["global_day_min"]

    return model, global_day_min


# =========================
# PREDICT (SAFE VERSION)
# =========================
def predict_next_price(product_history: pd.DataFrame):
    model, global_day_min = load_model()

    pdf = product_history.sort_values('date').tail(LOOKBACK + 1)
    pdf = engineer_features(pdf, global_day_min)

    X = pdf.iloc[[-1]][FEATURE_COLS]

    prediction = model.predict(X)[0]

    return float(prediction)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    print("🚀 Training model...")
    train_model()

    print("🔮 Running test prediction...")

    df = load_and_preprocess_data()
    sample_product = df[df['product_key'] == df['product_key'].iloc[0]]

    pred = predict_next_price(sample_product)

    print(f"✅ Predicted next price: {pred:.2f} EGP")
