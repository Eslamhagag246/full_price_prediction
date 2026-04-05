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
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

MODEL_PATH = "mobile_price_model.pkl"
LOOKBACK = 7

FEATURE_COLS = [
    'day_index', 'dayofweek', 'day_of_month', 'month',
    'rolling_avg_3', 'rolling_avg_7', 'rolling_std_3',
    'price_lag_1', 'price_lag_3', 'price_lag_7',
    'ram_normalized', 'storage_normalized', 'specs_score',
]


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
# LOAD MODEL (FIXED)
# =========================
def load_model():
    artifact = joblib.load(MODEL_PATH)

    model = artifact["model"]
    global_day_min = artifact["global_day_min"]

    return model, global_day_min


# =========================
# SINGLE PREDICTION
# =========================
def predict_next_price(product_history: pd.DataFrame) -> float:
    model, global_day_min = load_model()

    pdf = product_history.sort_values('date').tail(LOOKBACK + 1)
    pdf = engineer_features(pdf, global_day_min)

    X = pdf.iloc[[-1]][FEATURE_COLS]

    prediction = model.predict(X)[0]

    return float(prediction)


# =========================
# MULTI-STEP FORECAST (FIXED)
# =========================
def forecast_product(product_history: pd.DataFrame, days: int = 7):
    model, global_day_min = load_model()

    pdf = product_history.copy().sort_values('date')
    predictions = []

    for _ in range(days):
        pdf_fe = engineer_features(pdf.tail(LOOKBACK + 1), global_day_min)
        X = pdf_fe.iloc[[-1]][FEATURE_COLS]

        next_price = model.predict(X)[0]
        next_date = pdf['date'].max() + pd.Timedelta(days=1)

        new_row = pdf.iloc[-1:].copy()
        new_row['date'] = next_date
        new_row['price'] = next_price

        pdf = pd.concat([pdf, new_row], ignore_index=True)

        predictions.append({
            "date": next_date,
            "predicted_price": float(next_price)
        })

    return pd.DataFrame(predictions)


# =========================
# EXPORTS (IMPORTANT)
# =========================
__all__ = [
    "predict_next_price",
    "forecast_product",
]
