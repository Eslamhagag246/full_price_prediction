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
    """Load data based on device type"""
    if device_type == "Tablets":
        filepath = 'tablets_cleaned_continuous.csv'
        load_func = load_tablet_data_func
    else:
        filepath = 'mobile_cleaned_70K.csv'
        load_func = load_mobile_data_func
    
    try:
        df = load_func(filepath)
        return df, filepath
    except FileNotFoundError:
        st.error(f"❌ File not found: {filepath}")
        return None, filepath
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None, filepath


def generate_buy_signal(result):
    """Generate buy/wait/hold signal based on forecast"""
    last_price = result['last_price']
    future_price = result['forecast_prices'][-1]
    change_pct = ((future_price - last_price) / last_price) * 100
    mae = result['mae']
    confidence = result['confidence']
    
    # Volatility check
    volatility_ratio = (mae / last_price) * 100
    
    if volatility_ratio > 10:  # High volatility
        signal_type = "volatile"
        signal_icon = "⚠️"
        signal_title = "CAUTION - HIGH PRICE VOLATILITY"
        signal_desc = f"Price fluctuations detected (±{volatility_ratio:.1f}%)"
        signal_detail = "💡 Monitor for a few more days before making a decision"
    elif change_pct < -2:  # Price dropping - GOOD TO BUY
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
    """Create forecast chart with optional date range"""
    pdf = result['pdf']
    
    # Apply date range filter if specified
    if date_range:
        start_date, end_date = date_range
        pdf = pdf[(pdf['date'] >= start_date) & (pdf['date'] <= end_date)]
    
    forecast_dates = result['forecast_dates']
    forecast_prices = result['forecast_prices']
    mae = result['mae']
    
    # Colors
    if device_type == "Tablets":
        color_main = '#667eea'
        color_forecast = '#f093fb'
    else:
        color_main = '#f5576c'
        color_forecast = '#feca57'
    
    fig = go.Figure()
    
    # Historical prices
    fig.add_trace(go.Scatter(
        x=pdf['date'],
        y=pdf['price'],
        mode='lines+markers',
        name='Historical Price',
        line=dict(color=color_main, width=3),
        marker=dict(size=6, color=color_main),
        hovertemplate='<b>%{x}</b><br>EGP %{y:,.0f}<extra></extra>'
    ))
    
    # Rolling average
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
    """Create comparison chart for multiple products"""
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

# Initialize session state
if 'show_market_insights' not in st.session_state:
    st.session_state.show_market_insights = False

with st.sidebar:
    st.markdown("## 🎯 Select Device Type")
    
    device_type = st.radio(
        "Choose category:",
        options=["Tablets", "Mobile Phones"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Check model
    model_key = 'tablet' if device_type == "Tablets" else 'mobile'
    
    if MODELS_LOADED[model_key]:
        st.success(f"✅ {device_type} model loaded")
    else:
        st.error(f"❌ {device_type} model not found")
        st.stop()
    
    # Load data
    df, filepath = load_data(device_type)
    
    if df is None:
        st.stop()
    
    # Market Insights Section
    st.markdown("---")
    
    if not st.session_state.show_market_insights:
        # Large, prominent Market Insights button
        st.markdown('<div style="margin: 1rem 0;">', unsafe_allow_html=True)
        
        insights_clicked = st.button(
            "📊 Market Insights",
            use_container_width=True,
            key="market_insights_btn"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Custom styling for this button
        st.markdown("""
        <style>
        /* Market Insights button styling */
        button[kind="primary"][key="market_insights_btn"] {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 1rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 1.05rem !important;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        button[kind="primary"][key="market_insights_btn"]:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 6px 25px rgba(255, 107, 107, 0.5) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if insights_clicked:
            st.session_state.show_market_insights = True
            st.rerun()
            
    else:
        # Small, subtle back button
        st.markdown('<div style="margin: 0.5rem 0;">', unsafe_allow_html=True)
        
        back_clicked = st.button(
            "← Back",
            use_container_width=True,
            key="back_btn"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Custom styling for back button (smaller, subtle)
        st.markdown("""
        <style>
        /* Back button styling */
        button[key="back_btn"] {
            background: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            transition: all 0.3s ease !important;
        }
        button[key="back_btn"]:hover {
            background: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if back_clicked:
            st.session_state.show_market_insights = False
            st.rerun()

# ═══════════════════════════════════════════════════════════
# CHECK IF SHOWING MARKET INSIGHTS
# ═══════════════════════════════════════════════════════════

if st.session_state.show_market_insights:
    # ═══════════════════════════════════════════════════════════
    # MARKET INSIGHTS PAGE
    # ═══════════════════════════════════════════════════════════
    
    st.markdown("## 📈 Market Insights")
    st.markdown("**Which products had the biggest price changes over the tracked period?**")
    
    # Calculate price changes
    price_changes = []
    
    for product_key in df['product_key'].unique():
        pdf = df[df['product_key'] == product_key].copy()
        
        if len(pdf) < 2:
            continue
        
        pdf = pdf.sort_values('date')
        first_price = pdf['price'].iloc[0]
        last_price = pdf['price'].iloc[-1]
        
        if first_price > 0:
            pct_change = ((last_price - first_price) / first_price) * 100
            
            price_changes.append({
                'Product': pdf['name'].iloc[-1],
                'Website': pdf['website'].iloc[-1].upper() if 'website' in pdf.columns else 'N/A',
                'Change %': f"{pct_change:.1f}%",
                'Current Price': f"EGP {int(last_price):,}",
                '_change_pct': pct_change
            })
    
    if price_changes:
        price_changes_df = pd.DataFrame(price_changes)
        
        # Two columns: Drops vs Rises
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🟢 Biggest Price Drops")
            top_drops = price_changes_df.nsmallest(5, '_change_pct')[['Product', 'Website', 'Change %', 'Current Price']]
            st.dataframe(top_drops, use_container_width=True, hide_index=True, height=250)
        
        with col2:
            st.markdown("### 🔴 Biggest Price Rises")
            top_rises = price_changes_df.nlargest(5, '_change_pct')[['Product', 'Website', 'Change %', 'Current Price']]
            st.dataframe(top_rises, use_container_width=True, hide_index=True, height=250)
        
        st.markdown("---")
        st.markdown("### ✅ Price Change % Since First Observation")
        
        # Chart
        chart_data = price_changes_df.sort_values('_change_pct', ascending=False).head(15)
        
        fig = px.bar(
            chart_data,
            x='Product',
            y='_change_pct',
            color='_change_pct',
            color_continuous_scale=['#00ff88', '#ffd166', '#ff6b6b'],
            color_continuous_midpoint=0,
            labels={'_change_pct': 'Price Change (%)'}
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False,
            plot_bgcolor='white',
            xaxis_title=None,
            yaxis_title='Price Change (%)',
            font=dict(family='Inter', size=12)
        )
        
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to calculate price changes")
    
    st.stop()  # Stop here, don't show forecast page

# ═══════════════════════════════════════════════════════════
# FILTERS (PRODUCT FORECAST PAGE)
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

# Filters
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

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# PRODUCT SELECTION
# ═══════════════════════════════════════════════════════════

if filtered_df.empty:
    st.warning("⚠️ No products found. Try different filters.")
    st.stop()

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

# Product comparison option
compare_mode = st.checkbox("📊 Compare multiple products", value=False)

if compare_mode:
    selected_products = st.multiselect(
        "Select 2-3 products to compare",
        options=product_groups['product_key'].tolist(),
        format_func=lambda x: f"{product_groups[product_groups['product_key']==x]['name'].values[0]}",
        max_selections=3
    )
    
    if len(selected_products) < 2:
        st.info("Please select at least 2 products to compare")
        st.stop()
else:
    selected_product = st.selectbox(
        f"📱 Select a {device_type[:-1].lower()}",
        options=product_groups['product_key'].tolist(),
        format_func=lambda x: (
            f"{product_groups[product_groups['product_key']==x]['name'].values[0]} | "
            f"{product_groups[product_groups['product_key']==x]['ram_gb'].values[0]}GB + "
            f"{product_groups[product_groups['product_key']==x]['storage_gb'].values[0]}GB | "
            f"{product_groups[product_groups['product_key']==x]['website'].values[0].upper()} | "
            f"({product_groups[product_groups['product_key']==x]['n_obs'].values[0]} observations)"
        ),
        help="Select a product to see price forecast"
    )
    selected_products = [selected_product]

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# FORECAST & DISPLAY
# ═══════════════════════════════════════════════════════════

# Generate forecasts
results = []
product_infos = []

for product_key in selected_products:
    product_df = df[df['product_key'] == product_key].copy()
    product_info = product_groups[product_groups['product_key'] == product_key].iloc[0]
    product_infos.append(product_info)
    
    with st.spinner(f"🤖 Generating forecast for {product_info['name']}..."):
        try:
            if device_type == "Tablets":
                result = forecast_tablet_func(product_df, days_ahead=7, model=tablet_model)
            else:
                result = forecast_mobile_func(product_df, days_ahead=7, model=mobile_model)
            results.append(result)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.stop()

# Display comparison or single product
if compare_mode:
    st.markdown("## 📊 Product Comparison")
    
    # Comparison table
    comp_data = []
    for info, result in zip(product_infos, results):
        comp_data.append({
            'Product': info['name'],
            'Current Price': f"EGP {result['last_price']:,.0f}",
            '7-Day Forecast': f"EGP {result['forecast_prices'][-1]:,.0f}",
            'Change': f"{((result['forecast_prices'][-1] - result['last_price']) / result['last_price'] * 100):+.1f}%",
            'Confidence': result['confidence']
        })
    
    st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
    
    # Comparison chart
    st.plotly_chart(
        create_comparison_chart(results, [info['name'] for info in product_infos]),
        use_container_width=True
    )
    
else:
    # Single product display
    result = results[0]
    product_info = product_infos[0]
    
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
    
    # Buy/Wait/Hold Signal
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
    
    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        min_date = result['pdf']['date'].min().date()
        max_date = result['pdf']['date'].max().date()
        start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    
    with col2:
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Reset Range"):
            start_date = min_date
            end_date = max_date
    
    # Chart
    date_range = (pd.Timestamp(start_date), pd.Timestamp(end_date)) if start_date and end_date else None
    st.plotly_chart(create_forecast_chart(result, device_type, date_range), use_container_width=True)
    
    # Download forecast button
    forecast_df = pd.DataFrame({
        'Date': [d.strftime('%Y-%m-%d') for d in result['forecast_dates']],
        'Forecasted Price (EGP)': result['forecast_prices'],
        'Lower Bound (EGP)': [max(0, p - result['mae']) for p in result['forecast_prices']],
        'Upper Bound (EGP)': [p + result['mae'] for p in result['forecast_prices']]
    })
    
    csv = forecast_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Forecast (CSV)",
        data=csv,
        file_name=f"{product_info['name']}_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    
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
    
    # URL
    if 'URL' in df[df['product_key'] == selected_product].columns:
        url = df[df['product_key'] == selected_product]['URL'].iloc[-1]
        if url and str(url) != 'nan':
            st.markdown(f"[🔗 View on {product_info['website'].upper()}]({url})")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #718096; font-size: 0.9rem; padding: 1rem;'>
    <p>📱 Price Tracker Pro - Powered by Global Linear Regression</p>
    <p>Smart price forecasting with AI-driven buy/wait/hold signals</p>
</div>
""", unsafe_allow_html=True)
