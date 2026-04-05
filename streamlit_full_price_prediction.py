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
        options=["Tablets", "Mobiles"],
        help="Choose between tablets or mobile phones"
    )
    
    st.markdown("---")
    st.markdown("### 🎯 Mode")
    
    app_mode = st.radio(
        "Select Mode",
        options=["🔮 Price Forecast", "🎯 Best Deal Finder"],
        help="Price Forecast: See 7-day predictions | Best Deal Finder: Find cheapest website"
    )
    
    model_key = 'tablet' if device_type == "Tablets" else 'mobile'
    
    if app_mode == "🔮 Price Forecast" and not MODELS_LOADED[model_key]:
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
# MODE 1: PRICE FORECAST
# ═══════════════════════════════════════════════════════════

if app_mode == "🔮 Price Forecast":
    
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
    
    # Generate forecast
    with st.spinner("🤖 Generating forecast..."):
        try:
            if device_type == "Tablets":
                result = forecast_tablet_func(product_df, days_ahead=7, model=tablet_model)
            else:
                result = forecast_mobile_func(product_df, days_ahead=7, model=mobile_model)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.stop()
    
    # Display
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## 📱 {product_info['name']}")
    with col2:
        badge_class = 'badge-tablet' if device_type == "Tablets" else 'badge-mobile'
        st.markdown(f'<span class="device-badge {badge_class}">{device_type[:-1]}</span>', unsafe_allow_html=True)
    
    # Specs
    spec_col1, spec_col2, spec_col3, spec_col4 = st.columns(4)
    spec_col1.metric("🏷️ Brand", product_info['brand'].title())
    spec_col2.metric("💾 RAM", f"{product_info['ram_gb']}GB")
    spec_col3.metric("💿 Storage", f"{product_info['storage_gb']}GB")
    spec_col4.metric("🛒 Website", product_info['website'].upper())
    
    st.markdown("---")
    
    # Buy Signal
    signal = generate_buy_signal(result)
    
    st.markdown(f"""
    <div class="signal-banner signal-{signal['type']}">
        <div class="signal-title">{signal['icon']} {signal['title']}</div>
        <div class="signal-desc">{signal['desc']}</div>
        <div class="signal-detail">{signal['detail']}</div>
        <div class="signal-detail" style="margin-top: 0.5rem;">
            Current: EGP {signal['current']:,.0f} → Forecast: EGP {signal['forecast']:,.0f} | 
            Confidence: {signal['confidence']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats cards
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Current Price</div>
            <div class="stat-value">EGP {result['last_price']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">7-Day Forecast</div>
            <div class="stat-value">EGP {result['forecast_prices'][-1]:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col3:
        change = result['forecast_prices'][-1] - result['last_price']
        change_pct = (change / result['last_price']) * 100
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Expected Change</div>
            <div class="stat-value">{change:+,.0f} EGP</div>
            <div style="font-size:0.9rem; margin-top:0.3rem;">({change_pct:+.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Confidence</div>
            <div class="stat-value">{result['confidence']}</div>
            <div style="font-size:0.9rem; margin-top:0.3rem;">({result['n_obs']} days tracked)</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Chart
    st.plotly_chart(create_forecast_chart(result, device_type), use_container_width=True)
    
    # Forecast table
    st.markdown("### 📅 7-Day Forecast Breakdown")
    
    forecast_table = pd.DataFrame({
        'Date': [d.strftime('%A, %B %d') for d in result['forecast_dates']],
        'Forecasted Price': [f"EGP {p:,.0f}" for p in result['forecast_prices']],
        'Lower Bound': [f"EGP {max(0, p - result['mae']):,.0f}" for p in result['forecast_prices']],
        'Upper Bound': [f"EGP {(p + result['mae']):,.0f}" for p in result['forecast_prices']]
    })
    
    st.dataframe(forecast_table, use_container_width=True, hide_index=True)
    
    # Stats
    st.markdown("---")
    st.markdown("### 📊 Price Statistics")
    
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    stats_col1.metric("📉 Minimum Price", f"EGP {result['min_price']:,.0f}")
    stats_col2.metric("📊 Average Price", f"EGP {result['avg_price']:,.0f}")
    stats_col3.metric("📈 Maximum Price", f"EGP {result['max_price']:,.0f}")
    stats_col4.metric("🎯 Model Accuracy (MAE)", f"±{result['mae']:,.0f} EGP")

# ═══════════════════════════════════════════════════════════
# MODE 2: BEST DEAL FINDER (NEW!)
# ═══════════════════════════════════════════════════════════

elif app_mode == "🎯 Best Deal Finder":
    
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
    
    # Display
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
