import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import warnings
from supabase import create_client, Client

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


def load_and_preprocess_data() -> pd.DataFrame:
    print("📊 Loading data from Supabase...")
    products_df = fetch_all('products')
    prices_df   = fetch_all('price_history')

    products_df = products_df[
        (products_df['category'] == 'mobile') &
        (products_df['is_active'] == True)
    ]

    product_ids = set(products_df['id'])
    prices_df   = prices_df[prices_df['product_id'].isin(product_ids)]

    df = prices_df.merge(
        products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
        left_on='product_id', right_on='id', how='left',
    )

    df['price']     = pd.to_numeric(df['price'], errors='coerce')
    df              = df.dropna(subset=['price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
    df['date']      = pd.to_datetime(df['timestamp'].dt.date)
    df              = df.dropna(subset=['timestamp', 'date'])

    df['product_key'] = (
        df['name'].str.lower().str.strip() + ' '
        + df['website'].str.lower() + ' '
        + df['ram_gb'].astype(str) + ' '
        + df['storage_gb'].astype(str)
    )

    df_daily = (
        df.groupby(['product_key', 'date'])
        .agg(
            price=('price', 'mean'),
            name=('name', 'first'),
            brand=('brand', 'first'),
            website=('website', 'first'),
            ram_gb=('ram_gb', 'first'),
            storage_gb=('storage_gb', 'first'),
            URL=('url', 'last'),
            timestamp=('timestamp', 'first'),
        )
        .reset_index()
        .sort_values(['product_key', 'date'])
    )

    print(f"✅ Loaded {len(df_daily):,} daily records")
    return df_daily

def engineer_features(pdf: pd.DataFrame, day_min: pd.Timestamp) -> pd.DataFrame:
    pdf = pdf.sort_values('date').copy()

    pdf['day_index']    = (pdf['date'] - day_min).dt.days
    pdf['dayofweek']    = pdf['date'].dt.dayofweek
    pdf['day_of_month'] = pdf['date'].dt.day
    pdf['month']        = pdf['date'].dt.month

    pdf['rolling_avg_3'] = pdf['price'].rolling(3, min_periods=1).mean()
    pdf['rolling_avg_7'] = pdf['price'].rolling(7, min_periods=1).mean()
    pdf['rolling_std_3'] = pdf['price'].rolling(3, min_periods=1).std().fillna(0)

    pdf['price_lag_1'] = pdf['price'].shift(1).fillna(pdf['price'].iloc[0])
    pdf['price_lag_3'] = pdf['price'].shift(3).fillna(pdf['price'].iloc[0])
    pdf['price_lag_7'] = pdf['price'].shift(7).fillna(pdf['price'].iloc[0])

    pdf['ram_normalized']     = pdf['ram_gb']     / 16.0
    pdf['storage_normalized'] = pdf['storage_gb'] / 1024.0
    pdf['specs_score']        = (pdf['ram_gb'] / 4.0) + (pdf['storage_gb'] / 128.0)

    return pdf


def train_global_model(min_obs: int = 10, test_size: float = 0.2):
    df = load_and_preprocess_data()

    global_day_min = df['date'].min()
    print(f"📅 Global day_min (for day_index anchor): {global_day_min.date()}")

    X_train_list, X_test_list = [], []
    y_train_list, y_test_list = [], []
    skipped = 0

    for product_key in df['product_key'].unique():
        pdf = (
            df[df['product_key'] == product_key]
            .copy()
            .sort_values('date')
        )
        split_idx = int(len(pdf) * (1 - test_size))
        pdf_train = pdf.iloc[:split_idx].copy()
        pdf_test  = pdf.iloc[split_idx:].copy()
        
        upper = pdf_train['price'].quantile(0.99)
        lower = pdf_train['price'].quantile(0.01)
        pdf_train = pdf_train[(pdf_train['price'] >= lower) & (pdf_train['price'] <= upper)]

        pdf_test = pdf_test[(pdf_test['price'] >= lower) & (pdf_test['price'] <= upper)]

        if len(pdf_train) < min_obs or pdf_test.empty:
            skipped += 1
            continue

        pdf_train['target'] = pdf_train['price'].shift(-1)
        pdf_train = pdf_train.dropna(subset=['target'])

        pdf['target'] = pdf['price'].shift(-1)
        pdf = pdf.dropna(subset=['target'])

        if len(pdf) < min_obs:
            skipped += 1
            continue

        split_idx = int(len(pdf) * (1 - test_size))
        pdf_train = pdf.iloc[:split_idx].copy()
        pdf_test  = pdf.iloc[split_idx:].copy()

        if pdf_train.empty or pdf_test.empty:
            skipped += 1
            continue

        pdf_train_fe = engineer_features(pdf_train, global_day_min)

        context          = pdf_train.iloc[-LOOKBACK:].copy()
        pdf_test_ctx     = pd.concat([context, pdf_test], ignore_index=True)
        pdf_test_fe_full = engineer_features(pdf_test_ctx, global_day_min)
        pdf_test_fe      = pdf_test_fe_full.iloc[len(context):].copy()

        X_train_list.append(pdf_train_fe[FEATURE_COLS])
        y_train_list.append(pdf_train_fe['target'])
        X_test_list.append(pdf_test_fe[FEATURE_COLS])
        y_test_list.append(pdf_test_fe['target'])

    if not X_train_list:
        raise RuntimeError("No products met the minimum observation threshold.")

    print(f"ℹ️  Skipped {skipped} products (too few observations)")

    X_train = pd.concat(X_train_list, ignore_index=True)
    X_test  = pd.concat(X_test_list,  ignore_index=True)
    y_train = pd.concat(y_train_list, ignore_index=True)
    y_test  = pd.concat(y_test_list,  ignore_index=True)

    print(f"\n🏋️  Training on {len(X_train):,} samples | evaluating on {len(X_test):,} samples")

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_train_pred = model.predict(X_train)
    y_test_pred  = model.predict(X_test)

    print("\n" + "=" * 60)
    print("📊 MODEL PERFORMANCE")
    print("=" * 60)

    print("\n🟢 TRAINING")
    print(f"   MAE : {mean_absolute_error(y_train, y_train_pred):>12,.2f} EGP")
    print(f"   RMSE: {np.sqrt(mean_squared_error(y_train, y_train_pred)):>12,.2f} EGP")
    print(f"   R²  : {r2_score(y_train, y_train_pred):>12.4f}")

    print("\n🔵 TEST")
    print(f"   MAE : {mean_absolute_error(y_test, y_test_pred):>12,.2f} EGP")
    print(f"   RMSE: {np.sqrt(mean_squared_error(y_test, y_test_pred)):>12,.2f} EGP")
    print(f"   R²  : {r2_score(y_test, y_test_pred):>12.4f}")

    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae  = mean_absolute_error(y_test,  y_test_pred)
    gap_ratio = test_mae / train_mae

    print(f"\n⚖️  Train/Test MAE ratio: {gap_ratio:.2f}x")
    if gap_ratio > 3:
        print("   ⚠️  Large gap — consider feature review or a more powerful model.")
    else:
        print("   ✅ Gap looks healthy.")

    artifact = {"model": model, "global_day_min": global_day_min}
    joblib.dump(artifact, MODEL_PATH)
    print(f"\n💾 Model + day_min anchor saved → {MODEL_PATH}")

    return model, global_day_min


def predict_next_price(artifact: dict, product_history: pd.DataFrame) -> float:
 
    model        = artifact["model"]
    global_day_min = artifact["global_day_min"]

    pdf      = product_history.sort_values('date').copy().tail(LOOKBACK + 1)
    pdf      = engineer_features(pdf, global_day_min)
    last_row = pdf.iloc[[-1]][FEATURE_COLS]
    return float(model.predict(last_row)[0])


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TRAINING GLOBAL MOBILE PRICE MODEL")
    print("=" * 60)
    train_global_model(min_obs=10, test_size=0.2)
