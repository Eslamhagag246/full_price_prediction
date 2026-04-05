import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta, datetime

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
MODELS_LOADED = {'tablet': False, 'mobile': False}
tablet_model = None
mobile_model = None

try:
    from supabase_loader import (
        load_tablets_from_supabase,
        load_mobiles_from_supabase,
        get_product_recommendation)
    SUPABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Error importing supabase_loader.py: {str(e)}")
    SUPABASE_AVAILABLE = False

try:
    from tablet_model_newVersion import (
        forecast_product as forecast_tablet_func,
        load_global_model as load_tablet_model
    )
    tablet_model = load_tablet_model()
    MODELS_LOADED['tablet'] = True
except:
    st.sidebar.warning("⚠️ Tablet model not loaded")

try:
    from mobile_model_newVersion import (
        forecast_product as forecast_mobile_func,
        load_global_model as load_mobile_model
    )
    mobile_model = load_mobile_model()
    MODELS_LOADED['mobile'] = True
except:
    st.sidebar.warning("⚠️ Mobile model not loaded")

# ═══════════════════════════════════════════════════════════
# CSS
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
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.5rem 2rem;
    font-weight: 600;
}
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); }
section[data-testid="stSidebar"] * { color: white !important; }
.rec-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
}
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
}
.stat-label { font-size: 0.85rem; opacity: 0.9; }
.stat-value { font-size: 1.8rem; font-weight: 700; }
.trend-up { color: #e74c3c; font-weight: bold; }
.trend-down { color: #2ecc71; font-weight: bold; }
.trend-stable { color: #f39c12; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_data(device_type):
    if not SUPABASE_AVAILABLE:
        return None, None
    try:
        if device_type == "Tablets":
            df = load_tablets_from_supabase()
        else:
            df = load_mobiles_from_supabase()
        
        if df.empty:
            st.error(f"❌ No data found!")
            return None, None
        
        return df, "Supabase"
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None, None

def generate_buy_signal(result):
    last_price = result['last_price']
    future_price = result['forecast_prices'][-1]
    change_pct = ((future_price - last_price) / last_price) * 100
    
    if change_pct < -3:
        return {'type': 'buy', 'icon': '🟢', 'title': 'BUY SIGNAL', 'desc': f"Price dropping {abs(change_pct):.1f}%"}
    elif change_pct > 3:
        return {'type': 'wait', 'icon': '🔴', 'title': 'WAIT SIGNAL', 'desc': f"Price rising {change_pct:.1f}%"}
    else:
        return {'type': 'hold', 'icon': '🟡', 'title': 'HOLD', 'desc': 'Price stable'}

def create_forecast_chart(result, device_type):
    pdf = result['pdf']
    forecast_dates = result['forecast_dates']
    forecast_prices = result['forecast_prices']
    mae = result['mae']
    
    color = '#667eea' if device_type == "Tablets" else '#f5576c'
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=pdf['date'], y=pdf['price'],
        mode='lines+markers', name='Historical',
        line=dict(color=color, width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates, y=forecast_prices,
        mode='lines+markers', name='Forecast',
        line=dict(color='#f093fb', width=3, dash='dash')
    ))
    
    upper = [p + mae for p in forecast_prices]
    lower = [max(0, p - mae) for p in forecast_prices]
    
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1],
        y=upper + lower[::-1],
        fill='toself', fillcolor='rgba(240,147,251,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence'
    ))
    
    fig.update_layout(
        title="Price History & Forecast",
        xaxis_title="Date", yaxis_title="Price (EGP)",
        height=500
    )
    
    return fig

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

st.title("📱 Price Tracker Pro")
st.markdown("### 🤖 AI-Powered Price Forecasting & Best Deal Finder")

# Session state
if 'show_market_insights' not in st.session_state:
    st.session_state.show_market_insights = False

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    device_type = st.radio(
        "📦 Device Type",
        options=["Tablets", "Mobiles"]
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Mode")
    
    app_mode = st.radio(
        "Select Mode",
        options=["🔮 Price Forecast", "🎯 Best Deal Finder"]
    )
    
    model_key = 'tablet' if device_type == "Tablets" else 'mobile'
    
    if app_mode == "🔮 Price Forecast" and not MODELS_LOADED[model_key]:
        st.error(f"❌ Model not found")
        st.stop()

# Load data
df, source = load_data(device_type)

if df is None or df.empty:
    st.error("❌ No data!")
    st.info("⚠️ **ISSUE DETECTED:** Your database only has 1 observation per product!")
    st.info("**FIX:** Run `populate_supabase_quick.py` to import all historical data")
    st.code("""
# Run this to fix:
python populate_supabase_quick.py
    """)
    st.stop()

with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Dataset Info")
    st.metric("Total Products", f"{df['product_key'].nunique():,}")
    st.metric("Data Points", f"{len(df):,}")
    st.markdown(f"**Last Updated:** {df['date'].max().strftime('%b %d, %Y')}")
    
    # Market Insights Button
    st.markdown("---")
    if st.button("📊 Market Insights", use_container_width=True):
        st.session_state.show_market_insights = not st.session_state.show_market_insights
        st.rerun()

# ═══════════════════════════════════════════════════════════
# MARKET INSIGHTS
# ═══════════════════════════════════════════════════════════

if st.session_state.show_market_insights:
    st.markdown("## 📈 Market Insights")
    
    price_changes = []
    for product_key in df['product_key'].unique():
        pdf = df[df['product_key'] == product_key].sort_values('date')
        if len(pdf) < 2:
            continue
        
        first_price = pdf['price'].iloc[0]
        last_price = pdf['price'].iloc[-1]
        
        if first_price > 0:
            pct_change = ((last_price - first_price) / first_price) * 100
            price_changes.append({
                'Product': pdf['name'].iloc[-1],
                'Website': pdf['website'].iloc[-1].upper(),
                'Change %': f"{pct_change:.1f}%",
                'Current': f"EGP {int(last_price):,}",
                '_pct': pct_change
            })
    
    if price_changes:
        df_changes = pd.DataFrame(price_changes)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📉 Top Price Drops")
            drops = df_changes[df_changes['_pct'] < 0].nsmallest(10, '_pct')[['Product', 'Website', 'Change %', 'Current']]
            st.dataframe(drops, hide_index=True)
        
        with col2:
            st.markdown("### 📈 Top Price Increases")
            rises = df_changes[df_changes['_pct'] > 0].nlargest(10, '_pct')[['Product', 'Website', 'Change %', 'Current']]
            st.dataframe(rises, hide_index=True)
    
    if st.button("← Back to Main"):
        st.session_state.show_market_insights = False
        st.rerun()
    
    st.stop()

# ═══════════════════════════════════════════════════════════
# FILTERS
# ═══════════════════════════════════════════════════════════

st.markdown("### 🔍 Search & Filter")

search = st.text_input("🔎 Search", placeholder="e.g., iPad, Galaxy...")
filtered_df = df[df['name'].str.contains(search, case=False, na=False)] if search else df.copy()

col1, col2, col3, col4 = st.columns(4)
with col1:
    brands = st.multiselect("🏷️ Brand", sorted(filtered_df['brand'].unique()))
with col2:
    websites = st.multiselect("🛒 Website", sorted(filtered_df['website'].unique()))
with col3:
    rams = st.multiselect("💾 RAM (GB)", sorted(filtered_df['ram_gb'].unique()))
with col4:
    storages = st.multiselect("💿 Storage (GB)", sorted(filtered_df['storage_gb'].unique()))

if brands:
    filtered_df = filtered_df[filtered_df['brand'].isin(brands)]
if websites:
    filtered_df = filtered_df[filtered_df['website'].isin(websites)]
if rams:
    filtered_df = filtered_df[filtered_df['ram_gb'].isin(rams)]
if storages:
    filtered_df = filtered_df[filtered_df['storage_gb'].isin(storages)]

if filtered_df.empty:
    st.warning("No products found")
    st.stop()

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# MODE 1: PRICE FORECAST
# ═══════════════════════════════════════════════════════════

if app_mode == "🔮 Price Forecast":
    
    products = filtered_df.groupby('product_key').agg({
        'name': 'first',
        'brand': 'first',
        'website': 'first',
        'ram_gb': 'first',
        'storage_gb': 'first',
        'price': 'count'
    }).reset_index()
    
    products.columns = ['product_key', 'name', 'brand', 'website', 'ram_gb', 'storage_gb', 'n_obs']
    products = products.sort_values('n_obs', ascending=False)
    
    st.markdown(f"**Found {len(products)} products**")
    
    selected = st.selectbox(
        "📱 Select Product",
        products['product_key'].tolist(),
        format_func=lambda x: (
            f"{products[products['product_key']==x]['name'].values[0]} | "
            f"{products[products['product_key']==x]['ram_gb'].values[0]}GB + "
            f"{products[products['product_key']==x]['storage_gb'].values[0]}GB | "
            f"{products[products['product_key']==x]['website'].values[0].upper()} | "
            f"({products[products['product_key']==x]['n_obs'].values[0]} obs)"
        )
    )
    
    st.markdown("---")
    
    product_df = df[df['product_key'] == selected]
    info = products[products['product_key'] == selected].iloc[0]
    
    with st.spinner("🤖 Generating forecast..."):
        if device_type == "Tablets":
            result = forecast_tablet_func(product_df, days_ahead=7, model=tablet_model)
        else:
            result = forecast_mobile_func(product_df, days_ahead=7, model=mobile_model)
    
    st.markdown(f"## 📱 {info['name']}")
    
    # Specs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏷️ Brand", info['brand'].title())
    c2.metric("💾 RAM", f"{info['ram_gb']}GB")
    c3.metric("💿 Storage", f"{info['storage_gb']}GB")
    c4.metric("🛒 Website", info['website'].upper())
    
    st.markdown("---")
    
    # Signal
    signal = generate_buy_signal(result)
    st.markdown(f"""
    <div class="rec-card">
        <h3>{signal['icon']} {signal['title']}</h3>
        <p>{signal['desc']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Current Price</div>
            <div class="stat-value">EGP {result['last_price']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with s2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">7-Day Forecast</div>
            <div class="stat-value">EGP {result['forecast_prices'][-1]:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with s3:
        change = result['forecast_prices'][-1] - result['last_price']
        pct = (change / result['last_price']) * 100
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Change</div>
            <div class="stat-value">{change:+,.0f} EGP</div>
            <div style="font-size:0.9rem;">({pct:+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with s4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Confidence</div>
            <div class="stat-value">{result['confidence']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Chart
    st.plotly_chart(create_forecast_chart(result, device_type), use_container_width=True)
    
    # Table
    st.markdown("### 📅 7-Day Forecast")
    forecast_table = pd.DataFrame({
        'Date': [d.strftime('%A, %b %d') for d in result['forecast_dates']],
        'Price': [f"EGP {p:,.0f}" for p in result['forecast_prices']]
    })
    st.dataframe(forecast_table, hide_index=True, use_container_width=True)
    
    # Stats
    st.markdown("---")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("📉 Min", f"EGP {result['min_price']:,.0f}")
    sc2.metric("📊 Avg", f"EGP {result['avg_price']:,.0f}")
    sc3.metric("📈 Max", f"EGP {result['max_price']:,.0f}")
    sc4.metric("🎯 MAE", f"±{result['mae']:,.0f}")

# ═══════════════════════════════════════════════════════════
# MODE 2: BEST DEAL FINDER
# ═══════════════════════════════════════════════════════════

elif app_mode == "🎯 Best Deal Finder":
    
    st.markdown("## 🎯 Find Best Deal")
    
    unique = filtered_df.groupby(['name', 'ram_gb', 'storage_gb']).size().reset_index(name='count')
    
    st.markdown(f"**Found {len(unique)} products**")
    
    idx = st.selectbox(
        "📱 Select Product",
        range(len(unique)),
        format_func=lambda x: (
            f"{unique.iloc[x]['name']} | "
            f"{unique.iloc[x]['ram_gb']}GB + {unique.iloc[x]['storage_gb']}GB | "
            f"({unique.iloc[x]['count']} websites)"
        )
    )
    
    sel = unique.iloc[idx]
    
    st.markdown("---")
    
    with st.spinner("🔍 Analyzing..."):
        rec = get_product_recommendation(
            name=sel['name'],
            ram_gb=sel['ram_gb'],
            storage_gb=sel['storage_gb'],
            category=device_type.lower()[:-1],
            df=df
        )
    
    if not rec:
        st.error("No data")
        st.stop()
    
    st.markdown(f"## 📱 {sel['name']}")
    st.markdown(f"**Specs:** {sel['ram_gb']}GB + {sel['storage_gb']}GB")
    
    st.markdown("---")
    st.markdown("### 🏆 Best Deal")
    
    trend_class = "trend-down" if rec['price_change_7d'] < 0 else "trend-up"
    
    st.markdown(f"""
    <div class="rec-card">
        <h2>🏆 {rec['best_website']}</h2>
        <h1>EGP {rec['best_price']:,.0f}</h1>
        <p class="{trend_class}">{rec['trend']}</p>
        <p style="font-size:1.1rem;">{rec['recommendation']}</p>
        <p style="font-size:0.9rem;">7-day change: {rec['price_change_7d']:+.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    if rec['best_url']:
        st.markdown(f"[🛒 Buy Now]({rec['best_url']})")
    
    # Alternatives
    if rec['alternatives']:
        st.markdown("---")
        st.markdown("### 🔄 Alternatives")
        
        for alt in rec['alternatives']:
            c1, c2, c3 = st.columns([2,2,3])
            c1.markdown(f"**{alt['website']}**")
            c2.markdown(f"**EGP {alt['current_price']:,.0f}**")
            trend = "trend-down" if alt['price_change'] < 0 else "trend-up"
            c3.markdown(f"<span class='{trend}'>{alt['trend']}</span>", unsafe_allow_html=True)
            st.markdown("---")
    
    # Chart
    st.markdown("### 📊 Price Comparison")
    websites = [rec['best_website']] + [a['website'] for a in rec['alternatives']]
    prices = [rec['best_price']] + [a['current_price'] for a in rec['alternatives']]
    
    fig = go.Figure(data=[go.Bar(
        x=websites, y=prices,
        marker_color=['#2ecc71'] + ['#3498db'] * len(rec['alternatives']),
        text=[f"EGP {p:,.0f}" for p in prices],
        textposition='outside'
    )])
    fig.update_layout(title="Prices", height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#718096; padding:1rem;'>
    <p>📱 Price Tracker Pro - Powered by AI</p>
</div>
""", unsafe_allow_html=True)
