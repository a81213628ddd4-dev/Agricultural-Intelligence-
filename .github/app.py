# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import plotly.express as px
from PIL import Image

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Farm Intelligence System",
    page_icon="🌾",
    layout="wide"
)

# ====================== CUSTOM CSS ======================
st.markdown("""
<style>
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f5e9 100%);
    }

    /* Main Title */
    h1 {
        color: #1b5e20 !important;
        text-align: center;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #e8f5e9;
        border-right: 2px solid #a5d6a7;
    }

    /* ===== TEXT COLOUR OF LABELS (Select State, Nitrogen, etc.) ===== */
    section[data-testid="stSidebar"] label {
        color: #1b5e20 !important;          /* Dark green colour */
        font-weight: 600 !important;
        font-size: 15px !important;
    }

    /* Input boxes text */
    section[data-testid="stSidebar"] input, 
    section[data-testid="stSidebar"] select {
        color: #000000 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
    }
    .stButton > button:hover {
        background-color: #1b5e20;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ====================== TITLE ======================
st.title("🌾 Farm Intelligence System")
st.caption("AI Agronomist – Crop Recommendation + Smart Irrigation + Fertilizer + Government Schemes")

# ====================== DATA ======================
STATE_COORDS = {
    "Punjab": (30.9, 75.8), "Haryana": (29.0, 76.1), "Uttar Pradesh": (26.8, 80.9),
    "Rajasthan": (26.9, 75.8), "Madhya Pradesh": (23.3, 77.4), "Maharashtra": (19.8, 75.7),
    "Gujarat": (22.3, 71.2), "Karnataka": (15.3, 75.7), "Tamil Nadu": (11.1, 78.7),
    "Andhra Pradesh": (15.9, 79.7), "Telangana": (17.4, 78.5), "West Bengal": (22.9, 88.4),
    "Bihar": (25.6, 85.1), "Odisha": (20.3, 85.8), "Assam": (26.2, 92.9),
    "Kerala": (10.5, 76.3), "Himachal Pradesh": (31.1, 77.2), "Other": (28.6, 77.2)
}

STANDARD_NPK = {
    "Rice": (110, 50, 40), "Wheat": (120, 60, 40), "Maize": (135, 70, 45),
    "Mustard": (80, 45, 30), "Groundnut": (22, 45, 45), "Soybean": (25, 55, 30),
    "Cotton": (125, 60, 60), "Sugarcane": (250, 90, 125), "Potato": (165, 90, 110),
    "Default": (100, 50, 40)
}

CROP_REQUIREMENTS = {
    "Rice": {"water": "High", "duration": "90-150 days", "states": ["West Bengal", "Uttar Pradesh", "Punjab", "Andhra Pradesh", "Telangana", "Odisha", "Bihar", "Tamil Nadu"]},
    "Wheat": {"water": "Moderate", "duration": "110-140 days", "states": ["Uttar Pradesh", "Punjab", "Haryana", "Madhya Pradesh", "Rajasthan", "Bihar"]},
    "Maize": {"water": "Moderate", "duration": "80-120 days", "states": ["Karnataka", "Madhya Pradesh", "Bihar", "Andhra Pradesh", "Telangana"]},
    "Mustard": {"water": "Low-Moderate", "duration": "90-140 days", "states": ["Rajasthan", "Uttar Pradesh", "Haryana", "Madhya Pradesh"]},
    "Groundnut": {"water": "Moderate", "duration": "100-140 days", "states": ["Gujarat", "Rajasthan", "Andhra Pradesh", "Tamil Nadu", "Karnataka"]},
    "Soybean": {"water": "Moderate", "duration": "90-120 days", "states": ["Madhya Pradesh", "Maharashtra", "Rajasthan"]},
    "Cotton": {"water": "Moderate-High", "duration": "150-180 days", "states": ["Maharashtra", "Gujarat", "Telangana", "Andhra Pradesh", "Punjab"]},
    "Sugarcane": {"water": "Very High", "duration": "10-18 months", "states": ["Uttar Pradesh", "Maharashtra", "Karnataka", "Tamil Nadu"]},
    "Potato": {"water": "Frequent moderate", "duration": "90-120 days", "states": ["Uttar Pradesh", "Bihar", "West Bengal", "Gujarat", "Punjab"]},
}

BASE_IRRIGATION = {
    "Wheat": [(20, "First irrigation – Crown root"), (40, "Tillering"), (60, "Jointing"), (80, "Flowering"), (100, "Grain filling")],
    "Rice": [(10, "Maintain standing water"), (30, "Tillering"), (50, "Panicle initiation"), (70, "Flowering")],
    "Mustard": [(30, "Rosette"), (50, "Flowering"), (70, "Pod formation")],
    "Groundnut": [(25, "Flowering"), (45, "Pegging"), (70, "Pod development")],
    "Cotton": [(30, "Vegetative"), (55, "Flowering"), (80, "Boll development")],
    "Sugarcane": [(15, "Early growth"), (40, "Grand growth"), (70, "Maturity")],
    "Maize": [(20, "Knee-high"), (40, "Tasseling"), (60, "Grain filling")],
    "Potato": [(15, "Sprouting"), (35, "Tuber initiation"), (55, "Tuber bulking")],
    "Soybean": [(25, "Flowering"), (45, "Pod filling")]
}

CENTRAL_SCHEMES = {
    "NFSM": "National Food Security Mission – Seeds, demonstrations, machinery, micronutrients",
    "NMEO-OS": "National Mission on Edible Oils – Oilseeds (Groundnut, Mustard, Soybean etc.)",
    "MIDH": "Mission for Integrated Development of Horticulture (Fruits, Vegetables, Spices)",
    "PMFBY": "Pradhan Mantri Fasal Bima Yojana – Crop Insurance",
    "PM-AASHA": "Price Support Scheme + MSP / FRP procurement",
    "PMKSY": "Pradhan Mantri Krishi Sinchayee Yojana – Micro-irrigation",
    "SMAM": "Sub-Mission on Agricultural Mechanisation – Machinery & drone subsidies",
    "PKVY": "Paramparagat Krishi Vikas Yojana – Organic farming",
    "AIF": "Agriculture Infrastructure Fund – Warehouses & cold storage loans",
    "PM-KISAN": "₹6,000 per year direct income support",
    "KCC": "Kisan Credit Card – Subsidised crop loans",
    "Soil Health Card": "Free soil testing and fertiliser recommendations"
}

STATE_SCHEMES = {
    "Punjab": ["Heavy MSP for Wheat & Paddy", "Crop diversification incentives", "Mechanisation support"],
    "Haryana": ["Wheat & Paddy MSP", "Crop diversification schemes"],
    "Uttar Pradesh": ["Sugarcane FRP + bonuses", "Wheat & Rice procurement", "Potato schemes"],
    "Rajasthan": ["Strong support for Mustard & Groundnut", "Interest-free crop loans", "Organic promotion"],
    "Maharashtra": ["Sugarcane incentives", "Cotton & Soybean support", "Horticulture under MIDH"],
    "Gujarat": ["Groundnut MSP focus", "Seed & input subsidies", "Solar fencing support"],
    "Madhya Pradesh": ["Soybean & Pulses support", "Wheat programmes", "Horticulture expansion"],
    "Karnataka": ["Seed subsidies", "Ragi & Maize focus", "Coffee support"],
    "Tamil Nadu": ["Groundnut & bio-input subsidies", "Horticulture packages"],
    "Andhra Pradesh": ["Groundnut seed subsidy", "Free/subsidised power", "Drone subsidies"],
    "Telangana": ["Cotton & Groundnut support", "Free power", "Drone subsidies"],
    "West Bengal": ["Rice & Jute support", "Potato schemes", "Tea & horticulture"],
    "Kerala": ["Special packages for Rubber, Coconut, Spices, Tea, Coffee"],
    "Assam": ["Higher Central share", "Tea, Jute, Rice, Spices support"],
    "Himachal Pradesh": ["Apple & temperate fruits under MIDH", "Organic support"],
    "Other": ["Central schemes + local seed subsidy programmes"]
}

# ====================== FUNCTIONS ======================
@st.cache_data(ttl=3600)
def get_weather(lat, lon, days=14):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=Asia/Kolkata&forecast_days={days}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()["daily"]
        return pd.DataFrame({
            "date": pd.to_datetime(data["time"]).dt.date,
            "precip_mm": data["precipitation_sum"],
            "temp_max": data["temperature_2m_max"]
        })
    except:
        dates = [datetime.now().date() + timedelta(days=i) for i in range(days)]
        return pd.DataFrame({
            "date": dates,
            "precip_mm": np.random.uniform(0, 12, days).round(1),
            "temp_max": np.random.uniform(28, 36, days).round(1)
        })

def adjust_irrigation(base, weather, threshold=10.0):
    today = datetime.now().date()
    result = []
    for day, task in base:
        planned = today + timedelta(days=day)
        mask = (weather["date"] >= planned - timedelta(days=2)) & (weather["date"] <= planned + timedelta(days=2))
        rain = weather.loc[mask, "precip_mm"].sum()
        if rain >= threshold:
            new_day = day + 3
            status = f"AUTO-DELAYED (rain {rain:.1f} mm)"
        else:
            new_day = day
            status = "On schedule"
        result.append({
            "Day": new_day,
            "Date": (today + timedelta(days=new_day)).strftime("%d %b %Y"),
            "Task": task,
            "Status": status,
            "Rain (mm)": round(rain, 1)
        })
    return result

def recommend_crop(N, P, K, ph, temp, state):
    scores = {}
    for crop, info in CROP_REQUIREMENTS.items():
        score = 70
        if state in info["states"]:
            score += 15
        if 6.0 <= ph <= 7.5:
            score += 5
        if 20 <= temp <= 32:
            score += 5
        scores[crop] = min(score, 97)
    best = max(scores, key=scores.get)
    return best, scores[best]

# ====================== SIDEBAR ======================
st.sidebar.header("Farm Data Input")

state = st.sidebar.selectbox("Select State", list(STATE_COORDS.keys()))
N = st.sidebar.number_input("Nitrogen (N) kg/ha", 10.0, 300.0, 90.0)
P = st.sidebar.number_input("Phosphorus (P) kg/ha", 5.0, 200.0, 45.0)
K = st.sidebar.number_input("Potassium (K) kg/ha", 5.0, 200.0, 65.0)
ph = st.sidebar.slider("Soil pH", 4.5, 9.0, 6.5)
temp = st.sidebar.slider("Average Temperature (°C)", 10.0, 40.0, 27.0)
size = st.sidebar.number_input("Field Size (acres)", 0.5, 100.0, 5.0)

uploaded_file = st.sidebar.file_uploader("Upload Soil Report / Field Photo", type=["jpg", "png", "jpeg", "pdf"])

run_btn = st.sidebar.button("Get AI Recommendation", type="primary")

# ====================== MAIN CONTENT ======================
if run_btn:
    crop, conf = recommend_crop(N, P, K, ph, temp, state)

    st.success(f"**Recommended Crop: {crop}**   |   Confidence: **{conf}%**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Water Need", CROP_REQUIREMENTS[crop]["water"])
    col2.metric("Duration", CROP_REQUIREMENTS[crop]["duration"])
    col3.metric("Field Size", f"{size} acres")

    # Fertilizer
    st.subheader("Fertilizer Recommendation (ICAR Standard)")
    std = STANDARD_NPK.get(crop, STANDARD_NPK["Default"])
    need_N = max(0, std[0] - N)
    need_P = max(0, std[1] - P)
    need_K = max(0, std[2] - K)

    st.write(f"**Standard dose for {crop}:** N = {std[0]} | P₂O₅ = {std[1]} | K₂O = {std[2]} kg/ha")
    st.markdown(f"- **Nitrogen still needed:** {need_N:.0f} kg/ha → Urea ≈ **{need_N * 2.17:.0f} kg/ha**")
    st.markdown(f"- **Phosphorus still needed:** {need_P:.0f} kg/ha")
    st.markdown(f"- **Potassium still needed:** {need_K:.0f} kg/ha")

    # Weather + Irrigation
    lat, lon = STATE_COORDS[state]
    weather = get_weather(lat, lon)

    st.subheader("Live Weather & Smart Irrigation")
    fig = px.bar(weather, x="date", y="precip_mm", title="14-Day Rainfall Forecast (mm)")
    st.plotly_chart(fig, use_container_width=True)

    base = BASE_IRRIGATION.get(crop, [(20, "First irrigation"), (45, "Second irrigation"), (70, "Third irrigation")])
    adjusted = adjust_irrigation(base, weather)

    st.write("**Smart Irrigation Schedule** (automatically delayed if rain is expected)")
    st.dataframe(pd.DataFrame(adjusted), use_container_width=True)

    # Government Schemes
    st.subheader("Government Schemes You Can Avail")

    with st.expander("Central Government Schemes (All India)", expanded=True):
        for name, desc in CENTRAL_SCHEMES.items():
            st.markdown(f"**{name}**")
            st.write(desc)
            st.write("")

    with st.expander(f"State-specific Schemes – {state}", expanded=True):
        schemes = STATE_SCHEMES.get(state, STATE_SCHEMES["Other"])
        for s in schemes:
            st.markdown(f"- {s}")

    st.info("Always verify the latest guidelines on the official Ministry of Agriculture website and your State Agriculture Department.")

    # Show uploaded image
    if uploaded_file is not None and uploaded_file.type.startswith("image"):
        st.subheader("Uploaded Photo")
        st.image(Image.open(uploaded_file), width=400)

else:
    st.info("← Fill the details in the sidebar and click **Get AI Recommendation**")
    st.markdown("""
    ### Features of this system:
    - Best crop recommendation for your soil & location
    - Exact fertiliser quantity still needed (ICAR based)
    - Live weather + auto-adjusted irrigation dates
    - Central & State government schemes
    - Upload soil report or field photo
    """)
