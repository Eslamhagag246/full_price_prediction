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

def fetch_all(table_name):
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

@st.cache_data(ttl=3600)
def load_all_products_cached():
    df = fetch_all('products')
    if not df.empty:
        df = df[df['is_active'] == True]
    return df

@st.cache_data(ttl=3600)
def load_all_prices_cached():
    return fetch_all('price_history')

@st.cache_data(ttl=3600)
def load_tablets_from_supabase():

    products_df = load_all_products_cached()
    prices_df = load_all_prices_cached()

    if products_df.empty or prices_df.empty:
        return pd.DataFrame()

    tablet_products = products_df[products_df['category'] == 'tablet']
    tablet_ids = tablet_products['id'].tolist()

    tablet_prices = prices_df[prices_df['product_id'].isin(tablet_ids)]

    df = tablet_prices.merge(
        tablet_products[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
        left_on='product_id',
        right_on='id',
        how='left'
    )

    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
    df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)

    df['date'] = pd.to_datetime(df['date'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df['product_key'] = (
        df['name'].str.lower().str.strip() + ' ' +
        df['website'].str.lower() + ' ' +
        df['ram_gb'].astype(str) + ' ' +
        df['storage_gb'].astype(str)
    )

    if 'url' in df.columns:
        df.rename(columns={'url': 'URL'}, inplace=True)

    df = df.drop(columns=['id_x', 'id_y', 'product_id'], errors='ignore')
    df = df.sort_values(['product_key', 'date', 'timestamp'])

    return df

@st.cache_data(ttl=3600)
def load_mobiles_from_supabase():

    products_df = load_all_products_cached()
    prices_df = load_all_prices_cached()

    if products_df.empty or prices_df.empty:
        return pd.DataFrame()

    mobile_products = products_df[products_df['category'] == 'mobile']
    mobile_ids = mobile_products['id'].tolist()

    mobile_prices = prices_df[prices_df['product_id'].isin(mobile_ids)]

    df = mobile_prices.merge(
        mobile_products[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
        left_on='product_id',
        right_on='id',
        how='left'
    )

    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
    df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)

    df['date'] = pd.to_datetime(df['date'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df['product_key'] = (
        df['name'].str.lower().str.strip() + ' ' +
        df['website'].str.lower() + ' ' +
        df['ram_gb'].astype(str) + ' ' +
        df['storage_gb'].astype(str)
    )

    if 'url' in df.columns:
        df.rename(columns={'url': 'URL'}, inplace=True)

    df = df.drop(columns=['id_x', 'id_y', 'product_id'], errors='ignore')
    df = df.sort_values(['product_key', 'date', 'timestamp'])

    return df

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

if __name__ == "__main__":
    print("="*50)

    full, daily = load_and_preprocess_data('tablets')

    print("FULL DATA:", len(full))
    print("DAILY DATA:", len(daily))
    print("UNIQUE PRODUCTS:", full['product_key'].nunique())

    print("="*50)
