import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta
import os

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="AI Device Price Intelligence",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# CUSTOM UI STYLE
# ==========================================

st.markdown("""
<style>

.main {
    background-color:#0e1117;
}

h1,h2,h3{
    color:#4CAF50;
}

.metric-card{
    background:#1c1f26;
    padding:15px;
    border-radius:10px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================

st.markdown("""
# 📊 AI Device Price Intelligence Dashboard
### Real-time analysis and forecasting for **Mobile & Tablet Prices**
""")

# ==========================================
# IMPORT MODELS
# ==========================================

MODELS_LOADED = {'tablet': False, 'mobile': False}
tablet_model = None
mobile_model = None

try:
    from tablet_model_newVersion import (
        load_and_preprocess_data as load_tablet_data_func,
        forecast_product as forecast_tablet_func,
        load_global_model as load_tablet_model
    )
    # Try to load pre-trained model
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
    # Try to load pre-trained model
    try:
        mobile_model = load_mobile_model()
        MODELS_LOADED['mobile'] = True
    except:
        st.sidebar.warning("⚠️ Mobile model not trained yet")
except ImportError as e:
    st.error(f"❌ Error importing mobile_model_newVersion.py: {str(e)}")



# ==========================================
# LOAD DATA
# ==========================================

@st.cache_data
def load_tablet_data():

    path = "tablets_cleaned_continuous.csv"

    if os.path.exists(path):

        return load_tablets(path)

    return None


@st.cache_data
def load_mobile_data():

    path = "mobile_cleaned_70K.csv"

    if os.path.exists(path):

        return load_mobiles(path)

    return None


# ==========================================
# PRICE TREND CHART
# ==========================================

def price_chart(history_dates, history_prices, forecast_dates, forecast_prices):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=history_dates,
            y=history_prices,
            name="Historical Price",
            mode="lines+markers"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_prices,
            name="Forecast",
            mode="lines+markers",
            line=dict(dash="dash")
        )
    )

    fig.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Price (EGP)"
    )

    return fig


# ==========================================
# FORECAST TABLE
# ==========================================

def build_forecast_table(dates, prices):

    df = pd.DataFrame({
        "Date":dates,
        "Predicted Price":prices
    })

    stats = {
        "min":np.min(prices),
        "max":np.max(prices),
        "avg":np.mean(prices)
    }

    return df,stats


# ==========================================
# MARKET INSIGHTS
# ==========================================

def market_insights(df):

    latest = df.sort_values("date").groupby("product_key").tail(1)

    rising = latest.sort_values("price",ascending=False).head(5)

    falling = latest.sort_values("price").head(5)

    return rising, falling


# ==========================================
# DASHBOARD VIEW
# ==========================================

def dashboard(df, forecast_func, device):

    if df is None:

        st.warning("Dataset not found")

        return

    st.sidebar.header("Filters")

    brand = st.sidebar.selectbox("Brand", sorted(df["brand"].dropna().unique()))
    ram = st.sidebar.selectbox("RAM", sorted(df["ram_gb"].dropna().unique()))
    storage = st.sidebar.selectbox("Storage", sorted(df["storage_gb"].dropna().unique()))

    filtered = df[
        (df["brand"]==brand) &
        (df["ram_gb"]==ram) &
        (df["storage_gb"]==storage)
    ]

    product = st.selectbox("Select Product", filtered["name"].unique())

    pdf = filtered[filtered["name"]==product].sort_values("date")

    if len(pdf)<10:

        st.warning("Not enough data")

        return

    # forecast

    forecast_dates, forecast_prices = forecast_func(pdf)

    history_dates = pdf["date"]
    history_prices = pdf["price"]

    # ==========================================
    # KPI SECTION
    # ==========================================

    col1,col2,col3,col4 = st.columns(4)

    current = history_prices.iloc[-1]
    predicted = forecast_prices[-1]

    change = predicted-current

    col1.metric("Current Price", f"{current:,.0f} EGP")
    col2.metric("7-Day Forecast", f"{predicted:,.0f} EGP", f"{change:,.0f}")
    col3.metric("Observations", len(pdf))
    col4.metric("Average Price", f"{history_prices.mean():,.0f} EGP")

    # ==========================================
    # PRICE CHART
    # ==========================================

    st.subheader("📈 Price Trend & Forecast")

    st.plotly_chart(
        price_chart(history_dates,history_prices,forecast_dates,forecast_prices),
        use_container_width=True
    )

    # ==========================================
    # FORECAST TABLE
    # ==========================================

    st.subheader("📅 7-Day Forecast Table")

    forecast_df,stats = build_forecast_table(forecast_dates,forecast_prices)

    st.dataframe(forecast_df)

    col1,col2,col3 = st.columns(3)

    col1.metric("Min Forecast", f"{stats['min']:,.0f} EGP")
    col2.metric("Max Forecast", f"{stats['max']:,.0f} EGP")
    col3.metric("Avg Forecast", f"{stats['avg']:,.0f} EGP")


# ==========================================
# INSIGHTS SECTION
# ==========================================

def insights_section(df):

    st.subheader("📊 Market Insights")

    rising, falling = market_insights(df)

    col1,col2 = st.columns(2)

    with col1:

        st.write("🔥 Highest Price Products")

        st.dataframe(rising[["name","price","website"]])

    with col2:

        st.write("📉 Lowest Price Products")

        st.dataframe(falling[["name","price","website"]])


# ==========================================
# MAIN TABS
# ==========================================

tab1,tab2,tab3 = st.tabs(["📱 Mobile","💻 Tablet","📊 Market Insights"])

# MOBILE
with tab1:

    st.header("Mobile Price Forecast")

    if MODELS_AVAILABLE:

        df = load_mobile_data()

        dashboard(df,forecast_mobile,"mobile")


# TABLET
with tab2:

    st.header("Tablet Price Forecast")

    if MODELS_AVAILABLE:

        df = load_tablet_data()

        dashboard(df,forecast_tablet,"tablet")


# INSIGHTS
with tab3:

    df_mobile = load_mobile_data()

    if df_mobile is not None:

        insights_section(df_mobile)
