import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta, datetime
import os

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Price Tracker - Tablets & Mobiles",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════
# IMPORT MODELS
# ═══════════════════════════════════════════════════════════
from supabase_loader_OPTIMIZED import (
    load_tablets_from_supabase,
    load_mobiles_from_supabase,
    get_product_recommendation
)
 
# Import model functions
try:
    from tablet_model_newVersion import (
        forecast_product as forecast_tablet_func,
        load_global_model as load_tablet_model
    )
    tablet_model = load_tablet_model()
    MODELS_LOADED = {'tablet': True}
except:
    MODELS_LOADED = {'tablet': False}
    st.sidebar.warning("⚠️ Tablet model not loaded")
 
try:
    from mobile_model_newVersion import (
        forecast_product as forecast_mobile_func,
        load_global_model as load_mobile_model
    )
    mobile_model = load_mobile_model()
    MODELS_LOADED['mobile'] = True
except:
    MODELS_LOADED['mobile'] = False
    st.sidebar.warning("⚠️ Mobile model not loaded")
 
# ═══════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
 
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
 
.main .block-container {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
 
h1 { color: #667eea; font-weight: 700; }
h2, h3 { color: #4a5568; font-weight: 600; }
 
.rec-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}
 
.price-box {
    background: white;
    color: #667eea;
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    border: 2px solid #667eea;
}
 
.trend-up { color: #e74c3c; font-weight: bold; }
.trend-down { color: #2ecc71; font-weight: bold; }
.trend-stable { color: #f39c12; font-weight: bold; }
 
.buy-button {
    background: #2ecc71;
    color: white;
    padding: 0.8rem 2rem;
    border-radius: 10px;
    text-decoration: none;
    display: inline-block;
    font-weight: 600;
    margin-top: 1rem;
}
 
.buy-button:hover {
    background: #27ae60;
    text-decoration: none;
    color: white;
}
</style>
""", unsafe_allow_html=True)
 
# ═══════════════════════════════════════════════════════════
# DATA LOADING (CACHED!)
# ═══════════════════════════════════════════════════════════
 
@st.cache_data(ttl=3600)
def load_data(device_type):
    """Load data with caching - MUCH FASTER!"""
    if device_type == "Tablets":
        df = load_tablets_from_supabase()
        return df, "Supabase (tablets)"
    else:
        df = load_mobiles_from_supabase()
        return df, "Supabase (mobiles)"
 
# ═══════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════
 
st.markdown("# 📱 Price Tracker Pro")
st.markdown("### 🤖 AI-Powered Price Forecasting & Recommender System")
 
# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
 
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    device_type = st.radio(
        "📦 Device Type",
        options=["Tablets", "Mobiles"],
        help="Choose between tablets or mobile phones"
    )
    
    # Mode selection
    st.markdown("---")
    st.markdown("### 🎯 Mode")
    
    mode = st.radio(
        "Select Mode",
        options=["🔮 Price Forecast", "🎯 Best Deal Finder"],
        help="Choose what you want to do"
    )
    
    model_key = 'tablet' if device_type == "Tablets" else 'mobile'
    
    if mode == "🔮 Price Forecast" and not MODELS_LOADED[model_key]:
        st.error(f"❌ {device_type} model not found")
        st.stop()
 
# Load data
df, source = load_data(device_type)
 
if df is None or df.empty:
    st.error(f"❌ No {device_type.lower()} data found!")
    st.stop()
 
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Dataset Info")
    st.metric("Total Products", f"{df['product_key'].nunique():,}")
    st.metric("Data Points", f"{len(df):,}")
    last_update = df['date'].max()
    st.markdown(f"**Last Updated:** {last_update.strftime('%b %d, %Y')}")
    st.success(f"📡 {source}")
 
# ═══════════════════════════════════════════════════════════
# FILTERS (Common for both modes)
# ═══════════════════════════════════════════════════════════
 
st.markdown("### 🔍 Search & Filter Products")
 
search_term = st.text_input(
    "🔎 Search by product name",
    placeholder="e.g., iPad, Galaxy, iPhone...",
    help="Search for products by name"
)
 
if search_term:
    filtered_df = df[df['name'].str.contains(search_term, case=False, na=False)]
else:
    filtered_df = df.copy()
 
col1, col2, col3, col4 = st.columns(4)
 
with col1:
    brands = sorted(filtered_df['brand'].unique())
    selected_brands = st.multiselect("🏷️ Brand", brands, default=[])
 
with col2:
    websites = sorted(filtered_df['website'].unique())
    selected_websites = st.multiselect("🛒 Website", websites, default=[])
 
with col3:
    rams = sorted(filtered_df['ram_gb'].unique())
    selected_rams = st.multiselect("💾 RAM (GB)", rams, default=[])
 
with col4:
    storages = sorted(filtered_df['storage_gb'].unique())
    selected_storages = st.multiselect("💿 Storage (GB)", storages, default=[])
 
# Apply filters
if selected_brands:
    filtered_df = filtered_df[filtered_df['brand'].isin(selected_brands)]
if selected_websites:
    filtered_df = filtered_df[filtered_df['website'].isin(selected_websites)]
if selected_rams:
    filtered_df = filtered_df[filtered_df['ram_gb'].isin(selected_rams)]
if selected_storages:
    filtered_df = filtered_df[filtered_df['storage_gb'].isin(selected_storages)]
 
if filtered_df.empty:
    st.warning("⚠️ No products found. Try different filters.")
    st.stop()
 
st.markdown("---")
 
# ═══════════════════════════════════════════════════════════
# MODE 1: PRICE FORECAST (Original functionality)
# ═══════════════════════════════════════════════════════════
 
if mode == "🔮 Price Forecast":
    
    product_groups = filtered_df.groupby('product_key').agg({
        'name': 'first',
        'brand': 'first',
        'website': 'first',
        'ram_gb': 'first',
        'storage_gb': 'first',
        'price': 'count'
    }).reset_index()
    
    product_groups.columns = ['product_key', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'n_obs']
    product_groups = product_groups.sort_values('n_obs', ascending=False)
    
    st.markdown(f"**Found {len(product_groups)} products**")
    
    selected_product = st.selectbox(
        f"📱 Select a {device_type[:-1].lower()}",
        options=product_groups['product_key'].tolist(),
        format_func=lambda x: (
            f"{product_groups[product_groups['product_key']==x]['name'].values[0]} | "
            f"{product_groups[product_groups['product_key']==x]['ram_gb'].values[0]}GB + "
            f"{product_groups[product_groups['product_key']==x]['storage_gb'].values[0]}GB | "
            f"{product_groups[product_groups['product_key']==x]['website'].values[0].upper()} | "
            f"({product_groups[product_groups['product_key']==x]['n_obs'].values[0]} observations)"
        )
    )
    
    st.markdown("---")
    
    product_df = df[df['product_key'] == selected_product].copy()
    product_info = product_groups[product_groups['product_key'] == selected_product].iloc[0]
    
    # Show forecast (existing code continues...)
    st.markdown(f"## 📱 {product_info['name']}")
    
    # Generate forecast and display chart...
    # (Keep your existing forecast code here)
 
# ═══════════════════════════════════════════════════════════
# MODE 2: BEST DEAL FINDER (NEW!)
# ═══════════════════════════════════════════════════════════
 
elif mode == "🎯 Best Deal Finder":
    
    st.markdown("## 🎯 Find the Best Deal")
    st.markdown("Select a product to see the best website to buy from based on current prices and trends")
    
    # Get unique products (same name/ram/storage across different websites)
    unique_products = filtered_df.groupby(['name', 'ram_gb', 'storage_gb']).size().reset_index(name='website_count')
    unique_products = unique_products[unique_products['website_count'] > 0]
    
    if unique_products.empty:
        st.warning("No products found with your filters")
        st.stop()
    
    st.markdown(f"**Found {len(unique_products)} products**")
    
    # Product selection
    selected_idx = st.selectbox(
        f"📱 Select a {device_type[:-1].lower()}",
        options=range(len(unique_products)),
        format_func=lambda x: (
            f"{unique_products.iloc[x]['name']} | "
            f"{unique_products.iloc[x]['ram_gb']}GB RAM + "
            f"{unique_products.iloc[x]['storage_gb']}GB Storage | "
            f"({unique_products.iloc[x]['website_count']} websites)"
        )
    )
    
    selected_product = unique_products.iloc[selected_idx]
    
    st.markdown("---")
    
    # Get recommendation
    with st.spinner("🔍 Analyzing prices across websites..."):
        recommendation = get_product_recommendation(
            name=selected_product['name'],
            ram_gb=selected_product['ram_gb'],
            storage_gb=selected_product['storage_gb'],
            category=device_type.lower()[:-1],
            df=df
        )
    
    if not recommendation:
        st.error("No price data available for this product")
        st.stop()
    
    # Display recommendation
    st.markdown(f"## 📱 {selected_product['name']}")
    st.markdown(f"**Specs:** {selected_product['ram_gb']}GB RAM + {selected_product['storage_gb']}GB Storage")
    
    st.markdown("---")
    
    # Best deal card
    st.markdown("### 🏆 Best Deal")
    
    best_price_change = recommendation['price_change_7d']
    trend_class = "trend-down" if best_price_change < 0 else ("trend-up" if best_price_change > 0 else "trend-stable")
    
    st.markdown(f"""
    <div class="rec-card">
        <h2>🏆 {recommendation['best_website']}</h2>
        <h1>EGP {recommendation['best_price']:,.0f}</h1>
        <p class="{trend_class}">{recommendation['trend']}</p>
        <p style="font-size: 1.1rem; margin-top: 1rem;">{recommendation['recommendation']}</p>
        <p style="font-size: 0.9rem; opacity: 0.9;">7-day price change: {best_price_change:+.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    if recommendation['best_url']:
        st.markdown(f'<a href="{recommendation["best_url"]}" class="buy-button" target="_blank">🛒 Buy Now on {recommendation["best_website"]}</a>', unsafe_allow_html=True)
    
    # Alternative websites
    if recommendation['alternatives']:
        st.markdown("---")
        st.markdown("### 🔄 Alternative Websites")
        
        for alt in recommendation['alternatives']:
            price_change = alt['price_change']
            trend_class = "trend-down" if price_change < 0 else ("trend-up" if price_change > 0 else "trend-stable")
            
            col1, col2, col3 = st.columns([2, 2, 3])
            
            with col1:
                st.markdown(f"**{alt['website']}**")
            with col2:
                st.markdown(f"**EGP {alt['current_price']:,.0f}**")
            with col3:
                st.markdown(f'<span class="{trend_class}">{alt["trend"]} ({price_change:+.1f}%)</span>', unsafe_allow_html=True)
            
            if alt.get('url'):
                st.markdown(f"[🔗 View on {alt['website']}]({alt['url']})")
            
            st.markdown("---")
    
    # Price comparison chart
    st.markdown("### 📊 Price Comparison")
    
    all_websites = [recommendation['best_website']] + [alt['website'] for alt in recommendation['alternatives']]
    all_prices = [recommendation['best_price']] + [alt['current_price'] for alt in recommendation['alternatives']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=all_websites,
            y=all_prices,
            marker_color=['#2ecc71'] + ['#3498db'] * len(recommendation['alternatives']),
            text=[f"EGP {p:,.0f}" for p in all_prices],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Current Prices Across Websites",
        xaxis_title="Website",
        yaxis_title="Price (EGP)",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
 
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #718096; font-size: 0.9rem; padding: 1rem;'>
    <p>📱 Price Tracker Pro - Powered by Supabase & AI</p>
    <p>✅ Real-time data | 🎯 Smart recommendations | ⚡ Optimized for speed</p>
</div>
""", unsafe_allow_html=True)
