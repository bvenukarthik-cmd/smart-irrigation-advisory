import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import urllib.parse

# --- 1. PAGE & MODERN THEME CONFIGURATION ---
st.set_page_config(
    page_title="AquaAdvice | Smart Irrigation Intelligence",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Dashboard CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Top Banner Gradient Hero */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0d9488 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #f8fafc;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    /* Glassmorphism Metric Cards */
    .metric-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin: 4px 0;
    }
    .metric-badge {
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 20px;
        display: inline-block;
    }
    
    /* Status Action Banners */
    .status-card {
        padding: 20px;
        border-radius: 14px;
        margin-bottom: 16px;
        border-left: 6px solid;
    }
    .status-red {
        background-color: #fef2f2;
        border-color: #ef4444;
        color: #991b1b;
    }
    .status-green {
        background-color: #f0fdf4;
        border-color: #22c55e;
        color: #166534;
    }
    .status-yellow {
        background-color: #fffbeb;
        border-color: #f59e0b;
        color: #92400e;
    }
    
    /* Streamlit UI Polish */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "alert_logs" not in st.session_state:
    st.session_state.alert_logs = []

# --- 3. AGRONOMIC & METEOROLOGICAL DATABASES ---
INDIAN_DISTRICTS = {
    "Maharashtra": {
        "Pune": (18.5204, 73.8567),
        "Nashik": (19.9975, 73.7898),
        "Nagpur": (21.1458, 79.0882),
        "Kolhapur": (16.7050, 74.2433),
        "Solapur": (17.6599, 75.9064),
        "Aurangabad (Chh. Sambhajinagar)": (19.8762, 75.3433),
        "Amravati": (20.9320, 77.7523)
    },
    "Punjab": {
        "Ludhiana": (30.9010, 75.8573),
        "Amritsar": (31.6340, 74.8723),
        "Patiala": (30.3398, 76.3869),
        "Bhatinda": (30.2110, 74.9455),
        "Jalandhar": (31.3260, 75.5762)
    },
    "Uttar Pradesh": {
        "Varanasi": (25.3176, 82.9739),
        "Lucknow": (26.8467, 80.9462),
        "Kanpur": (26.4499, 80.3319),
        "Meerut": (28.9845, 77.7064),
        "Prayagraj": (25.4358, 81.8463),
        "Bareilly": (28.3670, 79.4304)
    },
    "Karnataka": {
        "Belagavi": (15.8497, 74.4977),
        "Dharwad / Hubli": (15.4589, 75.0078),
        "Mysuru": (12.2958, 76.6394),
        "Shivamogga": (13.9299, 75.5681),
        "Vijayapura (Bijapur)": (16.8302, 75.7100)
    },
    "Madhya Pradesh": {
        "Indore": (22.7196, 75.8577),
        "Ujjain": (23.1765, 75.7885),
        "Bhopal": (23.2599, 77.4126),
        "Jabalpur": (23.1815, 79.9864),
        "Hoshangabad (Narmadapuram)": (22.7519, 77.7289)
    },
    "Gujarat": {
        "Rajkot": (22.3039, 70.8022),
        "Surat": (21.1702, 72.8311),
        "Vadodara": (22.3072, 73.1812),
        "Junagadh": (21.5222, 70.4579),
        "Mehsana": (23.5880, 72.3693)
    },
    "Andhra Pradesh & Telangana": {
        "Guntur": (16.3067, 80.4365),
        "Warangal": (17.9689, 79.5941),
        "Kurnool": (15.8281, 78.0373),
        "Godavari (Rajahmundry)": (17.0005, 81.8040),
        "Nizamabad": (18.6725, 78.0941)
    },
    "Tamil Nadu": {
        "Coimbatore": (11.0168, 76.9558),
        "Thanjavur (Delta region)": (10.7870, 79.1378),
        "Madurai": (9.9252, 78.1198),
        "Salem": (11.6643, 78.1460)
    },
    "Haryana": {
        "Karnal": (29.6857, 76.9905),
        "Hisar": (29.1492, 75.7217),
        "Sirsa": (29.5349, 75.0290),
        "Ambala": (30.3782, 76.7767)
    },
    "Rajasthan": {
        "Kota": (25.2138, 75.8648),
        "Ganganagar": (29.9038, 73.8772),
        "Jaipur": (26.9124, 75.7873),
        "Bikaner": (28.0229, 73.3119)
    }
}

CROPS_KC = {
    "Wheat (गेहूं)": {"Initial": 0.35, "Mid": 1.15, "End": 0.45, "root_depth_m": 0.8},
    "Maize / Corn (मक्का)": {"Initial": 0.40, "Mid": 1.20, "End": 0.60, "root_depth_m": 1.0},
    "Rice / Paddy (धान)": {"Initial": 1.05, "Mid": 1.20, "End": 0.90, "root_depth_m": 0.6},
    "Cotton (कपास)": {"Initial": 0.35, "Mid": 1.20, "End": 0.65, "root_depth_m": 1.2},
    "Tomato / Vegetables (सब्जियां)": {"Initial": 0.60, "Mid": 1.15, "End": 0.80, "root_depth_m": 0.5},
    "Sugarcane (गन्ना)": {"Initial": 0.40, "Mid": 1.25, "End": 0.75, "root_depth_m": 1.5},
    "Soybean (सोयाबीन)": {"Initial": 0.40, "Mid": 1.15, "End": 0.50, "root_depth_m": 0.9},
    "Groundnut / Peanut (मूंगफली)": {"Initial": 0.40, "Mid": 1.15, "End": 0.60, "root_depth_m": 0.7}
}

SOIL_TYPES = {
    "Sandy Loam (बलुई दोमट)": {"field_capacity": 18.0, "wilting_point": 8.0, "desc": "Light texture; fast drainage. Requires short, frequent irrigation."},
    "Loam (दोमट मिट्टी)": {"field_capacity": 28.0, "wilting_point": 14.0, "desc": "Optimal agricultural soil with balanced water retention."},
    "Clay Loam (चिकनी दोमट)": {"field_capacity": 36.0, "wilting_point": 20.0, "desc": "Fine texture with high moisture holding capacity."},
    "Black Clay / Regur (काली मिट्टी)": {"field_capacity": 42.0, "wilting_point": 24.0, "desc": "Very high retention; vulnerable to waterlogging if over-irrigated."}
}

IRRIGATION_METHODS = {
    "Drip Irrigation (ड्रिप/टपक)": {"efficiency": 0.90, "desc": "Precision delivery directly to roots (90% application efficiency)."},
    "Sprinkler System (फव्वारा)": {"efficiency": 0.75, "desc": "Simulates precipitation across crop canopy (75% application efficiency)."},
    "Surface / Flood (पारंपरिक बहाव)": {"efficiency": 0.55, "desc": "Traditional flood run; up to 45% lost to runoff and evaporation."}
}

# --- 4. WEATHER & ET0 FETCHER ---
@st.cache_data(ttl=3600)
def fetch_weather_data(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&daily=et0_fao_evapotranspiration,precipitation_sum,temperature_2m_max,temperature_2m_min"
        f"&timezone=auto&forecast_days=3"
    )
    try:
        res = requests.get(url, timeout=8).json()
        daily = res["daily"]
        return pd.DataFrame({
            "Date": daily["time"],
            "ET0_mm": daily["et0_fao_evapotranspiration"],
            "Rain_mm": daily["precipitation_sum"],
            "Temp_Max": daily["temperature_2m_max"]
        })
    except Exception:
        return pd.DataFrame({
            "Date": [datetime.today().strftime('%Y-%m-%d')],
            "ET0_mm": [4.8],
            "Rain_mm": [0.0],
            "Temp_Max": [32.0]
        })

# --- 5. SIDEBAR: PARAMETERS & FIELD CONTROLS ---
with st.sidebar:
    st.markdown("### 📍 Farm Profile")
    selected_state = st.selectbox(
        "State (राज्य)", 
        list(INDIAN_DISTRICTS.keys()),
        help="Select the geographic state of your farm.",
        key="sb_state_select"
    )
    selected_district = st.selectbox(
        "District / Tehsil (ज़िला)", 
        list(INDIAN_DISTRICTS[selected_state].keys()),
        help="Hyper-local weather and evapotranspiration data are fetched for this location.",
        key="sb_district_select"
    )
    lat, lon = INDIAN_DISTRICTS[selected_state][selected_district]
    
    st.markdown("---")
    st.markdown("### 🌱 Crop & Soil Configuration")
    crop = st.selectbox(
        "Crop Type (फसल)", 
        list(CROPS_KC.keys()),
        help="Select your cultivated crop to determine root depth and crop coefficient (Kc).",
        key="sb_crop_select"
    )
    stage = st.selectbox(
        "Growth Stage (अवस्था)", 
        ["Initial (प्रारंभिक)", "Mid (मध्य वृद्धि)", "End (परिपक्वता)"],
        help="Crop water demand peaks during the Mid-season reproductive phase.",
        key="sb_stage_select"
    )
    stage_key = "Initial" if "Initial" in stage else ("Mid" if "Mid" in stage else "End")
    
    soil = st.selectbox(
        "Soil Texture (मिट्टी)", 
        list(SOIL_TYPES.keys()),
        help="Soil texture determines moisture retention limits (Field Capacity and Wilting Point).",
        key="sb_soil_select"
    )
    st.caption(f"💡 *{SOIL_TYPES[soil]['desc']}*")

    st.markdown("---")
    st.markdown("### ⚙️ Hydraulic Delivery Setup")
    method = st.selectbox(
        "Irrigation Method (सिंचाई प्रकार)",
        list(IRRIGATION_METHODS.keys()),
        help="System efficiency directly determines how much extra water must be pumped.",
        key="sb_method_select"
    )
    field_area_acres = st.number_input(
        "Field Area (एकड़)", 
        min_value=0.1, value=1.0, step=0.1,
        help="Total cultivated acreage (1 Acre = 4,046.86 m²).",
        key="sb_area_input"
    )
    current_soil_moisture = st.slider(
        "Current Soil Moisture (% Vol)", 
        min_value=5.0, max_value=50.0, value=18.0,
        help="Volumetric moisture content from your root-zone probe sensor.",
        key="sb_moisture_slider"
    )
    pump_flow_rate = st.number_input(
        "Pump Flow Rate (Liters/Hour)", 
        min_value=500, value=5000, step=500,
        help="Water discharge capacity of your motor/pump setup.",
        key="sb_flow_rate_input"
    )

# --- 6. CORE FAO-56 SCIENTIFIC ENGINE ---
weather_df = fetch_weather_data(lat, lon)
today_weather = weather_df.iloc[0]

et0_today = today_weather["ET0_mm"] if today_weather["ET0_mm"] is not None else 4.5
rain_today = today_weather["Rain_mm"] if today_weather["Rain_mm"] is not None else 0.0
kc_val = CROPS_KC[crop][stage_key]
etc_today = et0_today * kc_val

soil_info = SOIL_TYPES[soil]
fc = soil_info["field_capacity"]
wp = soil_info["wilting_point"]
mad_threshold = wp + 0.5 * (fc - wp)

root_depth_mm = CROPS_KC[crop]["root_depth_m"] * 1000

if current_soil_moisture < fc:
    moisture_deficit_mm = ((fc - current_soil_moisture) / 100.0) * root_depth_mm
else:
    moisture_deficit_mm = 0.0

p_effective = rain_today * 0.8
net_irrigation_depth_mm = max(0.0, etc_today + moisture_deficit_mm - p_effective)

method_efficiency = IRRIGATION_METHODS[method]["efficiency"]
gross_irrigation_depth_mm = net_irrigation_depth_mm / method_efficiency

area_sq_m = field_area_acres * 4046.86
water_volume_liters = gross_irrigation_depth_mm * area_sq_m
pump_runtime_hours = water_volume_liters / pump_flow_rate
hours = int(pump_runtime_hours)
mins = int((pump_runtime_hours % 1) * 60)

# --- 7. MAIN DASHBOARD: HERO BANNER ---
st.markdown(f"""
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <h1 class="hero-title">💧 AquaAdvice Precision Engine</h1>
            <p class="hero-subtitle">Smart agro-meteorological advisory for <b>{selected_district}, {selected_state}</b> | Crop: <b>{crop.split('(')[0]}</b> ({stage_key})</p>
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.15);">
            <span style="font-size: 12px; color: #cbd5e1;">Delivery Method:</span><br>
            <b style="color: #38bdf8;">{method.split('(')[0]} ({int(method_efficiency*100)}% Eff.)</b>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 8. TOP 4 METRIC CARDS ---
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Atmospheric Demand (ET₀)</div>
        <div class="metric-val">{et0_today:.2f} <span style="font-size: 14px; font-weight: normal; color: #64748b;">mm/day</span></div>
        <span class="metric-badge" style="background: #e0f2fe; color: #0284c7;">Reference Grass Penman</span>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Crop Water Need (ETc)</div>
        <div class="metric-val">{etc_today:.2f} <span style="font-size: 14px; font-weight: normal; color: #64748b;">mm/day</span></div>
        <span class="metric-badge" style="background: #fef3c7; color: #d97706;">Kc Factor: {kc_val}</span>
    </div>
    """, unsafe_allow_html=True)

with m3:
    rain_color = "#dcfce7" if rain_today > 0 else "#f1f5f9"
    rain_text = "#15803d" if rain_today > 0 else "#64748b"
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Forecast Precipitation</div>
        <div class="metric-val">{rain_today:.1f} <span style="font-size: 14px; font-weight: normal; color: #64748b;">mm</span></div>
        <span class="metric-badge" style="background: {rain_color}; color: {rain_text};">Effective Credit: {p_effective:.1f} mm</span>
    </div>
    """, unsafe_allow_html=True)

with m4:
    moist_color = "#fef2f2" if current_soil_moisture < mad_threshold else "#f0fdf4"
    moist_text = "#dc2626" if current_soil_moisture < mad_threshold else "#16a34a"
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Soil Root-Zone Moisture</div>
        <div class="metric-val">{current_soil_moisture:.1f}%</div>
        <span class="metric-badge" style="background: {moist_color}; color: {moist_text};">Threshold: {mad_threshold:.1f}% | FC: {fc:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# --- 9. TABBED SECTION ARCHITECTURE ---
tab_advisory, tab_analytics, tab_dispatch, tab_forecast = st.tabs([
    "📋 Action Plan & Gauge", 
    "💰 Savings & Carbon Analytics", 
    "📲 WhatsApp/SMS Gateway", 
    "🗺️ Satellite & 3-Day Forecast"
])

# --- TAB 1: ACTION PLAN & SENSOR GAUGE ---
with tab_advisory:
    col_left, col_right = st.columns([1.3, 1])
    
    clean_crop = crop.split('(')[0].strip()
    
    if current_soil_moisture > fc:
        status_tag = "NO IRRIGATION"
        action_text_en = f"Soil moisture is optimal ({current_soil_moisture}%). No irrigation required today."
        action_text_hi = f"मिट्टी में पर्याप्त नमी है ({current_soil_moisture}%)। आज सिंचाई की आवश्यकता नहीं है।"
        banner_html = f"""
        <div class="status-card status-green">
            <h3 style="margin: 0 0 6px 0;">🟢 Optimal Soil Moisture — No Irrigation Required</h3>
            <p style="margin: 0; font-size: 14px;">The soil profile is currently at or above Field Capacity (<b>{fc}%</b>). Additional watering will result in runoff or waterlogging.</p>
        </div>
        """
    elif current_soil_moisture > mad_threshold and rain_today > etc_today:
        status_tag = "POSTPONE IRRIGATION"
        action_text_en = f"Rain expected ({rain_today:.1f} mm). Postpone irrigation to save water."
        action_text_hi = f"बारिश की संभावना है ({rain_today:.1f} मिमी)। पानी बचाने के लिए सिंचाई टालें।"
        banner_html = f"""
        <div class="status-card status-yellow">
            <h3 style="margin: 0 0 6px 0;">🟡 Rainfall Forecasted — Postpone Irrigation</h3>
            <p style="margin: 0; font-size: 14px;">Current root-zone moisture is sufficient and <b>{rain_today:.1f} mm</b> precipitation is expected. Hold off pumping to conserve power.</p>
        </div>
        """
    else:
        status_tag = "IRRIGATE TODAY"
        action_text_en = f"Irrigate {clean_crop} today: Run pump for {hours}h {mins}m ({water_volume_liters:,.0f} L). Best window: 05:30 AM - 08:30 AM."
        action_text_hi = f"आज {clean_crop} की सिंचाई करें: मोटर {hours} घंटे {mins} मिनट चलाएं ({water_volume_liters:,.0f} लीटर)। समय: सुबह 05:30 से 08:30 बजे।"
        banner_html = f"""
        <div class="status-card status-red">
            <h3 style="margin: 0 0 6px 0;">🔴 Irrigation Recommended Today</h3>
            <p style="margin: 0; font-size: 14px;">Root-zone moisture has dropped below the Management Allowed Depletion threshold (<b>{mad_threshold:.1f}%</b>). Refill required.</p>
        </div>
        """

    with col_left:
        st.markdown(banner_html, unsafe_allow_html=True)
        
        # Operational summary card
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
            <h4 style="margin-top: 0; color: #0f172a; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px;">⚡ Operational Prescription</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                <div>
                    <span style="font-size: 12px; color: #64748b;">Gross Irrigation Depth</span><br>
                    <b style="font-size: 18px; color: #0284c7;">{gross_irrigation_depth_mm:.2f} mm</b>
                </div>
                <div>
                    <span style="font-size: 12px; color: #64748b;">Total Water Volume</span><br>
                    <b style="font-size: 18px; color: #0284c7;">{water_volume_liters:,.0f} Liters <span style="font-size: 13px; color: #64748b;">({water_volume_liters/1000:.1f} m³)</span></b>
                </div>
                <div>
                    <span style="font-size: 12px; color: #64748b;">Recommended Pump Runtime</span><br>
                    <b style="font-size: 18px; color: #059669;">{hours}h {mins}m</b>
                </div>
                <div>
                    <span style="font-size: 12px; color: #64748b;">Application Window</span><br>
                    <b style="font-size: 16px; color: #d97706;">05:30 AM – 08:30 AM</b>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 FAO-56 Mathematical Step-by-Step Proof"):
            st.markdown(f"""
            * **Step 1: Crop ET ($ET_c$):** ${et0_today:.2f}\\text{{ mm (ET0)}} \\times {kc_val}\\text{{ (Kc)}} = \\mathbf{{{etc_today:.2f}\\text{{ mm}}}}$
            * **Step 2: Soil Depletion Deficit:** $({fc}\\% - {current_soil_moisture}\\%) \\times {root_depth_mm}\\text{{ mm}} = \\mathbf{{{moisture_deficit_mm:.2f}\\text{{ mm}}}}$
            * **Step 3: Precipitation Offset:** ${rain_today:.1f}\\text{{ mm Rain}} \\times 0.8 = \\mathbf{{{p_effective:.2f}\\text{{ mm}}}}$
            * **Step 4: System Gross Adjustment:** $(\\text{{ETc}} + \\text{{Deficit}} - \\text{{Rain}}) \\div {method_efficiency}\\text{{ (Eff.)}} = \\mathbf{{{gross_irrigation_depth_mm:.2f}\\text{{ mm}}}}$
            """)

    with col_right:
        # High-definition Plotly Gauge with explicit unique key
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_soil_moisture,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Soil Moisture Status (% Vol)", 'font': {'size': 16, 'family': 'Plus Jakarta Sans'}},
            gauge={
                'axis': {'range': [0, 50], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                'bar': {'color': "#0284c7", 'thickness': 0.25},
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "#cbd5e1",
                'steps': [
                    {'range': [0, wp], 'color': '#fee2e2'},
                    {'range': [wp, mad_threshold], 'color': '#fef3c7'},
                    {'range': [mad_threshold, fc], 'color': '#dcfce7'},
                    {'range': [fc, 50], 'color': '#e0f2fe'}
                ],
                'threshold': {
                    'line': {'color': "#ef4444", 'width': 3},
                    'thickness': 0.75,
                    'value': mad_threshold
                }
            }
        ))
        fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True, key="plotly_soil_moisture_gauge")
        st.caption("<div style='text-align: center; color: #64748b;'>🔴 Wilting Point | 🟡 Depletion Alert | 🟢 Optimal | 🔵 Field Capacity</div>", unsafe_allow_html=True)

# --- TAB 2: SAVINGS & CARBON ANALYTICS ---
with tab_analytics:
    conventional_flood_depth_mm = 60.0
    conventional_water_liters = conventional_flood_depth_mm * area_sq_m
    conventional_pump_hours = conventional_water_liters / pump_flow_rate

    c1, c2, c3 = st.columns(3)
    with c1:
        pump_hp = st.number_input("Pump Power (HP)", min_value=1.0, value=5.0, step=0.5, help="Motor power in horsepower.", key="tab2_pump_hp_input")
    with c2:
        tariff_per_kwh = st.number_input("Electricity Tariff (₹ / kWh)", min_value=0.0, value=6.50, step=0.5, key="tab2_tariff_input")
    with c3:
        season_cycles = st.slider("Irrigation Events / Season", min_value=5, max_value=40, value=15, key="tab2_season_slider")

    pump_kw = pump_hp * 0.746
    precision_kwh_event = pump_runtime_hours * pump_kw
    conventional_kwh_event = conventional_pump_hours * pump_kw

    water_saved_liters = max(0.0, conventional_water_liters - water_volume_liters)
    energy_saved_kwh = max(0.0, conventional_kwh_event - precision_kwh_event)
    cost_saved_event = energy_saved_kwh * tariff_per_kwh
    cost_saved_season = cost_saved_event * season_cycles
    carbon_avoided_kg = energy_saved_kwh * season_cycles * 0.82

    # Comparative Metric Cards
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Water Saved (Event)", f"{water_saved_liters:,.0f} L", f"{(water_saved_liters*100/conventional_water_liters if conventional_water_liters>0 else 0):.1f}% reduction")
    with s2:
        st.metric("Power Saved (Event)", f"{energy_saved_kwh:.2f} kWh", "Direct Grid Relief")
    with s3:
        st.metric("Bill Savings (Event)", f"₹ {cost_saved_event:,.2f}", "Per Watering Event")
    with s4:
        st.metric("Estimated Season Savings", f"₹ {cost_saved_season:,.2f}", f"🌱 {carbon_avoided_kg:.1f} kg CO₂")

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # Clean comparative bar chart with explicit unique key
    comp_df = pd.DataFrame({
        "Metric": ["Water Volume (kL)", "Pump Runtime (Hrs)", "Energy (kWh)", "Cost per Event (₹)"],
        "Conventional Flood (60mm)": [conventional_water_liters / 1000, conventional_pump_hours, conventional_kwh_event, conventional_kwh_event * tariff_per_kwh],
        "AquaAdvice Precision": [water_volume_liters / 1000, pump_runtime_hours, precision_kwh_event, precision_kwh_event * tariff_per_kwh]
    })

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        x=comp_df["Metric"], 
        y=comp_df["Conventional Flood (60mm)"], 
        name="Conventional Flood (60mm)", 
        marker=dict(
            color="#ef4444",
            line=dict(color="#b91c1c", width=1.5)
        )
    ))
    fig_comp.add_trace(go.Bar(
        x=comp_df["Metric"], 
        y=comp_df["AquaAdvice Precision"], 
        name="AquaAdvice Precision", 
        marker=dict(
            color="#0d9488",
            line=dict(color="#0f766e", width=1.5)
        )
    ))
    fig_comp.update_layout(
        barmode="group",
        height=320,
        font=dict(family="Plus Jakarta Sans"),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_comp.update_yaxes(gridcolor="#f1f5f9")
    st.plotly_chart(fig_comp, use_container_width=True, key="plotly_savings_comparison_chart")

# --- TAB 3: DISPATCH GATEWAY ---
with tab_dispatch:
    d_col1, d_col2 = st.columns([1.2, 1])
    
    with d_col1:
        f1, f2 = st.columns(2)
        with f1:
            farmer_name = st.text_input("Farmer Name (किसान का नाम)", value="Ramesh Patil", key="dispatch_farmer_name")
            farmer_phone = st.text_input("Mobile Number", value="+91 98765 43210", key="dispatch_farmer_phone")
        with f2:
            channel = st.selectbox("Dispatch Channel", ["WhatsApp Advisory", "SMS Alert"], key="dispatch_channel_select")
            lang = st.radio("Advisory Language (भाषा)", ["English", "Hindi"], horizontal=True, key="dispatch_lang_select")

        selected_body = action_text_hi if lang == "Hindi" else action_text_en
        timestamp_str = datetime.now().strftime("%d-%b-%Y, %I:%M %p")
        
        message_payload = (
            f"💧 *AQUA ADVICE ALERT* 💧\n"
            f"👤 *Farmer:* {farmer_name}\n"
            f"📍 *Location:* {selected_district}, {selected_state}\n"
            f"🌱 *Crop:* {clean_crop} ({stage_key} Stage)\n"
            f"📊 *Status:* {status_tag}\n"
            f"💧 *Recommendation:* {selected_body}\n"
            f"🕒 *Issued:* {timestamp_str}"
        )

        st.markdown("**Message Payload Preview:**")
        st.info(message_payload)

        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("🚀 Trigger Instant Alert (Simulated)", use_container_width=True, type="primary", key="btn_simulated_dispatch"):
                with st.spinner(f"Connecting to {channel} Gateway..."):
                    time.sleep(1.0)
                st.session_state.alert_logs.insert(0, {
                    "Time": timestamp_str,
                    "Recipient": f"{farmer_name} ({farmer_phone})",
                    "Channel": channel,
                    "Status": "Delivered ✅"
                })
                st.success(f"Advisory delivered to {farmer_name}!")
        with btn2:
            clean_phone = farmer_phone.replace("+", "").replace(" ", "").replace("-", "")
            wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(message_payload)}"
            st.link_button("📲 Send Real WhatsApp Message", wa_url, use_container_width=True)

    with d_col2:
        st.markdown("**Real-Time Dispatch Audit Log**")
        if st.session_state.alert_logs:
            st.dataframe(pd.DataFrame(st.session_state.alert_logs), hide_index=True, use_container_width=True)
            if st.button("Clear History", use_container_width=True, key="btn_clear_dispatch_logs"):
                st.session_state.alert_logs = []
                st.rerun()
        else:
            st.caption("No alerts dispatched in this session yet.")

# --- TAB 4: SATELLITE & 3-DAY FORECAST ---
with tab_forecast:
    fc_col1, fc_col2 = st.columns([1, 1.2])
    
    with fc_col1:
        st.markdown("#### 🗺️ Agro-Climatic Grid Plot")
        map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
        st.map(map_df, zoom=9)
        st.caption(f"Coordinates: `{lat:.4f}°N, {lon:.4f}°E` ({selected_district}, {selected_state})")

    with fc_col2:
        st.markdown("#### 📅 3-Day Hydrological Water Balance")
        weather_df["Projected_ETc (mm)"] = weather_df["ET0_mm"] * kc_val
        weather_df["Net_Deficit (mm)"] = weather_df["Rain_mm"] - weather_df["Projected_ETc (mm)"]
        st.dataframe(
            weather_df.rename(columns={
                "Date": "Date",
                "ET0_mm": "ET₀ (mm)",
                "Rain_mm": "Rain (mm)",
                "Temp_Max": "Max Temp (°C)",
                "Projected_ETc (mm)": "Crop ETc (mm)",
                "Net_Deficit (mm)": "Net Balance (mm)"
            }),
            hide_index=True,
            use_container_width=True
        )
        st.caption("Positive balance = rain surplus; negative balance = soil moisture depletion.")
  
  
