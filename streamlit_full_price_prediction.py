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

/* Buy/Wait/Hold Signal */
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
    if device_type == "Tablets":
        df = load_tablets_from_supabase()
        return df, "Supabase (tablets)"
    else:
        df = load_mobiles_from_supabase()
        return df, "Supabase (mobiles)"

def generate_buy_signal(result):
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
        signal_detail = "💡 Monitor for a few more days before making a decision"
    elif change_pct < -2:  
        signal_type = "buy"
        signal_icon = "💰"
        signal_title = "EXCELLENT BUYING OPPORTUNITY"
        signal_desc = f"AI model predicts a {abs(change_pct):.1f}% price drop"
        signal_detail = f"✓ Best time to buy - Expected savings: EGP {abs(future_price - last_price):,.0f}"
    elif change_pct > 2:  # Price rising - WAIT
        signal_type = "wait"
        signal_icon = "⏳"
        signal_title = "NOT RECOMMENDED - PRICE RISING"
        signal_desc = f"Price expected to increase by {change_pct:.1f}% in next 7 days"
        signal_detail = f"⚠️ Wait for price to stabilize - Expected cost increase: EGP {abs(future_price - last_price):,.0f}"
    else:  # Stable
        signal_type = "hold"
        signal_icon = "📊"
        signal_title = "STABLE PRICING - BUY ANYTIME"
        signal_desc = f"Price expected to remain steady (±{abs(change_pct):.1f}%)"
        signal_detail = f"✓ Safe to purchase now - Low volatility (±{mae:,.0f} EGP)"
    
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
    
    # Connection to forecast
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
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_prices,
        mode='lines+markers',
        name='7-Day Forecast',
        line=dict(color=color_forecast, width=3, dash='dash'),
        marker=dict(size=8, symbol='diamond', color=color_forecast),
        hovertemplate='<b>%{x}</b><br>Forecast: EGP %{y:,.0f}<extra></extra>'
    ))
    
    # Confidence band
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
    
    # Today marker
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
        x=today_str, y=1,
        yref='paper',
        text="Today",
        showarrow=False,
        font=dict(color="gray", size=11),
        yshift=10
    )
    
    # Layout
    fig.update_layout(
        title={
            'text': '📈 Price History & 7-Day Forecast',
            'font': {'size': 20, 'color': '#2d3748', 'family': 'Inter'}
        },
        xaxis_title='Date',
        yaxis_title='Price (EGP)',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter', size=12, color='#4a5568'),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#e2e8f0',
            borderwidth=1
        ),
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f7fafc')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f7fafc')
    
    return fig


def create_comparison_chart(results_list, product_names):
    fig = go.Figure()
    
    colors = ['#667eea', '#f093fb', '#f5576c']
    
    for idx, (result, name) in enumerate(zip(results_list, product_names)):
        pdf = result['pdf']
        forecast_dates = result['forecast_dates']
        forecast_prices = result['forecast_prices']
        
        color = colors[idx % len(colors)]
        
        # Historical
        fig.add_trace(go.Scatter(
            x=pdf['date'],
            y=pdf['price'],
            mode='lines',
            name=f'{name} (Historical)',
            line=dict(color=color, width=2),
            hovertemplate='<b>%{x}</b><br>EGP %{y:,.0f}<extra></extra>'
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_prices,
            mode='lines',
            name=f'{name} (Forecast)',
            line=dict(color=color, width=2, dash='dash'),
            hovertemplate='<b>%{x}</b><br>EGP %{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title='Product Comparison',
        xaxis_title='Date',
        yaxis_title='Price (EGP)',
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
        hovermode='x unified'
    )
    
    return fig


# ═══════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════

st.title("📱 Price Tracker Pro")
st.markdown("**Track & Forecast Prices for Tablets & Mobile Phones**")
st.markdown("---")

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
    <p>📱 Price Tracker Pro - Powered by Global Linear Regression</p>
    <p>Smart price forecasting with AI-driven buy/wait/hold signals</p>
</div>
""", unsafe_allow_html=True)
