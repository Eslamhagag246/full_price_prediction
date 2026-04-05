import streamlit as st
import os
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

SUPABASE_URL = "https://ryiqzurrmvaftbnpiopx.supabase.co"
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ5aXF6dXJybXZhZnRibnBpb3B4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzcwMDY5NywiZXhwIjoyMDg5Mjc2Njk3fQ.7uVZj7t93AWOZd3CsU__AZTXQyNDUxM3IN3VWurzG04' 
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_cached(table_name):
    all_data = []
    limit = 1000
    offset = 0

    while True:
        response = supabase.table(table_name) \
            .select("*") \
            .range(offset, offset + limit - 1) \
            .execute()

        data = response.data

        if not data:
            break

        all_data.extend(data)

        if len(data) < limit:
            break

        offset += limit

    return pd.DataFrame(all_data)


@st.cache_data(ttl=3600, show_spinner=False)
def load_all_base_tables():
    products_df = fetch_all_cached('products')
    prices_df = fetch_all_cached('price_history')
    return products_df, prices_df


@st.cache_data(ttl=3600)
def load_tablets_from_supabase():
    try:
        products_df, prices_df = load_all_base_tables()

        products_df = products_df[
            (products_df['category'] == 'tablet') &
            (products_df['is_active'] == True)
        ]

        if products_df.empty or prices_df.empty:
            return pd.DataFrame()

        tablet_ids = set(products_df['id'])
        prices_df = prices_df[prices_df['product_id'].isin(tablet_ids)]

        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )

        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        df['product_key'] = (
            df['name'].str.lower().str.strip() + ' ' +
            df['website'].str.lower() + ' ' +
            df['ram_gb'].astype(str) + ' ' +
            df['storage_gb'].astype(str)
        )

        if 'url' in df.columns:
            df.rename(columns={'url': 'URL'}, inplace=True)

        df = df.dropna(subset=['timestamp', 'date'])
        df = df.drop(columns=['id_x', 'id_y', 'product_id'], errors='ignore')
        df = df.sort_values(['product_key', 'date', 'timestamp'])

        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_mobiles_from_supabase():
    try:
        products_df, prices_df = load_all_base_tables()

        products_df = products_df[
            (products_df['category'] == 'mobile') &
            (products_df['is_active'] == True)
        ]

        if products_df.empty or prices_df.empty:
            return pd.DataFrame()

        mobile_ids = set(products_df['id'])
        prices_df = prices_df[prices_df['product_id'].isin(mobile_ids)]

        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )

        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        df['product_key'] = (
            df['name'].str.lower().str.strip() + ' ' +
            df['website'].str.lower() + ' ' +
            df['ram_gb'].astype(str) + ' ' +
            df['storage_gb'].astype(str)
        )

        if 'url' in df.columns:
            df.rename(columns={'url': 'URL'}, inplace=True)

        df = df.dropna(subset=['timestamp', 'date'])
        df = df.drop(columns=['id_x', 'id_y', 'product_id'], errors='ignore')
        df = df.sort_values(['product_key', 'date', 'timestamp'])

        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_and_preprocess_data(filepath='tablets'):

    if 'tablet' in filepath.lower():
        df = load_tablets_from_supabase()
    elif 'mobile' in filepath.lower():
        df = load_mobiles_from_supabase()
    else:
        raise ValueError("Invalid type")

    if df.empty:
        raise ValueError("No data found")

    df_full = df.copy()

    df_daily = df.sort_values(['product_key', 'date', 'timestamp']) \
                 .drop_duplicates(['product_key', 'date'], keep='last')

    return df_full, df_daily


# ═══════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTING SUPABASE DATA LOADER")
    print("="*60)

    print("\n📱 Tablets Test:")
    tablets_df = load_tablets_from_supabase()
    print(f"Records: {len(tablets_df)}")

    print("\n📱 Mobiles Test:")
    mobiles_df = load_mobiles_from_supabase()
    print(f"Records: {len(mobiles_df)}")
    
    dups = tablets_df.duplicated(subset=['product_key', 'date']).sum()
    print(f"   Duplicates: {dups} (should be 0!)")
    
    print("\n🔄 Wrapper Test:")
    df = load_and_preprocess_data('tablets')
    print(f"Final records: {len(df)}")

    print("\n✅ DONE")
