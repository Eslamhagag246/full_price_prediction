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
# IMPORT MODELS & LOADERS
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
    from tablet_ensemble_streamlit import (
        forecast_product as forecast_tablet_func,
        load_global_model as load_tablet_model)
    try:
        tablet_model = load_tablet_model()
        MODELS_LOADED['tablet'] = True
    except Exception:
        pass
except ImportError:
    pass

try:
    from mobile_ensemble_streamlit import (
        forecast_product as forecast_mobile_func,
        load_global_model as load_mobile_model)
    try:
        mobile_model = load_mobile_model()
        MODELS_LOADED['mobile'] = True
    except Exception:
        pass
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════
# CSS — refined: less saturated, white secondary blocks,
#         strong gradient only for hero cards & actions
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Page background — softer violet instead of full gradient */
.stApp { background: #f0f2ff; }

/* Main card */
.main .block-container {
    background: white;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    box-shadow: 0 4px 24px rgba(102,126,234,0.10);
    max-width: 1200px;
}

h1 { color: #5a67d8; font-weight: 700; margin-bottom: 0.25rem; }
h2, h3 { color: #4a5568; font-weight: 600; }

/* Sidebar — kept full gradient as primary brand zone */
section[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #667eea 0%, #764ba2 100%);
}
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] .stRadio label { font-weight: 500; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #f7f8ff;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
    color: #5a67d8;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
}

/* Status bar */
.status-bar {
    background: #f7f8ff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.65rem 1.2rem;
    display: flex;
    gap: 2rem;
    align-items: center;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.status-item { font-size: 0.82rem; color: #4a5568; }
.status-item strong { color: #5a67d8; }

/* Hero stat cards — strong gradient for primary metrics */
.stat-card-hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.25rem 1.5rem;
    border-radius: 14px;
    text-align: center;
    margin: 0.4rem 0;
    box-shadow: 0 6px 20px rgba(102,126,234,0.25);
}

/* Secondary stat cards — white with accent border */
.stat-card-secondary {
    background: white;
    border: 2px solid #e9ecff;
    color: #2d3748;
    padding: 1.25rem 1.5rem;
    border-radius: 14px;
    text-align: center;
    margin: 0.4rem 0;
}
.stat-card-secondary .stat-label { color: #718096; }
.stat-card-secondary .stat-value { color: #5a67d8; }

.stat-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.4rem;
    opacity: 0.9;
}
.stat-value { font-size: 1.7rem; font-weight: 700; }
.stat-sub { font-size: 0.82rem; margin-top: 0.25rem; opacity: 0.8; }

/* Current price card — accent but not gradient overload */
.price-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 1.25rem 1.5rem;
    border-radius: 14px;
    text-align: center;
    margin: 0.4rem 0;
    box-shadow: 0 6px 20px rgba(245,87,108,0.2);
}

/* Signal banners */
.signal-banner {
    padding: 1.25rem 1.5rem;
    border-radius: 12px;
    margin: 1.25rem 0;
    border-left: 5px solid;
}
.signal-buy    { background:#f0fff4; border-left-color:#38a169; color:#276749; }
.signal-wait   { background:#fffbeb; border-left-color:#d69e2e; color:#744210; }
.signal-hold   { background:#ebf8ff; border-left-color:#3182ce; color:#1a365d; }
.signal-volatile { background:#fff5f5; border-left-color:#e53e3e; color:#742a2a; }
.signal-title  { font-size:1.2rem; font-weight:700; margin-bottom:0.35rem; }
.signal-desc   { font-size:0.97rem; margin-bottom:0.2rem; }
.signal-detail { font-size:0.87rem; opacity:0.8; }

/* Device badge */
.device-badge {
    display:inline-block; padding:0.25rem 0.75rem;
    border-radius:20px; font-size:0.85rem; font-weight:600; margin:0.2rem;
}
.badge-tablet { background:linear-gradient(135deg,#667eea,#764ba2); color:white; }
.badge-mobile { background:linear-gradient(135deg,#f093fb,#f5576c); color:white; }

/* Best Deal table */
.deal-table { width:100%; border-collapse:collapse; margin-top:0.5rem; }
.deal-table th {
    background:#f7f8ff; color:#5a67d8; font-size:0.8rem;
    text-transform:uppercase; letter-spacing:0.5px;
    padding:0.6rem 0.8rem; text-align:left;
    border-bottom:2px solid #e2e8f0;
}
.deal-table td { padding:0.7rem 0.8rem; border-bottom:1px solid #f0f2f5; font-size:0.93rem; }
.deal-table tr:first-child td { background:#f0fff4; font-weight:600; }
.deal-table .best-badge {
    background:linear-gradient(135deg,#38a169,#2f855a);
    color:white; font-size:0.75rem; padding:0.2rem 0.5rem;
    border-radius:10px; font-weight:700;
}
.deal-link { color:#5a67d8; font-weight:600; text-decoration:none; }
.deal-link:hover { text-decoration:underline; }
.trend-up   { color:#e53e3e; font-weight:600; }
.trend-down { color:#38a169; font-weight:600; }
.trend-stable { color:#d69e2e; font-weight:600; }

/* Buttons */
.stButton > button {
    background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
    color:white; border:none; border-radius:10px;
    padding:0.45rem 1.8rem; font-weight:600; transition:all 0.2s;
}
.stButton > button:hover {
    transform:translateY(-2px);
    box-shadow:0 8px 16px rgba(102,126,234,0.35);
}

/* Metric values */
div[data-testid="stMetricValue"] {
    font-size:1.6rem; font-weight:700; color:#5a67d8;
}

/* Filter section */
.filter-section {
    background:#f7f8ff; border-radius:12px;
    padding:1rem 1.25rem; margin-bottom:1rem;
    border:1px solid #e9ecff;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_data(device_type):
    # ⚠️  No st.* calls inside @st.cache_data — Streamlit silently skips
    # caching when display calls are detected. Status returned as 4-tuple.
    if not SUPABASE_AVAILABLE:
        return None, "Supabase", "error", "❌ Supabase loader not available!"
    try:
        if device_type == "Tablets":
            df = load_tablets_from_supabase()
            source = "Supabase (tablets)"
        else:
            df = load_mobiles_from_supabase()
            source = "Supabase (mobiles)"

        if df is None or df.empty:
            return None, source, "error", f"❌ No {device_type.lower()} data found in Supabase!"

        return df, source, "success", f"✅ Loaded {len(df):,} records from {source}"

    except Exception as e:
        import traceback
        return None, "Supabase", "exception", str(e) + "\n" + traceback.format_exc()


def generate_buy_signal(result):
    last_price  = result['last_price']
    future_price = result['forecast_prices'][-1]
    change_pct   = ((future_price - last_price) / last_price) * 100
    volatility_ratio = (result['mae'] / last_price) * 100

    if volatility_ratio > 10:
        return dict(type="volatile", icon="⚠️", title="CAUTION — HIGH PRICE VOLATILITY",
                    desc=f"Price fluctuations detected (±{volatility_ratio:.1f}%)",
                    detail="Consider waiting for more stable pricing",
                    confidence=result['confidence'], current=last_price,
                    forecast=future_price, change_pct=change_pct)
    elif change_pct < -3:
        return dict(type="buy", icon="🟢", title="BUY SIGNAL",
                    desc=f"Price expected to drop {abs(change_pct):.1f}% over the next 7 days",
                    detail="Good opportunity to purchase now",
                    confidence=result['confidence'], current=last_price,
                    forecast=future_price, change_pct=change_pct)
    elif change_pct > 3:
        return dict(type="wait", icon="🔴", title="WAIT SIGNAL",
                    desc=f"Price expected to rise {change_pct:.1f}% over the next 7 days",
                    detail="Consider delaying your purchase",
                    confidence=result['confidence'], current=last_price,
                    forecast=future_price, change_pct=change_pct)
    else:
        return dict(type="hold", icon="🟡", title="HOLD / NEUTRAL",
                    desc="Price expected to remain relatively stable",
                    detail=f"Minor change expected: {change_pct:+.1f}% over 7 days",
                    confidence=result['confidence'], current=last_price,
                    forecast=future_price, change_pct=change_pct)


def create_forecast_chart(result, device_type, date_range=None):
    pdf = result['pdf'].copy()
    if date_range:
        s, e = date_range
        pdf = pdf[(pdf['date'] >= s) & (pdf['date'] <= e)]

    fd = result['forecast_dates']
    fp = result['forecast_prices']
    mae = result['mae']

    c_hist = '#667eea' if device_type == "Tablets" else '#f5576c'
    c_fore = '#f093fb' if device_type == "Tablets" else '#feca57'

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pdf['date'], y=pdf['price'],
        mode='lines+markers', name='Historical Price',
        line=dict(color=c_hist, width=3), marker=dict(size=5, color=c_hist),
        hovertemplate='<b>%{x|%b %d}</b><br>EGP %{y:,.0f}<extra></extra>'))

    if 'rolling_avg_7' in pdf.columns:
        fig.add_trace(go.Scatter(x=pdf['date'], y=pdf['rolling_avg_7'],
            mode='lines', name='7-Day Avg',
            line=dict(color=c_hist, width=2, dash='dot'), opacity=0.5,
            hovertemplate='<b>%{x|%b %d}</b><br>Avg: EGP %{y:,.0f}<extra></extra>'))

    # Bridge line
    fig.add_trace(go.Scatter(
        x=[pdf['date'].iloc[-1], fd[0]], y=[pdf['price'].iloc[-1], fp[0]],
        mode='lines', line=dict(color='#a0aec0', width=2, dash='dot'),
        showlegend=False, hoverinfo='skip'))

    fig.add_trace(go.Scatter(x=fd, y=fp,
        mode='lines+markers', name='7-Day Forecast',
        line=dict(color=c_fore, width=3, dash='dash'),
        marker=dict(size=8, symbol='diamond', color=c_fore),
        hovertemplate='<b>%{x|%b %d}</b><br>Forecast: EGP %{y:,.0f}<extra></extra>'))

    upper = [p + mae for p in fp]
    lower = [max(0, p - mae) for p in fp]
    fig.add_trace(go.Scatter(
        x=fd + fd[::-1], y=upper + lower[::-1],
        fill='toself', fillcolor='rgba(240,147,251,0.15)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Confidence Band', hoverinfo='skip'))

    today_str = pd.Timestamp.today().strftime('%Y-%m-%d')
    fig.add_shape(type="line", x0=today_str, x1=today_str, y0=0, y1=1,
                  yref='paper', line=dict(color="#a0aec0", width=1.5, dash="dot"))
    fig.add_annotation(x=today_str, y=1, yref='paper',
                       text="Today", showarrow=False, yshift=10,
                       font=dict(color="#718096", size=11))

    fig.update_layout(
        title="📊 Price History & 7-Day Forecast",
        xaxis_title="Date", yaxis_title="Price (EGP)",
        hovermode='x unified', plot_bgcolor='white',
        paper_bgcolor='white', height=480,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(t=60))
    return fig


def create_comparison_chart(results, product_names):
    fig = go.Figure()
    colors = ['#667eea', '#f5576c', '#f093fb', '#feca57']
    for i, (result, name) in enumerate(zip(results, product_names)):
        c = colors[i % len(colors)]
        fig.add_trace(go.Scatter(x=result['pdf']['date'], y=result['pdf']['price'],
            mode='lines', name=f"{name} (Historical)",
            line=dict(color=c, width=2), opacity=0.7))
        fig.add_trace(go.Scatter(x=result['forecast_dates'], y=result['forecast_prices'],
            mode='lines+markers', name=f"{name} (Forecast)",
            line=dict(color=c, width=2, dash='dash'),
            marker=dict(size=6, symbol='diamond')))
    fig.update_layout(title="Product Price Comparison",
        xaxis_title="Date", yaxis_title="Price (EGP)",
        height=550, hovermode='x unified', plot_bgcolor='white',
        paper_bgcolor='white')
    return fig


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📱 Price Tracker Pro")
    st.markdown("---")

    st.markdown("### Device Category")
    device_type = st.radio("Choose category:", options=["Tablets", "Mobile Phones"],
                           index=0, label_visibility="collapsed")

    st.markdown("---")

    # Model status
    model_key = 'tablet' if device_type == "Tablets" else 'mobile'
    if MODELS_LOADED[model_key]:
        st.success(f"✅ {device_type} model ready")
    else:
        st.warning(f"⚠️ {device_type} model not loaded")

    st.markdown("---")

    # Load data — all st.* calls here, OUTSIDE the cached function
    df, data_source, load_status, load_message = load_data(device_type)

    if load_status == "error":
        st.error(load_message)
        st.stop()
    elif load_status == "exception":
        st.error(f"❌ {load_message.splitlines()[0]}")
        st.code(load_message)
        st.stop()

    if df is None:
        st.stop()

    # Sidebar data summary
    last_refresh = datetime.now().strftime("%H:%M:%S")
    n_products = df['product_key'].nunique() if 'product_key' in df.columns else len(df)
    st.markdown(f"""
    <div style='font-size:0.82rem; opacity:0.9; line-height:1.8;'>
    🗄️ <b>Source:</b> {data_source}<br>
    📦 <b>Records:</b> {len(df):,}<br>
    🏷️ <b>Products:</b> {n_products:,}<br>
    🕐 <b>Loaded:</b> {last_refresh}
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.title("📱 Price Tracker Pro")
st.markdown("**Track & Forecast Prices for Tablets & Mobile Phones in Egypt**")

# ── TOP STATUS BAR ──────────────────────────────────────────
if df is not None:
    n_products  = df['product_key'].nunique() if 'product_key' in df.columns else len(df)
    model_status = "✅ Loaded" if MODELS_LOADED[model_key] else "❌ Not loaded"
    latest_date  = pd.to_datetime(df['date']).max().strftime('%b %d, %Y') if 'date' in df.columns else 'N/A'
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-item">🕐 <strong>Last refresh</strong> {datetime.now().strftime('%H:%M')}</div>
        <div class="status-item">🗄️ <strong>Source</strong> {data_source}</div>
        <div class="status-item">📦 <strong>Products loaded</strong> {n_products:,}</div>
        <div class="status-item">🤖 <strong>Model</strong> {model_status}</div>
        <div class="status-item">📅 <strong>Latest data</strong> {latest_date}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# FILTERS  (persistent via session_state)
# ═══════════════════════════════════════════════════════════
if df is None:
    st.stop()

# Init persistent filter state
for k in ['filter_search','filter_brands','filter_websites','filter_rams','filter_storages']:
    if k not in st.session_state:
        st.session_state[k] = [] if k != 'filter_search' else ''

st.markdown('<div class="filter-section">', unsafe_allow_html=True)
st.markdown("#### 🔍 Filter Products")

fcol0, fcol_clear = st.columns([5, 1])
with fcol0:
    search_term = st.text_input("Search by name", value=st.session_state.filter_search,
                                placeholder="e.g. Galaxy, iPad, iPhone…",
                                label_visibility="collapsed")
    st.session_state.filter_search = search_term
with fcol_clear:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear", key="clear_filters"):
        for k in ['filter_search','filter_brands','filter_websites','filter_rams','filter_storages']:
            st.session_state[k] = [] if k != 'filter_search' else ''
        st.rerun()

filtered_df = df[df['name'].str.contains(search_term, case=False, na=False)] if search_term else df.copy()

fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    sel_brands = st.multiselect("🏷️ Brand",
        sorted(filtered_df['brand'].unique()),
        default=[b for b in st.session_state.filter_brands if b in filtered_df['brand'].unique()],
        key="ms_brand")
    st.session_state.filter_brands = sel_brands
with fc2:
    sel_websites = st.multiselect("🛒 Website",
        sorted(filtered_df['website'].unique()),
        default=[w for w in st.session_state.filter_websites if w in filtered_df['website'].unique()],
        key="ms_website")
    st.session_state.filter_websites = sel_websites
with fc3:
    sel_rams = st.multiselect("💾 RAM (GB)",
        sorted(filtered_df['ram_gb'].unique()),
        default=[r for r in st.session_state.filter_rams if r in filtered_df['ram_gb'].unique()],
        key="ms_ram")
    st.session_state.filter_rams = sel_rams
with fc4:
    sel_storages = st.multiselect("💿 Storage (GB)",
        sorted(filtered_df['storage_gb'].unique()),
        default=[s for s in st.session_state.filter_storages if s in filtered_df['storage_gb'].unique()],
        key="ms_storage")
    st.session_state.filter_storages = sel_storages

if sel_brands:    filtered_df = filtered_df[filtered_df['brand'].isin(sel_brands)]
if sel_websites:  filtered_df = filtered_df[filtered_df['website'].isin(sel_websites)]
if sel_rams:      filtered_df = filtered_df[filtered_df['ram_gb'].isin(sel_rams)]
if sel_storages:  filtered_df = filtered_df[filtered_df['storage_gb'].isin(sel_storages)]

n_shown = filtered_df['product_key'].nunique() if 'product_key' in filtered_df.columns else len(filtered_df)
st.caption(f"Showing **{n_shown}** products  ·  {len(filtered_df):,} price records")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# MAIN TABS  (replaces sidebar mode + back-button flow)
# ═══════════════════════════════════════════════════════════
tab_forecast, tab_deal, tab_insights = st.tabs([
    "🔮 Price Forecast",
    "🎯 Best Deal Finder",
    "📈 Market Insights"
])

# ───────────────────────────────────────────────────────────
# TAB 1 — PRICE FORECAST
# ───────────────────────────────────────────────────────────
with tab_forecast:

    if not MODELS_LOADED[model_key]:
        st.error(f"❌ {device_type} model not loaded. Train the model first.")
        st.stop()

    if filtered_df.empty:
        st.warning("⚠️ No products match the current filters.")
        st.stop()

    product_groups = (
        filtered_df.groupby('product_key')
        .agg(name=('name','first'), brand=('brand','first'),
             website=('website','first'), ram_gb=('ram_gb','first'),
             storage_gb=('storage_gb','first'), n_obs=('price','count'))
        .reset_index()
        .sort_values('n_obs', ascending=False)
    )

    compare_mode = st.checkbox("📊 Compare multiple products (up to 3)", value=False)

    if compare_mode:
        selected_products = st.multiselect(
            "Select 2–3 products to compare",
            options=product_groups['product_key'].tolist(),
            format_func=lambda x: product_groups.loc[product_groups['product_key']==x,'name'].values[0],
            max_selections=3)
        if len(selected_products) < 2:
            st.info("Please select at least 2 products.")
            st.stop()
    else:
        # Two-step picker: brand first, then product
        pc1, pc2 = st.columns([1, 3])
        with pc1:
            brand_pick = st.selectbox("Brand", ["All"] + sorted(product_groups['brand'].unique().tolist()))
        pg_filtered = product_groups if brand_pick == "All" else product_groups[product_groups['brand'] == brand_pick]

        with pc2:
            selected_product = st.selectbox(
                f"📱 Select {device_type[:-1].lower()}",
                options=pg_filtered['product_key'].tolist(),
                format_func=lambda x: (
                    f"{pg_filtered.loc[pg_filtered['product_key']==x,'name'].values[0]}  ·  "
                    f"{pg_filtered.loc[pg_filtered['product_key']==x,'ram_gb'].values[0]}GB RAM  "
                    f"{pg_filtered.loc[pg_filtered['product_key']==x,'storage_gb'].values[0]}GB  ·  "
                    f"{pg_filtered.loc[pg_filtered['product_key']==x,'website'].values[0].upper()}  "
                    f"({pg_filtered.loc[pg_filtered['product_key']==x,'n_obs'].values[0]} obs)"
                ))
        selected_products = [selected_product]

    st.markdown("---")

    # Generate forecasts
    results, product_infos = [], []
    for product_key in selected_products:
        product_df   = df[df['product_key'] == product_key].copy().sort_values('date').reset_index(drop=True)
        product_info = product_groups[product_groups['product_key'] == product_key].iloc[0]
        product_infos.append(product_info)

        # Capture actual last price BEFORE calling model — guards the loop-clobber
        # bug in both tablet and mobile models where last_price gets overwritten.
        actual_last_price = float(product_df['price'].iloc[-1])

        with st.spinner(f"🤖 Forecasting {product_info['name']}…"):
            try:
                if device_type == "Tablets":
                    result = forecast_tablet_func(product_df, days_ahead=7, model=tablet_model)
                else:
                    result = forecast_mobile_func(product_df, days_ahead=7, model=mobile_model)
                result['last_price'] = actual_last_price
                results.append(result)
            except Exception as e:
                st.error(f"❌ Forecast error: {e}")
                st.stop()

    # ── COMPARISON MODE ─────────────────────────────────────
    if compare_mode:
        st.markdown("## 📊 Product Comparison")
        comp_rows = []
        for info, res in zip(product_infos, results):
            chg_pct = (res['forecast_prices'][-1] - res['last_price']) / res['last_price'] * 100
            comp_rows.append({
                'Product':          info['name'],
                'Current Price':    f"EGP {res['last_price']:,.0f}",
                '7-Day Forecast':   f"EGP {res['forecast_prices'][-1]:,.0f}",
                'Expected 7-Day Δ': f"{chg_pct:+.1f}%",
                'Confidence':       res['confidence']
            })
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
        st.plotly_chart(create_comparison_chart(results, [i['name'] for i in product_infos]),
                        use_container_width=True)

    # ── SINGLE PRODUCT ───────────────────────────────────────
    else:
        result       = results[0]
        product_info = product_infos[0]

        hc1, hc2 = st.columns([4, 1])
        with hc1:
            st.markdown(f"## 📱 {product_info['name']}")
        with hc2:
            badge_cls = 'badge-tablet' if device_type == "Tablets" else 'badge-mobile'
            st.markdown(f'<span class="device-badge {badge_cls}">{device_type[:-1]}</span>',
                        unsafe_allow_html=True)

        sp1, sp2, sp3, sp4 = st.columns(4)
        sp1.metric("🏷️ Brand",   product_info['brand'].title())
        sp2.metric("💾 RAM",     f"{product_info['ram_gb']}GB")
        sp3.metric("💿 Storage", f"{product_info['storage_gb']}GB")
        sp4.metric("🛒 Website", product_info['website'].upper())

        st.markdown("---")

        # Buy / Wait / Hold signal
        signal = generate_buy_signal(result)
        st.markdown(f"""
        <div class="signal-banner signal-{signal['type']}">
            <div class="signal-title">{signal['icon']} {signal['title']}</div>
            <div class="signal-desc">{signal['desc']}</div>
            <div class="signal-detail">{signal['detail']}</div>
            <div class="signal-detail" style="margin-top:0.4rem;">
                Current: <strong>EGP {signal['current']:,.0f}</strong> →
                Day-7 Forecast: <strong>EGP {signal['forecast']:,.0f}</strong> |
                Confidence: {signal['confidence']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── STAT CARDS ──────────────────────────────────────
        # Compute richer current-price context
        avg_7d = result['pdf'].tail(7)['price'].mean()
        vs_avg = result['last_price'] - avg_7d
        vs_avg_pct = (vs_avg / avg_7d) * 100 if avg_7d else 0

        change     = result['forecast_prices'][-1] - result['last_price']
        change_pct = (change / result['last_price']) * 100

        sc1, sc2, sc3, sc4 = st.columns(4)

        with sc1:
            st.markdown(f"""
            <div class="price-card">
                <div class="stat-label">Current Price</div>
                <div class="stat-value">EGP {result['last_price']:,.0f}</div>
                <div class="stat-sub">{product_info['website'].upper()} · {result['n_obs']} records</div>
                <div class="stat-sub">7d avg: EGP {avg_7d:,.0f}
                  ({vs_avg_pct:+.1f}% vs avg)</div>
            </div>""", unsafe_allow_html=True)

        with sc2:
            st.markdown(f"""
            <div class="stat-card-hero">
                <div class="stat-label">Day-7 Forecast</div>
                <div class="stat-value">EGP {result['forecast_prices'][-1]:,.0f}</div>
                <div class="stat-sub">Tomorrow: EGP {result['forecast_prices'][0]:,.0f}</div>
            </div>""", unsafe_allow_html=True)

        with sc3:
            arrow = "▲" if change > 0 else ("▼" if change < 0 else "—")
            st.markdown(f"""
            <div class="stat-card-secondary">
                <div class="stat-label">Expected 7-Day Change</div>
                <div class="stat-value">{change:+,.0f} EGP</div>
                <div class="stat-sub">{arrow} {change_pct:+.1f}% from current price</div>
                <div class="stat-sub" style="font-size:0.75rem;color:#718096;">
                    Day 1→7 vs today's price</div>
            </div>""", unsafe_allow_html=True)

        with sc4:
            st.markdown(f"""
            <div class="stat-card-secondary">
                <div class="stat-label">Confidence</div>
                <div class="stat-value">{result['confidence']}</div>
                <div class="stat-sub">MAE ±{result['mae']:,.0f} EGP</div>
                <div class="stat-sub">{result['n_obs']} days tracked</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Date range
        dr1, dr2, dr3 = st.columns([2, 2, 1])
        min_d = result['pdf']['date'].min().date()
        max_d = result['pdf']['date'].max().date()
        with dr1:
            start_date = st.date_input("Start Date", value=min_d, min_value=min_d, max_value=max_d)
        with dr2:
            end_date   = st.date_input("End Date",   value=max_d, min_value=min_d, max_value=max_d)
        with dr3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Reset"):
                start_date, end_date = min_d, max_d

        date_range = (pd.Timestamp(start_date), pd.Timestamp(end_date))
        st.plotly_chart(create_forecast_chart(result, device_type, date_range),
                        use_container_width=True)

        # Download
        dl_rows = []
        for i, (d, p) in enumerate(zip(result['forecast_dates'], result['forecast_prices'])):
            dl_rows.append({
                'Date': f"Tomorrow ({d.strftime('%Y-%m-%d')})" if i == 0 else d.strftime('%Y-%m-%d'),
                'Forecasted Price (EGP)': round(p),
                'Lower Bound (EGP)':      round(max(0, p - result['mae'])),
                'Upper Bound (EGP)':      round(p + result['mae'])
            })
        st.download_button("📥 Download Forecast CSV",
            data=pd.DataFrame(dl_rows).to_csv(index=False),
            file_name=f"{product_info['name']}_forecast_{datetime.now():%Y%m%d}.csv",
            mime="text/csv")

        # ── 7-DAY FORECAST TABLE ────────────────────────────
        st.markdown("### 📅 7-Day Forecast Breakdown")
        tbl_rows = []
        for i, (d, p) in enumerate(zip(result['forecast_dates'], result['forecast_prices'])):
            day_label = f"📍 Tomorrow  {d.strftime('%A, %b %d')}" if i == 0 else d.strftime('%A, %b %d')
            day_chg   = p - result['last_price']
            tbl_rows.append({
                'Day':              day_label,
                'Forecasted Price': f"EGP {p:,.0f}",
                'vs Today':         f"{day_chg:+,.0f} EGP  ({day_chg/result['last_price']*100:+.1f}%)",
                'Lower Bound':      f"EGP {max(0, p - result['mae']):,.0f}",
                'Upper Bound':      f"EGP {p + result['mae']:,.0f}"
            })
        st.dataframe(pd.DataFrame(tbl_rows), use_container_width=True, hide_index=True)

        # Price stats
        st.markdown("---")
        st.markdown("### 📊 Historical Price Statistics")
        ps1, ps2, ps3, ps4 = st.columns(4)
        ps1.metric("📉 Min Price",  f"EGP {result['min_price']:,.0f}")
        ps2.metric("📊 Avg Price",  f"EGP {result['avg_price']:,.0f}")
        ps3.metric("📈 Max Price",  f"EGP {result['max_price']:,.0f}")
        ps4.metric("🎯 MAE",        f"±{result['mae']:,.0f} EGP")

        # Product URL
        prod_rows = df[df['product_key'] == selected_products[0]]
        if 'URL' in prod_rows.columns:
            url = prod_rows.sort_values('date').iloc[-1].get('URL', '')
            if url and str(url) != 'nan':
                st.markdown(f"[🔗 View on {product_info['website'].upper()}]({url})")


# ───────────────────────────────────────────────────────────
# TAB 2 — BEST DEAL FINDER
# ───────────────────────────────────────────────────────────
with tab_deal:

    st.markdown("## 🎯 Best Deal Finder")
    st.markdown("Compare prices for the same product across all tracked websites.")

    if filtered_df.empty:
        st.warning("No products match the current filters.")
        st.stop()

    # Group by name+ram+storage (same physical product, different websites)
    unique_prods = (
        filtered_df.groupby(['name','ram_gb','storage_gb'])
        .agg(website_count=('website','nunique'))
        .reset_index()
        .sort_values('name')
    )

    if unique_prods.empty:
        st.warning("No products found.")
        st.stop()

    st.caption(f"Found **{len(unique_prods)}** products")

    # Two-step picker
    bd1, bd2 = st.columns([1, 3])
    with bd1:
        # Derive brand from filtered_df name match
        all_brands_deal = sorted(filtered_df['brand'].unique().tolist())
        brand_deal = st.selectbox("Brand", ["All"] + all_brands_deal, key="deal_brand")

    if brand_deal != "All":
        brand_names = filtered_df[filtered_df['brand'] == brand_deal]['name'].unique()
        up_filtered = unique_prods[unique_prods['name'].isin(brand_names)]
    else:
        up_filtered = unique_prods

    with bd2:
        sel_idx = st.selectbox(
            f"📱 Select {device_type[:-1].lower()}",
            options=range(len(up_filtered)),
            format_func=lambda x: (
                f"{up_filtered.iloc[x]['name']}  ·  "
                f"{up_filtered.iloc[x]['ram_gb']}GB RAM  "
                f"{up_filtered.iloc[x]['storage_gb']}GB  "
                f"({up_filtered.iloc[x]['website_count']} sites)"
            ),
            key="deal_product")

    sel_prod = up_filtered.iloc[sel_idx]
    st.markdown("---")

    # Fix: explicit category map — 'Mobile Phones'[:-1] = 'mobile phone' (wrong)
    category_map = {"Tablets": "tablet", "Mobile Phones": "mobile"}
    category_str = category_map.get(device_type, device_type.lower().split()[0])

    with st.spinner("🔍 Analysing prices across websites…"):
        recommendation = get_product_recommendation(
            name=sel_prod['name'],
            ram_gb=sel_prod['ram_gb'],
            storage_gb=sel_prod['storage_gb'],
            category=category_str,
            df=df
        )

    if not recommendation:
        # Fallback: build recommendation directly from the DataFrame
        # (handles cases where get_product_recommendation can't match on category)
        mask = (
            (df['name'] == sel_prod['name']) &
            (df['ram_gb'] == sel_prod['ram_gb']) &
            (df['storage_gb'] == sel_prod['storage_gb'])
        )
        prod_data = df[mask].copy()

        if prod_data.empty:
            st.error("No price data available for this product.")
            st.stop()

        # Build recommendation from raw data
        site_rows = []
        for site, grp in prod_data.groupby('website'):
            grp = grp.sort_values('date')
            cur = float(grp['price'].iloc[-1])
            old = float(grp[grp['date'] <= grp['date'].iloc[-1] - pd.Timedelta(days=7)]['price'].iloc[-1]) \
                  if len(grp) > 7 else float(grp['price'].iloc[0])
            chg = (cur - old) / old * 100 if old else 0
            url_val = grp.iloc[-1].get('URL') or grp.iloc[-1].get('url') or ''
            url_val = '' if str(url_val) == 'nan' else str(url_val)
            trend = "📉 Dropping" if chg < -1 else ("📈 Rising" if chg > 1 else "➡️ Stable")
            site_rows.append(dict(website=site.upper(), current_price=cur,
                                  price_change=chg, trend=trend, url=url_val,
                                  last_date=grp['date'].iloc[-1]))
        site_rows.sort(key=lambda r: r['current_price'])

        best = site_rows[0]
        recommendation = {
            'best_website':   best['website'],
            'best_price':     best['current_price'],
            'price_change_7d': best['price_change'],
            'trend':          best['trend'],
            'recommendation': "Lowest price available across tracked sites.",
            'best_url':       best['url'],
            'alternatives':   [
                dict(website=r['website'], current_price=r['current_price'],
                     price_change=r['price_change'], trend=r['trend'], url=r['url'])
                for r in site_rows[1:]
            ]
        }

    # ── COMPACT COMPARISON TABLE ─────────────────────────────
    st.markdown(f"### 📱 {sel_prod['name']}")
    st.markdown(f"**{sel_prod['ram_gb']}GB RAM · {sel_prod['storage_gb']}GB Storage**")
    st.markdown("---")
    st.markdown("### 🏆 Price Comparison Across Websites")

    all_sites = [dict(
        website=recommendation['best_website'],
        current_price=recommendation['best_price'],
        price_change=recommendation['price_change_7d'],
        trend=recommendation['trend'],
        url=recommendation['best_url'],
        is_best=True
    )] + [dict(**a, is_best=False) for a in recommendation.get('alternatives', [])]

    # HTML table
    rows_html = ""
    for r in all_sites:
        chg   = r['price_change']
        t_cls = "trend-down" if chg < -0.5 else ("trend-up" if chg > 0.5 else "trend-stable")
        badge = '<span class="best-badge">BEST</span> ' if r['is_best'] else ''
        link  = f'<a class="deal-link" href="{r["url"]}" target="_blank">Open ↗</a>' if r.get('url') else '—'
        rec   = "🟢 Buy now" if (r['is_best'] and chg <= 0) else \
                ("🔴 Rising" if chg > 2 else ("🟡 Watch" if r['is_best'] else ""))
        rows_html += f"""
        <tr>
            <td>{badge}{r['website']}</td>
            <td><strong>EGP {r['current_price']:,.0f}</strong></td>
            <td class="{t_cls}">{r['trend']}  ({chg:+.1f}%)</td>
            <td>{rec}</td>
            <td>{link}</td>
        </tr>"""

    st.markdown(f"""
    <table class="deal-table">
        <thead><tr>
            <th>Website</th>
            <th>Current Price</th>
            <th>7-Day Trend</th>
            <th>Recommendation</th>
            <th>Link</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Bar chart
    sites_  = [r['website'] for r in all_sites]
    prices_ = [r['current_price'] for r in all_sites]
    colors_ = ['#38a169'] + ['#667eea'] * (len(all_sites) - 1)

    fig_bar = go.Figure(go.Bar(
        x=sites_, y=prices_,
        marker_color=colors_,
        text=[f"EGP {p:,.0f}" for p in prices_],
        textposition='outside'))
    fig_bar.update_layout(
        title="Price Comparison",
        xaxis_title="Website", yaxis_title="Price (EGP)",
        height=380, plot_bgcolor='white', paper_bgcolor='white',
        showlegend=False, margin=dict(t=50))
    st.plotly_chart(fig_bar, use_container_width=True)


# ───────────────────────────────────────────────────────────
# TAB 3 — MARKET INSIGHTS
# ───────────────────────────────────────────────────────────
with tab_insights:

    st.markdown("## 📈 Market Insights")
    st.markdown("Which products had the biggest price changes over the tracked period?")

    changes = []
    for pk in df['product_key'].unique():
        pdf = df[df['product_key'] == pk].sort_values('date')
        if len(pdf) < 2:
            continue
        fp, lp = float(pdf['price'].iloc[0]), float(pdf['price'].iloc[-1])
        if fp > 0:
            changes.append({
                'Product':       pdf['name'].iloc[-1],
                'Website':       pdf['website'].iloc[-1].upper() if 'website' in pdf.columns else 'N/A',
                'Change %':      f"{((lp-fp)/fp*100):.1f}%",
                'Current Price': f"EGP {int(lp):,}",
                '_pct':          (lp - fp) / fp * 100
            })

    if not changes:
        st.warning("Not enough data to calculate price changes.")
    else:
        ch_df = pd.DataFrame(changes)
        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown("### 📉 Top Price Drops")
            drops = ch_df[ch_df['_pct'] < 0].nsmallest(10, '_pct')
            if not drops.empty:
                st.dataframe(drops[['Product','Website','Change %','Current Price']],
                             use_container_width=True, hide_index=True)
            else:
                st.info("No price drops detected.")
        with ic2:
            st.markdown("### 📈 Top Price Increases")
            rises = ch_df[ch_df['_pct'] > 0].nlargest(10, '_pct')
            if not rises.empty:
                st.dataframe(rises[['Product','Website','Change %','Current Price']],
                             use_container_width=True, hide_index=True)
            else:
                st.info("No price increases detected.")

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#a0aec0;font-size:0.85rem;padding:0.75rem;'>
    📱 Price Tracker Pro · Powered by LightGBM + XGBoost Ensemble
</div>
""", unsafe_allow_html=True)
