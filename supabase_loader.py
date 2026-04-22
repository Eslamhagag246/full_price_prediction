import streamlit as st
import os
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
from typing import Optional
# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

SUPABASE_URL = "https://ryiqzurrmvaftbnpiopx.supabase.co"
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ5aXF6dXJybXZhZnRibnBpb3B4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzcwMDY5NywiZXhwIjoyMDg5Mjc2Njk3fQ.7uVZj7t93AWOZd3CsU__AZTXQyNDUxM3IN3VWurzG04'

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def normalize_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def normalize_website(value) -> str:
    v = normalize_text(value).replace(" ", "")
    aliases = {
        "dream2000": "dream2000",
        "dream2000.com": "dream2000",
        "dream2000eg": "dream2000",
        "dream2000egypt": "dream2000",
        "2b": "2b",
        "twob": "2b",
        "btech": "btech",
        "b-tech": "btech",
        "jumia": "jumia",
        "jumiaegypt": "jumia",
        "dubaiphone": "dubaiphone",
        "dubai phone": "dubaiphone",
    }
    return aliases.get(v, v)


def normalize_int(value, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def build_product_key(name, website, ram_gb, storage_gb) -> str:
    return (
        f"{normalize_text(name)} "
        f"{normalize_website(website)} "
        f"{normalize_int(ram_gb)} "
        f"{normalize_int(storage_gb)}"
    ).strip()


def fetch_all_paginated(table_name: str, select_cols: str, page_size: int = 1000) -> pd.DataFrame:
    all_rows = []
    start = 0

    while True:
        response = (
            supabase.table(table_name)
            .select(select_cols)
            .range(start, start + page_size - 1)
            .execute()
        )

        rows = response.data or []
        if not rows:
            break

        all_rows.extend(rows)

        if len(rows) < page_size:
            break

        start += page_size

    return pd.DataFrame(all_rows)

@st.cache_data(ttl=3600) 
def get_all_products_cached():
    try:
        products_df = fetch_all_paginated(
            "products",
            "id,name,brand,ram_gb,storage_gb,website,category,url,is_active,first_seen,last_seen,created_at,updated_at"
        )

        if products_df.empty:
            return pd.DataFrame()

        if "is_active" in products_df.columns:
            products_df = products_df[products_df["is_active"] == True].copy()

        products_df["name"] = products_df["name"].apply(normalize_text)
        products_df["brand"] = products_df["brand"].fillna("").apply(normalize_text)
        products_df["website"] = products_df["website"].apply(normalize_website)
        products_df["category"] = products_df["category"].apply(normalize_text)
        products_df["ram_gb"] = products_df["ram_gb"].apply(normalize_int)
        products_df["storage_gb"] = products_df["storage_gb"].apply(normalize_int)
        products_df["url"] = products_df["url"].fillna("").astype(str).str.strip()

        products_df["product_key"] = products_df.apply(
            lambda r: build_product_key(r["name"], r["website"], r["ram_gb"], r["storage_gb"]),
            axis=1
        )

        products_df = products_df.drop_duplicates(subset=["id"], keep="last").copy()
        return products_df

    except Exception as e:
        print(f"❌ Error loading products: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600) 
def get_all_prices_cached():
    try:
        prices_df = fetch_all_paginated(
            "price_history",
            "id,product_id,price,date,timestamp,created_at"
        )

        if prices_df.empty:
            return pd.DataFrame()

        prices_df["price"] = pd.to_numeric(prices_df["price"], errors="coerce")
        prices_df["timestamp"] = pd.to_datetime(prices_df["timestamp"], errors="coerce", utc=True)
        prices_df["created_at"] = pd.to_datetime(prices_df["created_at"], errors="coerce", utc=True)
        prices_df["date"] = pd.to_datetime(prices_df["date"], errors="coerce")

        prices_df = prices_df.dropna(subset=["product_id", "price", "date"]).copy()
        return prices_df

    except Exception as e:
        print(f"❌ Error loading prices: {e}")
        return pd.DataFrame()
# ═══════════════════════════════════════════════════════════
# LOAD TABLETS (WITH CACHE)
# ═══════════════════════════════════════════════════════════

def load_category_from_supabase(category: str) -> pd.DataFrame:
    try:
        category = normalize_text(category)
        print(f"📊 Loading {category}s from Supabase (cached)...")

        products_df = get_all_products_cached()
        prices_df = get_all_prices_cached()

        if products_df.empty or prices_df.empty:
            return pd.DataFrame()

        products_df = products_df[products_df["category"] == category].copy()

        if products_df.empty:
            print(f"⚠️ No {category} products found")
            return pd.DataFrame()

        print(f"   Found {len(products_df)} active {category} products")

        product_ids = set(products_df["id"])
        prices_df = prices_df[prices_df["product_id"].isin(product_ids)].copy()

        print(f"   Filtered to {len(prices_df):,} {category} price records")

        df = prices_df.merge(
            products_df[
                ["id", "product_key", "name", "brand", "website", "category", "ram_gb", "storage_gb", "url"]
            ],
            left_on="product_id",
            right_on="id",
            how="left"
        )

        df.rename(columns={"url": "URL"}, inplace=True)

        df["name"] = df["name"].apply(normalize_text)
        df["brand"] = df["brand"].fillna("").apply(normalize_text)
        df["website"] = df["website"].apply(normalize_website)
        df["category"] = df["category"].apply(normalize_text)
        df["ram_gb"] = df["ram_gb"].apply(normalize_int)
        df["storage_gb"] = df["storage_gb"].apply(normalize_int)
        df["product_key"] = df.apply(
            lambda r: build_product_key(r["name"], r["website"], r["ram_gb"], r["storage_gb"]),
            axis=1
        )

        df = df.dropna(subset=["date"]).copy()
        df = df.drop(columns=["id"], errors="ignore")
        df = df.sort_values(["product_key", "date", "timestamp"], kind="stable").reset_index(drop=True)

        print(f"✅ Loaded {len(df):,} {category} records (CACHED)")
        return df

    except Exception as e:
        print(f"❌ Error loading {category}: {e}")
        return pd.DataFrame()


def load_tablets_from_supabase() -> pd.DataFrame:
    return load_category_from_supabase("tablet")


def load_mobiles_from_supabase() -> pd.DataFrame:
    return load_category_from_supabase("mobile")
# ═══════════════════════════════════════════════════════════
# PRICE RECOMMENDER SYSTEM
# ═══════════════════════════════════════════════════════════
def get_product_recommendation(
    name: str,
    ram_gb: int,
    storage_gb: int,
    category: str,
    df: pd.DataFrame
) -> Optional[dict]:
    if df.empty:
        return None

    product_df = df[
        (df["name"].str.lower() == name.lower()) &
        (df["ram_gb"] == ram_gb) &
        (df["storage_gb"] == storage_gb) &
        (df["category"].str.lower() == category.lower())
    ].copy()

    if product_df.empty:
        return None

    current_prices = (
        product_df.sort_values(["date", "timestamp"])
        .groupby("website", as_index=False)
        .tail(1)
        .copy()
    )

    if current_prices.empty:
        return None

    latest_date = product_df["date"].max()
    seven_days_ago = latest_date - pd.Timedelta(days=7)
    last_7_days = product_df[product_df["date"] >= seven_days_ago].copy()
    avg_7_days = last_7_days.groupby("website")["price"].mean().to_dict()

    results = []

    for _, row in current_prices.iterrows():
        website = row["website"]
        current_price = float(row["price"])
        avg_price = float(avg_7_days.get(website, current_price))

        if avg_price > 0:
            price_change = ((current_price - avg_price) / avg_price) * 100
        else:
            price_change = 0.0

        if price_change < -3:
            trend = "📉 Dropping"
            recommendation = "🟢 Great time to buy!"
        elif price_change > 3:
            trend = "📈 Rising"
            recommendation = "🔴 Wait for price drop"
        else:
            trend = "➡️ Stable"
            recommendation = "🟡 Normal price"

        results.append({
            "website": website.upper(),
            "current_price": current_price,
            "avg_7_days": avg_price,
            "price_change": price_change,
            "trend": trend,
            "recommendation": recommendation,
            "url": row.get("URL", "")
        })

    results = sorted(results, key=lambda x: x["current_price"])

    best = results[0]

    if best["price_change"] < -5:
        overall_rec = "🟢 STRONG BUY - Price dropped significantly!"
    elif best["price_change"] < -2:
        overall_rec = "🟢 BUY - Good deal right now"
    elif best["price_change"] > 5:
        overall_rec = "🔴 WAIT - Price is rising, wait for drop"
    elif best["price_change"] > 2:
        overall_rec = "🟡 HOLD - Price slightly high"
    else:
        overall_rec = "🟡 NORMAL - Average price"

    return {
        "best_website": best["website"],
        "best_price": best["current_price"],
        "price_change_7d": best["price_change"],
        "trend": best["trend"],
        "recommendation": overall_rec,
        "alternatives": results[1:],
        "best_url": best["url"]
    }
# ═══════════════════════════════════════════════════════════
# COMPATIBILITY WRAPPER
# ═══════════════════════════════════════════════════════════

def load_and_preprocess_data(filepath: str = "tablets") -> pd.DataFrame:
    if "tablet" in filepath.lower():
        df = load_tablets_from_supabase()
    elif "mobile" in filepath.lower():
        df = load_mobiles_from_supabase()
    else:
        raise ValueError(f"Unknown filepath: {filepath}")

    if df.empty:
        raise ValueError(f"No data found in Supabase for {filepath}")

    # one row per product_key per date per website
    df_daily = (
        df.groupby(["product_key", "website", "date"], as_index=False)
        .agg({
            "price": "mean",
            "name": "first",
            "brand": "first",
            "category": "first",
            "ram_gb": "first",
            "storage_gb": "first",
            "URL": "last",
            "timestamp": "max",
            "product_id": "first"
        })
        .sort_values(["product_key", "website", "date"], kind="stable")
        .reset_index(drop=True)
    )

    return df_daily

# ═══════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING SUPABASE DATA LOADER")
    print("=" * 60)

    print("\n📱 Tablets Test:")
    tablets_df = load_tablets_from_supabase()
    print(f"Records: {len(tablets_df)}")

    print("\n📱 Mobiles Test:")
    mobiles_df = load_mobiles_from_supabase()
    print(f"Records: {len(mobiles_df)}")

    print("\n🔄 Wrapper Test:")
    df = load_and_preprocess_data("tablets")
    print(f"Final records: {len(df)}")

    print("\n✅ DONE")
