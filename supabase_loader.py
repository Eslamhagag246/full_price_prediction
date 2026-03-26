
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
# DATA LOADING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def load_tablets_from_supabase():

    try:
        print("📊 Loading tablets from Supabase...")
        
        products_result = supabase.table('products')\
            .select('*')\
            .eq('category', 'tablet')\
            .eq('is_active', True)\
            .execute()
        
        if not products_result.data:
            print("⚠️ No tablet products found in database")
            return pd.DataFrame()
        
        products_df = pd.DataFrame(products_result.data)
        print(f"   ✓ Found {len(products_df)} tablet products")
        
        prices_result = supabase.table('price_history')\
            .select('*')\
            .execute()
        
        if not prices_result.data:
            print("⚠️ No price history found in database")
            return pd.DataFrame()
        
        prices_df = pd.DataFrame(prices_result.data)
        print(f"   ✓ Found {len(prices_df):,} total price records")
        
        tablet_product_ids = products_df['id'].tolist()
        prices_df = prices_df[prices_df['product_id'].isin(tablet_product_ids)]
        print(f"   ✓ Filtered to {len(prices_df):,} tablet price records")
        
        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )
        
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = pd.to_datetime(df['date'])
        
        df['product_key'] = (
            df['name'].str.lower().str.strip() + ' ' +
            df['website'].str.lower() + ' ' +
            df['ram_gb'].astype(str) + ' ' +
            df['storage_gb'].astype(str)
        )
        if 'url' in df.columns:
            df.rename(columns={'url': 'URL'}, inplace=True)
        df = df.drop(columns=['id_x', 'id_y', 'product_id'], errors='ignore')
        df = df.sort_values(['product_key', 'date'])
        
        print(f"✅ Successfully loaded {len(df):,} tablet records")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Unique products: {df['product_key'].nunique()}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading tablets from Supabase: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def load_mobiles_from_supabase():
    try:
        print("📊 Loading mobiles from Supabase...")
        
        products_result = supabase.table('products')\
            .select('*')\
            .eq('category', 'mobile')\
            .eq('is_active', True)\
            .execute()
        
        if not products_result.data:
            print("⚠️ No mobile products found in database")
            return pd.DataFrame()
        
        products_df = pd.DataFrame(products_result.data)
        print(f"   ✓ Found {len(products_df)} mobile products")
        
        prices_result = supabase.table('price_history')\
            .select('*')\
            .execute()
        
        if not prices_result.data:
            print("⚠️ No price history found in database")
            return pd.DataFrame()
        
        prices_df = pd.DataFrame(prices_result.data)
        print(f"   ✓ Found {len(prices_df):,} total price records")
        
        mobile_product_ids = products_df['id'].tolist()
        prices_df = prices_df[prices_df['product_id'].isin(mobile_product_ids)]
        print(f"   ✓ Filtered to {len(prices_df):,} mobile price records")
        s
        df = prices_df.merge(
            products_df[['id', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )
        
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['ram_gb'] = pd.to_numeric(df['ram_gb'], errors='coerce').fillna(0).astype(int)
        df['storage_gb'] = pd.to_numeric(df['storage_gb'], errors='coerce').fillna(0).astype(int)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = pd.to_datetime(df['date'])

        df['product_key'] = (
            df['name'].str.lower().str.strip() + ' ' +
            df['website'].str.lower() + ' ' +
            df['ram_gb'].astype(str) + ' ' +
            df['storage_gb'].astype(str)
        )

        if 'url' in df.columns:
            df.rename(columns={'url': 'URL'}, inplace=True)

        df = df.drop(columns=['id_x', 'id_y', 'product_id'], errors='ignore')
        
        df = df.sort_values(['product_key', 'date'])
        
        print(f"✅ Successfully loaded {len(df):,} mobile records")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Unique products: {df['product_key'].nunique()}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading mobiles from Supabase: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
        
# COMPATIBILITY WRAPPER 
def load_and_preprocess_data(filepath='tablets'):
    
    filepath_lower = str(filepath).lower()
    
    if 'tablet' in filepath_lower:
        print("\n📱 Loading TABLET data from Supabase...")
        df = load_tablets_from_supabase()
    elif 'mobile' in filepath_lower:
        print("\n📱 Loading MOBILE data from Supabase...")
        df = load_mobiles_from_supabase()
    else:
        raise ValueError(
            f"❌ Unknown filepath: {filepath}\n"
            f"Use 'tablets' or 'mobiles'"
        )
    
    if df.empty:
        raise ValueError(f"❌ No data found in Supabase for {filepath}")
    
    print(f"\n📊 Aggregating daily prices...")
    
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
    
    print(f"✅ Data ready: {len(df_daily):,} daily records for {df_daily['product_key'].nunique()} products")
    
    return df_daily

# ═══════════════════════════════════════════════════════════
# TEST FUNCTION
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTING SUPABASE DATA LOADER")
    print("="*60)
    print()
    
    # Test tablets
    print("1️⃣ Testing tablet loading...")
    print("-"*60)
    tablets_df = load_tablets_from_supabase()
    
    if not tablets_df.empty:
        print(f"\n✅ SUCCESS!")
        print(f"   Records: {len(tablets_df):,}")
        print(f"   Products: {tablets_df['product_key'].nunique()}")
        print(f"   Columns: {list(tablets_df.columns)}")
        print("\nSample data:")
        print(tablets_df.head(3))
    else:
        print("❌ No data loaded")
    
    print("\n" + "="*60)
    
    # Test mobiles
    print("2️⃣ Testing mobile loading...")
    print("-"*60)
    mobiles_df = load_mobiles_from_supabase()
    
    if not mobiles_df.empty:
        print(f"\n✅ SUCCESS!")
        print(f"   Records: {len(mobiles_df):,}")
        print(f"   Products: {mobiles_df['product_key'].nunique()}")
        print("\nSample data:")
        print(mobiles_df.head(3))
    else:
        print("❌ No data loaded")
    
    print("\n" + "="*60)
    
    # Test compatibility wrapper
    print("3️⃣ Testing compatibility wrapper...")
    print("-"*60)
    
    try:
        df = load_and_preprocess_data('tablets')
        print(f"✅ Wrapper works! Loaded {len(df):,} records")
    except Exception as e:
        print(f"❌ Wrapper failed: {e}")
    
    print("\n" + "="*60)
    print("✅ TESTING COMPLETE")
    print("="*60)
 
