
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
    """Fetch all rows from Supabase using pagination"""
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


# ═══════════════════════════════════════════════════════════
# LOAD TABLETS
# ═══════════════════════════════════════════════════════════

def load_tablets_from_supabase():
    try:
        print("📊 Loading tablets from Supabase...")

        products_df = fetch_all('products')
        products_df = products_df[
            (products_df['category'] == 'tablet') &
            (products_df['is_active'] == True)
        ]

        if products_df.empty:
            print("⚠️ No tablet products found")
            return pd.DataFrame()

        print(f"   Found {len(products_df)} tablet products")

        prices_df = fetch_all('price_history')

        if prices_df.empty:
            print("⚠️ No price history found")
            return pd.DataFrame()

        print(f"   Found {len(prices_df):,} price records")

        tablet_ids = set(products_df['id'])
        prices_df = prices_df[prices_df['product_id'].isin(tablet_ids)]

        print(f"   Filtered to {len(prices_df):,} tablet price records")

        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )

        # Cleaning
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        df['date'] = pd.to_datetime(df['date'], format='ISO8601', errors='coerce')

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
        df = df.sort_values(['product_key', 'date'])

        print(f"✅ Loaded {len(df):,} tablet records from Supabase")
        return df

    except Exception as e:
        print(f"❌ Error loading tablets: {e}")
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════
# LOAD MOBILES
# ═══════════════════════════════════════════════════════════

def load_mobiles_from_supabase():
    try:
        print("📊 Loading mobiles from Supabase...")

        products_df = fetch_all('products')
        products_df = products_df[
            (products_df['category'] == 'mobile') &
            (products_df['is_active'] == True)
        ]

        if products_df.empty:
            print("⚠️ No mobile products found")
            return pd.DataFrame()

        print(f"   Found {len(products_df)} mobile products")

        prices_df = fetch_all('price_history')

        if prices_df.empty:
            print("⚠️ No price history found")
            return pd.DataFrame()

        print(f"   Found {len(prices_df):,} price records")

        mobile_ids = set(products_df['id'])
        prices_df = prices_df[prices_df['product_id'].isin(mobile_ids)]

        print(f"   Filtered to {len(prices_df):,} mobile price records")

        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )

        # Cleaning
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        df['date'] = pd.to_datetime(df['date'], format='ISO8601', errors='coerce')

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
        df = df.sort_values(['product_key', 'date'])

        print(f"✅ Loaded {len(df):,} mobile records from Supabase")
        return df

    except Exception as e:
        print(f"❌ Error loading mobiles: {e}")
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════
# COMPATIBILITY WRAPPER
# ═══════════════════════════════════════════════════════════

def load_and_preprocess_data(filepath='tablets'):

    if 'tablet' in filepath.lower():
        df = load_tablets_from_supabase()
    elif 'mobile' in filepath.lower():
        df = load_mobiles_from_supabase()
    else:
        raise ValueError(f"Unknown filepath: {filepath}")

    if df.empty:
        raise ValueError(f"No data found in Supabase for {filepath}")

    df_daily = df.groupby(['product_key', 'date']).agg({
        'price': 'mean',
        'name': 'first',
        'brand': 'first',
        'website': 'first',
        'ram_gb': 'first',
        'storage_gb': 'first',
        'URL': 'last' if 'URL' in df.columns else 'first',
        'timestamp': 'first'
    }).reset_index()

    df_daily = df_daily.sort_values(['product_key', 'date'])

    return df_daily


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

    print("\n🔄 Wrapper Test:")
    df = load_and_preprocess_data('tablets')
    print(f"Final records: {len(df)}")

    print("\n✅ DONE")
