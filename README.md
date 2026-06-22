# 📱 Price Tracker Pro — Tablets & Mobiles Egypt

> **AI-powered price forecasting & smart deal detection for tablets and mobile phones in the Egyptian market.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)](https://streamlit.io)
[![Supabase](https://img.shields.io/badge/Database-Supabase-green?logo=supabase)](https://supabase.com)
[![ML](https://img.shields.io/badge/ML-Ensemble%20Models-orange?logo=scikit-learn)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## 🚀 Overview

**Price Tracker Pro** is a full-stack machine learning application that tracks, forecasts, and analyzes prices of tablets and mobile phones listed across Egyptian e-commerce websites. It empowers buyers to make smarter purchasing decisions using AI-driven 7-day price forecasts, buy/wait/hold signals, and cross-store deal comparisons — all through a sleek, dark-themed Streamlit dashboard.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔮 **7-Day Price Forecast** | Ensemble ML model predicts next 7 days of prices per product |
| 🟢 **Buy / Wait / Hold Signals** | Intelligent signals based on historical range, recent trend, and forecast |
| 🎯 **Best Deal Finder** | Compares prices across multiple e-commerce websites for the same product |
| 🔥 **Smart Deals Tab** | Surfaces top deals across the whole catalog automatically |
| 📊 **Interactive Charts** | Plotly charts with historical prices, rolling averages, and forecast bands |
| 🔍 **Advanced Filtering** | Filter by brand, website, RAM, storage, and keyword search |
| 🗄️ **Supabase Integration** | Real-time data loading from a cloud PostgreSQL backend |
| 📥 **CSV Export** | Download filtered data and forecast results |

---

## 🧠 How It Works

### Machine Learning Pipeline

Two separate **ensemble models** are trained — one for tablets and one for mobile phones:

- **Input features:** product specs (brand, RAM, storage), website, historical prices, time features
- **Model type:** Ensemble (stacked regressors / gradient boosting ensemble saved as `.pkl`)
- **Forecast horizon:** 7 days forward per product
- **Evaluation metric:** MAE (Mean Absolute Error), used to render confidence bands on charts

## 🗂️ Project Structure

```
full_price_prediction/
│
├── streamlit_full_price_prediction.py   # Main Streamlit app (UI, tabs, charts, signals)
├── tablet_ensemble_streamlit.py         # Tablet model loader + forecast function
├── mobile_ensemble_streamlit.py         # Mobile model loader + forecast function
├── supabase_loader.py                   # Supabase data fetching & product recommendations
│
├── tablet_ensemble_model.pkl            # Trained ensemble model for tablets
├── mobile_ensemble_model.pkl            # Trained ensemble model for mobile phones
│
├── requirements.txt                     # Python dependencies
└── .devcontainer/                       # Dev container configuration
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Eslamhagag246/full_price_prediction.git
cd full_price_prediction
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Supabase

Create a `.env` file (or set environment variables / Streamlit secrets) with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
```

> The `supabase_loader.py` module reads these to connect to your PostgreSQL database.

### 4. Run the app

```bash
streamlit run streamlit_full_price_prediction.py
```

The app will open at `http://localhost:8501`.

---

## 📊 App Tabs

### 🔮 Price Forecast
Select any product from the filtered list and get:
- Full historical price chart with 7-day rolling average
- 7-day AI forecast with confidence band (±MAE)
- Buy / Wait / Hold signal with detailed explanation
- Key stats: current price, forecast price, % change, historical min/max

### 🎯 Best Deal Finder
Search for a product across all tracked e-commerce websites and get:
- Price comparison table ranked from lowest to highest
- Best deal highlighted with a badge
- Direct links to product listings
- Trend indicator (rising / dropping / stable)

### 🔥 Smart Deals
Auto-scans the full catalog and surfaces the top products where:
- Current price is significantly below recent average
- Model forecasts prices are about to rise (act fast)
- Historical position is near all-time lows

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit + custom CSS (dark blue gradient theme) |
| **Charts** | Plotly (interactive, white background for exports) |
| **ML Models** | Scikit-learn ensemble (pickled `.pkl` files) |
| **Database** | Supabase (PostgreSQL, real-time API) |
| **Language** | Python 3.10+ |
| **Fonts / Design** | Google Fonts (Inter), CSS variables |

---

## 🔧 Configuration & Caching

- Data is cached for **1 hour** (`@st.cache_data(ttl=3600)`) to avoid redundant Supabase calls.
- Model loading is done once at startup and stored in module-level variables.
- Session state (`st.session_state`) persists filter selections across tab switches.

---

## 📈 Data Schema

The app expects data loaded from Supabase to contain at least these columns:

| Column | Description |
|---|---|
| `name` | Full product name |
| `brand` | Manufacturer brand |
| `website` | Source e-commerce website |
| `ram_gb` | RAM in GB |
| `storage_gb` | Internal storage in GB |
| `price` | Price in EGP |
| `date` | Date of the price observation |
| `product_key` | Unique identifier per product–website combination |

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push and open a Pull Request

Please open an issue first for major changes to discuss the approach.

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 👤 Author

**Eslam Hagag**  
📧 [GitHub Profile](https://github.com/Eslamhagag246)

---

> *Built to help Egyptian consumers stop guessing and start buying smarter.*
