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

# ═══════════════════════════════════════════════════════════
# CACHED FETCHING (FAST!)
# ═══════════════════════════════════════════════════════════

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
def get_all_products_cached():
    try:
        products_df = fetch_all('products')
        products_df = products_df[products_df['is_active'] == True]
        print(f"✅ Cached {len(products_df)} products")
        return products_df
    except Exception as e:
        print(f"❌ Error loading products: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_all_prices_cached():
    """Load ALL price history once and cache - FAST!"""
    try:
        prices_df = fetch_all('price_history')
        print(f"✅ Cached {len(prices_df):,} price records")
        return prices_df
    except Exception as e:
        print(f"❌ Error loading prices: {e}")
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════
# LOAD TABLETS (WITH CACHE)
# ═══════════════════════════════════════════════════════════

def load_tablets_from_supabase():
    try:
        print("📊 Loading tablets from Supabase (cached)...")

        # Get cached data
        products_df = get_all_products_cached()
        prices_df = get_all_prices_cached()
        
        if products_df.empty or prices_df.empty:
            return pd.DataFrame()

        # Filter for tablets only
        products_df = products_df[products_df['category'] == 'tablet']

        if products_df.empty:
            print("⚠️ No tablet products found")
            return pd.DataFrame()

        print(f"   Found {len(products_df)} tablet products")

        # Filter prices for tablets
        tablet_ids = set(products_df['id'])
        prices_df = prices_df[prices_df['product_id'].isin(tablet_ids)]

        print(f"   Filtered to {len(prices_df):,} tablet price records")

        # Merge
        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )

        # Clean data types
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        df['date'] = pd.to_datetime(df['date'], format='ISO8601', errors='coerce')

        # Create product_key
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

        print(f"✅ Loaded {len(df):,} tablet records (CACHED)")
        return df

    except Exception as e:
        print(f"❌ Error loading tablets: {e}")
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════
# LOAD MOBILES (WITH CACHE)
# ═══════════════════════════════════════════════════════════

def load_mobiles_from_supabase():
    try:
        print("📊 Loading mobiles from Supabase (cached)...")

        # Get cached data
        products_df = get_all_products_cached()
        prices_df = get_all_prices_cached()
        
        if products_df.empty or prices_df.empty:
            return pd.DataFrame()

        # Filter for mobiles only
        products_df = products_df[products_df['category'] == 'mobile']

        if products_df.empty:
            print("⚠️ No mobile products found")
            return pd.DataFrame()

        print(f"   Found {len(products_df)} mobile products")

        # Filter prices for mobiles
        mobile_ids = set(products_df['id'])
        prices_df = prices_df[prices_df['product_id'].isin(mobile_ids)]

        print(f"   Filtered to {len(prices_df):,} mobile price records")

        # Merge
        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )

        # Clean data types
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        df['date'] = pd.to_datetime(df['date'], format='ISO8601', errors='coerce')

        # Create product_key
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

        print(f"✅ Loaded {len(df):,} mobile records (CACHED)")
        return df

    except Exception as e:
        print(f"❌ Error loading mobiles: {e}")
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════
# PRICE RECOMMENDER SYSTEM
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_product_recommendation(name, ram_gb, storage_gb, category, df):
    product_df = df[
        (df['name'].str.lower() == name.lower()) &
        (df['ram_gb'] == ram_gb) &
        (df['storage_gb'] == storage_gb)
    ].copy()
    
    if product_df.empty:
        return None
    current_prices = (
            product_df.sort_values('date')
            .groupby('website')
            .tail(1)  # Get most recent row per website
            .copy()
        )
    
    latest_date = product_df['date'].max()
    
    seven_days_ago = latest_date - pd.Timedelta(days=7)
    last_7_days = product_df[product_df['date'] >= seven_days_ago]
    avg_7_days = last_7_days.groupby('website')['price'].mean().to_dict()
    results = []
    
    for idx, row in current_prices.iterrows():
        website = row['website']
        current_price = row['price']
        avg_price = avg_7_days.get(website, current_price)
        
        # Calculate price change
        if avg_price > 0:
            price_change = ((current_price - avg_price) / avg_price) * 100
        else:
            price_change = 0
        
        # Determine trend
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
            'website': website.upper(),
            'current_price': current_price,
            'avg_7_days': avg_price,
            'price_change': price_change,
            'trend': trend,
            'recommendation': recommendation,
            'url': row.get('URL', '')
        })
    
    # Sort by current price (cheapest first)
    results = sorted(results, key=lambda x: x['current_price'])
    
    if not results:
        return None
    
    best = results[0]
    
    # Overall recommendation
    if best['price_change'] < -5:
        overall_rec = "🟢 STRONG BUY - Price dropped significantly!"
    elif best['price_change'] < -2:
        overall_rec = "🟢 BUY - Good deal right now"
    elif best['price_change'] > 5:
        overall_rec = "🔴 WAIT - Price is rising, wait for drop"
    elif best['price_change'] > 2:
        overall_rec = "🟡 HOLD - Price slightly high"
    else:
        overall_rec = "🟡 NORMAL - Average price"
    
    return {
        'best_website': best['website'],
        'best_price': best['current_price'],
        'price_change_7d': best['price_change'],
        'trend': best['trend'],
        'recommendation': overall_rec,
        'alternatives': results[1:],
        'best_url': best['url']
    }


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

    # Daily aggregation
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
