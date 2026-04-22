
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import os

try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH_AVAILABLE = True
except ImportError:
    AUTO_REFRESH_AVAILABLE = False

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Price Tracker - Tablets & Mobiles",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

AUTO_REFRESH_SECONDS = int(os.getenv("AUTO_REFRESH_SECONDS", "300"))

def handle_auto_refresh():
    if not AUTO_REFRESH_AVAILABLE:
        return
    tick = st_autorefresh(interval=AUTO_REFRESH_SECONDS * 1000, key="auto_data_refresh")
    if "last_auto_refresh_tick" not in st.session_state:
        st.session_state.last_auto_refresh_tick = tick
    elif tick != st.session_state.last_auto_refresh_tick:
        st.session_state.last_auto_refresh_tick = tick
        st.cache_data.clear()

handle_auto_refresh()

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
        get_product_recommendation
    )
    SUPABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Error importing supabase_loader.py: {str(e)}")
    st.error("Make sure supabase_loader.py is in the same directory!")
    SUPABASE_AVAILABLE = False

try:
    from tablet_ensemble_streamlit import (
        forecast_product as forecast_tablet_func,
        load_global_model as load_tablet_model
    )
    try:
        tablet_model = load_tablet_model()
        MODELS_LOADED['tablet'] = True
    except Exception:
        st.sidebar.warning("⚠️ Tablet ensemble model not trained yet")
except ImportError as e:
    st.error(f"❌ Error importing tablet_ensemble_streamlit.py: {str(e)}")

try:
    from mobile_ensemble_streamlit import (
        forecast_product as forecast_mobile_func,
        load_global_model as load_mobile_model
    )
    try:
        mobile_model = load_mobile_model()
        MODELS_LOADED['mobile'] = True
    except Exception:
        st.sidebar.warning("⚠️ Mobile ensemble model not trained yet")
except ImportError as e:
    st.error(f"❌ Error importing mobile_ensemble_streamlit.py: {str(e)}")

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

div[data-testid="stMetricValue"] {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

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
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    margin: 0.5rem 0;
    box-shadow: 0 10px 30px rgba(240, 147, 251, 0.3);
}

.stat-label {
    font-size: 0.85rem;
    opacity: 0.95;
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

.buy-button:hover {
    filter: brightness(1.05);
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

div[data-testid="stMetric"] {
    background: #ffffff;
    border-radius: 12px;
    padding: 0.5rem 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def sort_price_history(pdf: pd.DataFrame) -> pd.DataFrame:
    pdf = pdf.copy()
    sort_cols = [c for c in ["date", "timestamp"] if c in pdf.columns]
    if sort_cols:
        pdf = pdf.sort_values(sort_cols, kind="stable")
    return pdf.reset_index(drop=True)

def get_actual_current_price_info(pdf: pd.DataFrame):
    pdf = sort_price_history(pdf)
    if pdf.empty:
        return np.nan, None, None
    row = pdf.iloc[-1]
    current_price = pd.to_numeric(row.get("price"), errors="coerce")
    current_date = row.get("date", None)
    current_url = row.get("URL", "") if "URL" in pdf.columns else ""
    try:
        current_price = float(current_price)
    except Exception:
        current_price = np.nan
    return current_price, current_date, current_url

def get_final_forecast_price(result) -> float:
    forecast_prices = pd.to_numeric(pd.Series(result.get("forecast_prices", [])), errors="coerce").dropna()
    if forecast_prices.empty:
        return np.nan
    return float(forecast_prices.iloc[-1])

@st.cache_data(ttl=3600, show_spinner=False)
def _load_data_cached(device_type: str):
    if not SUPABASE_AVAILABLE:
        return None, "Supabase"

    if device_type == "Tablets":
        df = load_tablets_from_supabase()
        source = "Supabase (tablets)"
    else:
        df = load_mobiles_from_supabase()
        source = "Supabase (mobiles)"

    if df is None or df.empty:
        return None, source

    df = df.copy()
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    df = df.dropna(subset=["price", "date"]).copy()
    sort_cols = [c for c in ["product_key", "date", "timestamp"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

    return df, source

def load_data(device_type):
    try:
        return _load_data_cached(device_type)
    except Exception as e:
        st.error(f"❌ Error loading data from Supabase: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, "Supabase"

def generate_buy_signal(result, actual_current_price: float):
    current_price = actual_current_price
    future_price = get_final_forecast_price(result)

    if pd.isna(current_price) or pd.isna(future_price) or current_price <= 0:
        return {
            'type': 'hold',
            'icon': '🟡',
            'title': 'INSUFFICIENT DATA',
            'desc': 'Could not compute current/forecast comparison',
            'detail': 'Please verify the latest history rows and forecast output',
            'confidence': result.get('confidence', 'N/A'),
            'current': current_price,
            'forecast': future_price,
            'change_pct': np.nan
        }

    change_pct = ((future_price - current_price) / current_price) * 100
    mae = float(result.get('mae', 0) or 0)
    confidence = result.get('confidence', 'N/A')

    volatility_ratio = (mae / current_price) * 100 if current_price > 0 else 0

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
        'current': current_price,
        'forecast': future_price,
        'change_pct': change_pct
    }

def create_forecast_chart(result, device_type, date_range=None):
    pdf = sort_price_history(result['pdf'])

    if date_range:
        start_date, end_date = date_range
        pdf = pdf[(pdf['date'] >= start_date) & (pdf['date'] <= end_date)].copy()
        pdf = sort_price_history(pdf)

    forecast_dates = result['forecast_dates']
    forecast_prices = pd.to_numeric(pd.Series(result['forecast_prices']), errors='coerce')
    mae = float(result['mae'])

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

    if not pdf.empty and len(forecast_dates) > 0:
        last_hist_date = pdf['date'].iloc[-1]
        last_hist_price = float(pdf['price'].iloc[-1])

        fig.add_trace(go.Scatter(
            x=[last_hist_date, forecast_dates[0]],
            y=[last_hist_price, float(forecast_prices.iloc[0])],
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

    upper = [float(p + mae) for p in forecast_prices]
    lower = [max(0.0, float(p - mae)) for p in forecast_prices]

    fig.add_trace(go.Scatter(
        x=list(forecast_dates) + list(forecast_dates)[::-1],
        y=upper + lower[::-1],
        fill='toself',
        fillcolor='rgba(240, 147, 251, 0.2)',
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
        title="📊 Price History & 7-Day Forecast",
        xaxis_title="Date",
        yaxis_title="Price (EGP)",
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
    )

    return fig

def create_comparison_chart(results, product_names):
    fig = go.Figure()
    colors = ['#667eea', '#f093fb', '#f5576c', '#feca57']

    for i, (result, name) in enumerate(zip(results, product_names)):
        color = colors[i % len(colors)]
        pdf = sort_price_history(result['pdf'])

        fig.add_trace(go.Scatter(
            x=pdf['date'],
            y=pdf['price'],
            mode='lines',
            name=f"{name} (Historical)",
            line=dict(color=color, width=2),
            opacity=0.7
        ))

        fig.add_trace(go.Scatter(
            x=result['forecast_dates'],
            y=result['forecast_prices'],
            mode='lines+markers',
            name=f"{name} (Forecast)",
            line=dict(color=color, width=2, dash='dash'),
            marker=dict(size=6, symbol='diamond')
        ))

    fig.update_layout(
        title="Product Price Comparison",
        xaxis_title="Date",
        yaxis_title="Price (EGP)",
        height=600,
        hovermode='x unified'
    )
    return fig


# ═══════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════

st.title("📱 Price Tracker Pro")
st.markdown("**Track & Forecast Prices for Tablets & Mobile Phones**")
st.markdown("---")

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
    st.markdown("### 🎯 Mode")
    app_mode = st.radio(
        "Select Mode:",
        options=["🔮 Price Forecast", "🎯 Best Deal Finder"],
        help="Price Forecast: See 7-day predictions | Best Deal Finder: Find cheapest website"
    )



    model_key = 'tablet' if device_type == "Tablets" else 'mobile'

    if app_mode == "🔮 Price Forecast":
        if MODELS_LOADED[model_key]:
            st.success(f"✅ {device_type} model loaded")
        else:
            st.error(f"❌ {device_type} model not found")
            st.stop()

    with st.spinner("Loading data..."):
        df, filepath = load_data(device_type)

    if df is None:
        st.stop()

    if AUTO_REFRESH_AVAILABLE:
        st.caption(f"Data source: {filepath} | Cache auto-refreshes every {AUTO_REFRESH_SECONDS // 60 if AUTO_REFRESH_SECONDS >= 60 else AUTO_REFRESH_SECONDS} {'minutes' if AUTO_REFRESH_SECONDS >= 60 else 'seconds'}")
    else:
        st.caption(f"Data source: {filepath} | Cached data will refresh automatically only after rerun. Install streamlit-autorefresh for timed refresh.")

    st.markdown("---")

    if not st.session_state.show_market_insights:
        insights_clicked = st.button("📊 Market Insights", use_container_width=True, key="market_insights_btn")
        if insights_clicked:
            st.session_state.show_market_insights = True
            st.rerun()
    else:
        back_clicked = st.button("← Back", use_container_width=True, key="back_btn")
        if back_clicked:
            st.session_state.show_market_insights = False
            st.rerun()

if st.session_state.show_market_insights:
    st.markdown("## 📈 Market Insights")
    st.markdown("**Which products had the biggest price changes over the tracked period?**")

    price_changes = []

    for product_key in df['product_key'].unique():
        pdf = sort_price_history(df[df['product_key'] == product_key].copy())
        if len(pdf) < 2:
            continue

        first_price = float(pdf['price'].iloc[0])
        last_price = float(pdf['price'].iloc[-1])

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
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📉 Top Price Drops")
            drops = price_changes_df[price_changes_df['_change_pct'] < 0].nsmallest(10, '_change_pct')
            if not drops.empty:
                st.dataframe(drops[['Product', 'Website', 'Change %', 'Current Price']], use_container_width=True, hide_index=True)
            else:
                st.info("No price drops detected")

        with col2:
            st.markdown("### 📈 Top Price Increases")
            rises = price_changes_df[price_changes_df['_change_pct'] > 0].nlargest(10, '_change_pct')
            if not rises.empty:
                st.dataframe(rises[['Product', 'Website', 'Change %', 'Current Price']], use_container_width=True, hide_index=True)
            else:
                st.info("No price increases detected")
    else:
        st.warning("Not enough data to calculate price changes")

    st.stop()

st.markdown("### 🔍 Search & Filter Products")

search_term = st.text_input(
    "🔎 Search by product name",
    placeholder="e.g., iPad, Galaxy, iPhone...",
    help="Search for products by name"
)

filtered_df = df[df['name'].str.contains(search_term, case=False, na=False)] if search_term else df.copy()

col1, col2, col3, col4 = st.columns(4)

with col1:
    brands = sorted(filtered_df['brand'].dropna().unique())
    selected_brands = st.multiselect("🏷️ Brand", brands, default=[])

with col2:
    websites = sorted(filtered_df['website'].dropna().unique())
    selected_websites = st.multiselect("🛒 Website", websites, default=[])

with col3:
    rams = sorted(filtered_df['ram_gb'].dropna().unique())
    selected_rams = st.multiselect("💾 RAM (GB)", rams, default=[])

with col4:
    storages = sorted(filtered_df['storage_gb'].dropna().unique())
    selected_storages = st.multiselect("💿 Storage (GB)", storages, default=[])

if selected_brands:
    filtered_df = filtered_df[filtered_df['brand'].isin(selected_brands)]
if selected_websites:
    filtered_df = filtered_df[filtered_df['website'].isin(selected_websites)]
if selected_rams:
    filtered_df = filtered_df[filtered_df['ram_gb'].isin(selected_rams)]
if selected_storages:
    filtered_df = filtered_df[filtered_df['storage_gb'].isin(selected_storages)]

st.markdown("---")

if app_mode == "🔮 Price Forecast":
    if filtered_df.empty:
        st.warning("⚠️ No products found. Try different filters.")
        st.stop()

    product_groups = filtered_df.groupby('product_key').agg({
        'name': 'first',
        'brand': 'first',
        'website': 'first',
        'category': 'first',
        'ram_gb': 'first',
        'storage_gb': 'first',
        'price': 'count'
    }).reset_index()

    product_groups.columns = ['product_key', 'name', 'brand', 'website', 'category', 'ram_gb', 'storage_gb', 'n_obs']
    product_groups = product_groups.sort_values('n_obs', ascending=False)

    st.markdown(f"**Found {len(product_groups)} products**")

    compare_mode = st.checkbox("📊 Compare multiple products", value=False)

    if compare_mode:
        selected_products = st.multiselect(
            "Select 2-3 products to compare",
            options=product_groups['product_key'].tolist(),
            format_func=lambda x: f"{product_groups[product_groups['product_key'] == x]['name'].values[0]}",
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

    results = []
    product_infos = []
    current_prices_map = {}

    for product_key in selected_products:
        product_df = sort_price_history(df[df['product_key'] == product_key].copy())
        product_info = product_groups[product_groups['product_key'] == product_key].iloc[0]
        product_infos.append(product_info)

        current_price, current_date, current_url = get_actual_current_price_info(product_df)
        current_prices_map[product_key] = {
            "price": current_price,
            "date": current_date,
            "url": current_url
        }

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

    if compare_mode:
        st.markdown("## 📊 Product Comparison")

        comp_data = []
        for info, result in zip(product_infos, results):
            actual_current_price = current_prices_map[info['product_key']]["price"]
            final_forecast_price = get_final_forecast_price(result)

            if pd.notna(actual_current_price) and pd.notna(final_forecast_price) and actual_current_price > 0:
                change_pct = ((final_forecast_price - actual_current_price) / actual_current_price) * 100
            else:
                change_pct = np.nan

            comp_data.append({
                'Product': info['name'],
                'Current Price': f"EGP {actual_current_price:,.0f}" if pd.notna(actual_current_price) else "N/A",
                '7-Day Forecast': f"EGP {final_forecast_price:,.0f}" if pd.notna(final_forecast_price) else "N/A",
                'Change': f"{change_pct:+.1f}%" if pd.notna(change_pct) else "N/A",
                'Confidence': result.get('confidence', 'N/A')
            })

        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
        st.plotly_chart(create_comparison_chart(results, [info['name'] for info in product_infos]), use_container_width=True)

    else:
        result = results[0]
        product_info = product_infos[0]
        product_key = product_info['product_key']

        actual_current_price = current_prices_map[product_key]["price"]
        actual_current_date = current_prices_map[product_key]["date"]
        actual_url = current_prices_map[product_key]["url"]
        final_forecast_price = get_final_forecast_price(result)

        if pd.notna(actual_current_price) and pd.notna(final_forecast_price) and actual_current_price > 0:
            expected_change_egp = final_forecast_price - actual_current_price
            expected_change_pct = (expected_change_egp / actual_current_price) * 100
        else:
            expected_change_egp = np.nan
            expected_change_pct = np.nan

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## 📱 {product_info['name']}")
        with col2:
            badge_class = 'badge-tablet' if device_type == "Tablets" else 'badge-mobile'
            st.markdown(f'<span class="device-badge {badge_class}">{device_type[:-1]}</span>', unsafe_allow_html=True)

        spec_col1, spec_col2, spec_col3, spec_col4 = st.columns(4)
        spec_col1.metric("🏷️ Brand", product_info['brand'].title())
        spec_col2.metric("💾 RAM", f"{product_info['ram_gb']}GB")
        spec_col3.metric("💿 Storage", f"{product_info['storage_gb']}GB")
        spec_col4.metric("🛒 Website", product_info['website'].upper())

        st.markdown("---")

        signal = generate_buy_signal(result, actual_current_price)

        current_display = f"EGP {signal['current']:,.0f}" if pd.notna(signal['current']) else "N/A"
        forecast_display = f"EGP {signal['forecast']:,.0f}" if pd.notna(signal['forecast']) else "N/A"

        st.markdown(f"""
        <div class="signal-banner signal-{signal['type']}">
            <div class="signal-title">{signal['icon']} {signal['title']}</div>
            <div class="signal-desc">{signal['desc']}</div>
            <div class="signal-detail">{signal['detail']}</div>
            <div class="signal-detail" style="margin-top: 0.5rem;">
                Current: {current_display} → Forecast: {forecast_display} |
                Confidence: {signal['confidence']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

        with stat_col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Current Price</div>
                <div class="stat-value">{f"EGP {actual_current_price:,.0f}" if pd.notna(actual_current_price) else "N/A"}</div>
            </div>
            """, unsafe_allow_html=True)

        with stat_col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">7-Day Forecast</div>
                <div class="stat-value">{f"EGP {final_forecast_price:,.0f}" if pd.notna(final_forecast_price) else "N/A"}</div>
            </div>
            """, unsafe_allow_html=True)

        with stat_col3:
            change_egp_text = f"{expected_change_egp:+,.0f} EGP" if pd.notna(expected_change_egp) else "N/A"
            change_pct_text = f"({expected_change_pct:+.1f}%)" if pd.notna(expected_change_pct) else ""
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Expected Change</div>
                <div class="stat-value">{change_egp_text}</div>
                <div style="font-size:0.9rem; margin-top:0.3rem;">{change_pct_text}</div>
            </div>
            """, unsafe_allow_html=True)

        with stat_col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Confidence</div>
                <div class="stat-value">{result.get('confidence', 'N/A')}</div>
                <div style="font-size:0.9rem; margin-top:0.3rem;">({result.get('n_obs', 0)} days tracked)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        pdf = sort_price_history(result['pdf'])
        min_date = pdf['date'].min().date()
        max_date = pdf['date'].max().date()

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Reset Range"):
                start_date = min_date
                end_date = max_date

        date_range = (pd.Timestamp(start_date), pd.Timestamp(end_date)) if start_date and end_date else None
        st.plotly_chart(create_forecast_chart(result, device_type, date_range), use_container_width=True)

        forecast_df = pd.DataFrame({
            'Date': [d.strftime('%Y-%m-%d') for d in result['forecast_dates']],
            'Forecasted Price (EGP)': pd.to_numeric(pd.Series(result['forecast_prices']), errors='coerce'),
            'Lower Bound (EGP)': [max(0, float(p) - float(result['mae'])) for p in pd.to_numeric(pd.Series(result['forecast_prices']), errors='coerce').fillna(0)],
            'Upper Bound (EGP)': [float(p) + float(result['mae']) for p in pd.to_numeric(pd.Series(result['forecast_prices']), errors='coerce').fillna(0)]
        })

        csv = forecast_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Forecast (CSV)",
            data=csv,
            file_name=f"{product_info['name']}_forecast_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        st.markdown("### 📅 7-Day Forecast Breakdown")
        forecast_table = pd.DataFrame({
            'Date': [d.strftime('%A, %B %d') for d in result['forecast_dates']],
            'Forecasted Price': [f"EGP {float(p):,.0f}" for p in pd.to_numeric(pd.Series(result['forecast_prices']), errors='coerce').fillna(0)],
            'Lower Bound': [f"EGP {max(0, float(p) - float(result['mae'])):,.0f}" for p in pd.to_numeric(pd.Series(result['forecast_prices']), errors='coerce').fillna(0)],
            'Upper Bound': [f"EGP {(float(p) + float(result['mae'])):,.0f}" for p in pd.to_numeric(pd.Series(result['forecast_prices']), errors='coerce').fillna(0)]
        })
        st.dataframe(forecast_table, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 📊 Price Statistics")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        stats_col1.metric("📉 Minimum Price", f"EGP {float(result['min_price']):,.0f}")
        stats_col2.metric("📊 Average Price", f"EGP {float(result['avg_price']):,.0f}")
        stats_col3.metric("📈 Maximum Price", f"EGP {float(result['max_price']):,.0f}")
        stats_col4.metric("🎯 Model Accuracy (MAE)", f"±{float(result['mae']):,.0f} EGP")

        if actual_url and str(actual_url) != 'nan':
            st.markdown(f"[🔗 View on {product_info['website'].upper()}]({actual_url})")

elif app_mode == "🎯 Best Deal Finder":
    st.markdown("## 🎯 Find the Best Deal")
    st.markdown("Select a product to see the best website to buy from based on current prices and trends")

    unique_products = filtered_df.groupby(['name', 'ram_gb', 'storage_gb']).agg({'website': 'nunique'}).reset_index()
    unique_products.columns = ['name', 'ram_gb', 'storage_gb', 'website_count']
    unique_products = unique_products[unique_products['website_count'] > 0]

    if unique_products.empty:
        st.warning("No products found with your filters")
        st.stop()

    st.markdown(f"**Found {len(unique_products)} products**")

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

    st.markdown(f"## 📱 {selected_product['name']}")
    st.markdown(f"**Specs:** {selected_product['ram_gb']}GB RAM + {selected_product['storage_gb']}GB Storage")
    st.markdown("---")
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

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #718096; font-size: 0.9rem; padding: 1rem;'>
    <p>📱 Price Tracker Pro - Powered by LightGBM + XGBoost Ensemble</p>
    <p>Smart price forecasting with AI-driven buy/wait/hold signals</p>
</div>
""", unsafe_allow_html=True)
