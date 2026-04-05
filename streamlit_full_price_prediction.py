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
    st.error("Make sure supabase_loader.py is in the same directory!")
    SUPABASE_AVAILABLE = False
try:
    from tablet_model_newVersion import (
        load_and_preprocess_data as load_tablet_data_func,
        forecast_product as forecast_tablet_func,
        load_global_model as load_tablet_model
    )
    try:
        tablet_model = load_tablet_model()
        MODELS_LOADED['tablet'] = True
    except:
        st.sidebar.warning("⚠️ Tablet model not trained yet")
except ImportError as e:
    st.error(f"❌ Error importing tablet_model_newVersion.py: {str(e)}")

try:
    from mobile_model_newVersion import (
        load_and_preprocess_data as load_mobile_data_func,
        forecast_product as forecast_mobile_func,
        load_global_model as load_mobile_model
    )
    try:
        mobile_model = load_mobile_model()
        MODELS_LOADED['mobile'] = True
    except:
        st.sidebar.warning("⚠️ Mobile model not trained yet")
except ImportError as e:
    st.error(f"❌ Error importing mobile_model_newVersion.py: {str(e)}")

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

h1 { color: #667eea; font-weight: 700; margin-bottom: 0.5rem; }
h2, h3 { color: #4a5568; font-weight: 600; }

.stSelectbox label, .stMultiSelect label { font-weight: 600; color: #2d3748; }
div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #667eea; }

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.5rem 2rem;
    font-weight: 600;
    transition: all 0.3s;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
}

section[data-testid="stSidebar"] { background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); }
section[data-testid="stSidebar"] * { color: white !important; }

.rec-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
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

.device-badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
    margin: 0.2rem;
}

.badge-tablet { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.badge-mobile { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    margin: 0.5rem 0;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.stat-label {
    font-size: 0.85rem;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}

.stat-value { font-size: 1.8rem; font-weight: 700; }

.signal-banner {
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1.5rem 0;
    border-left: 5px solid;
}

.signal-buy {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    border-left-color: #28a745;
    color: #155724;
}

.signal-wait {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    border-left-color: #ffc107;
    color: #856404;
}

.signal-hold {
    background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
    border-left-color: #17a2b8;
    color: #0c5460;
}

.signal-volatile {
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    border-left-color: #dc3545;
    color: #721c24;
}

.signal-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; }
.signal-desc { font-size: 1rem; margin-bottom: 0.3rem; }
.signal-detail { font-size: 0.9rem; opacity: 0.8; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_data(device_type):
    if not SUPABASE_AVAILABLE:
        st.error("❌ Supabase loader not available!")
        return None, "Supabase"
    try:
        if device_type == "Tablets":
            df = load_tablets_from_supabase()
            source = "Supabase (tablets)"
        else:
            df = load_mobiles_from_supabase()
            source = "Supabase (mobiles)"
        
        if df.empty:
            st.error(f"❌ No {device_type.lower()} data found in Supabase!")
            st.info("Make sure your scraper has run and data exists in the database.")
            return None, source
        
        return df, source
        
    except Exception as e:
        st.error(f"❌ Error loading data from Supabase: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, "Supabase"

def generate_buy_signal(result):
    """Generate buy/wait/hold signal based on forecast"""
    last_price = result['last_price']
    future_price = result['forecast_prices'][-1]
    change_pct = ((future_price - last_price) / last_price) * 100
    mae = result['mae']
    confidence = result['confidence']
    
    volatility_ratio = (mae / last_price) * 100
    
    if volatility_ratio > 10:
        signal_type = "volatile"
        signal_icon = "⚠️"
        signal_title = "CAUTION - HIGH PRICE VOLATILITY"
        signal_desc = f"Price fluctuations detected (±{volatility_ratio:.1f}%)"
        signal_detail = "Consider waiting for more stable pricing"
    elif change_pct < -3:
        signal_type = "buy"
        signal_icon = "🟢"
        signal_title = "BUY SIGNAL"
        signal_desc = f"Price expected to drop {abs(change_pct):.1f}% in next 7 days"
        signal_detail = "Good opportunity to purchase"
    elif change_pct > 3:
        signal_type = "wait"
        signal_icon = "🔴"
        signal_title = "WAIT SIGNAL"
        signal_desc = f"Price expected to rise {change_pct:.1f}% in next 7 days"
        signal_detail = "Consider delaying purchase"
    else:
        signal_type = "hold"
        signal_icon = "🟡"
        signal_title = "HOLD/NEUTRAL"
        signal_desc = "Price expected to remain relatively stable"
        signal_detail = f"Minor change expected: {change_pct:+.1f}%"
    
    return {
        'type': signal_type,
        'icon': signal_icon,
        'title': signal_title,
        'desc': signal_desc,
        'detail': signal_detail,
        'confidence': confidence,
        'current': last_price,
        'forecast': future_price,
        'change_pct': change_pct
    }


def create_forecast_chart(result, device_type, date_range=None):
    """Create forecast chart"""
    pdf = result['pdf']
    
    if date_range:
        start_date, end_date = date_range
        pdf = pdf[(pdf['date'] >= start_date) & (pdf['date'] <= end_date)]
    
    forecast_dates = result['forecast_dates']
    forecast_prices = result['forecast_prices']
    mae = result['mae']
    
    if device_type == "Tablets":
        color_main = '#667eea'
        color_forecast = '#f093fb'
    else:
        color_main = '#f5576c'
        color_forecast = '#feca57'
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=pdf['date'],
        y=pdf['price'],
        mode='lines+markers',
        name='Historical Price',
        line=dict(color=color_main, width=3),
        marker=dict(size=6, color=color_main),
        hovertemplate='<b>%{x}</b><br>EGP %{y:,.0f}<extra></extra>'
    ))
    
    if 'rolling_avg_7' in pdf.columns:
        fig.add_trace(go.Scatter(
            x=pdf['date'],
            y=pdf['rolling_avg_7'],
            mode='lines',
            name='7-Day Average',
            line=dict(color=color_main, width=2, dash='dot'),
            opacity=0.6,
            hovertemplate='<b>%{x}</b><br>Avg: EGP %{y:,.0f}<extra></extra>'
        ))
    
    last_hist_date = pdf['date'].iloc[-1]
    last_hist_price = pdf['price'].iloc[-1]
    
    fig.add_trace(go.Scatter(
        x=[last_hist_date, forecast_dates[0]],
        y=[last_hist_price, forecast_prices[0]],
        mode='lines',
        line=dict(color='gray', width=2, dash='dot'),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_prices,
        mode='lines+markers',
        name='7-Day Forecast',
        line=dict(color=color_forecast, width=3, dash='dash'),
        marker=dict(size=8, symbol='diamond', color=color_forecast),
        hovertemplate='<b>%{x}</b><br>Forecast: EGP %{y:,.0f}<extra></extra>'
    ))
    
    upper = [p + mae for p in forecast_prices]
    lower = [max(0, p - mae) for p in forecast_prices]
    
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1],
        y=upper + lower[::-1],
        fill='toself',
        fillcolor=f'rgba(240, 147, 251, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    today = pd.Timestamp.today().normalize()
    today_str = today.strftime('%Y-%m-%d')
    
    fig.add_shape(
        type="line",
        x0=today_str, x1=today_str,
        y0=0, y1=1,
        yref='paper',
        line=dict(color="gray", width=2, dash="dot")
    )
    
    fig.add_annotation(
        x=today_str,
        y=1,
        yref='paper',
        text="Today",
        showarrow=False,
        yshift=10
    )
    
    fig.update_layout(
        title=f"📊 Price History & 7-Day Forecast",
        xaxis_title="Date",
        yaxis_title="Price (EGP)",
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    return fig

# ═══════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════

st.markdown("# 📱 Price Tracker Pro")
st.markdown("### 🤖 AI-Powered Price Forecasting & Best Deal Finder")

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
<div style='text-align: center; color: #718096; font-size: 0.9rem; padding: 1rem;'>
    <p>📱 Price Tracker Pro - Powered by Supabase & AI</p>
    <p>✅ Real-time data | 🎯 Smart recommendations | ⚡ Optimized for speed</p>
</div>
""", unsafe_allow_html=True)
