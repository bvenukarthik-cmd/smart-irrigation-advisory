import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import urllib.parse

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Aqua Advice - Smart Irrigation Advisory",
    page_icon="💧",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if "alert_logs" not in st.session_state:
    st.session_state.alert_logs = []

# --- INDIAN AGRO-CLIMATIC DISTRICT MAPPING ---
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

# --- SCIENTIFIC DATA & AGRONOMIC CONSTANTS (FAO-56) ---
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
    "Sandy Loam (बलुई दोमट)": {"field_capacity": 18.0, "wilting_point": 8.0},
    "Loam (दोमट मिट्टी)": {"field_capacity": 28.0, "wilting_point": 14.0},
    "Clay Loam (चिकनी दोमट)": {"field_capacity": 36.0, "wilting_point": 20.0},
    "Black Clay / Regur (काली मिट्टी)": {"field_capacity": 42.0, "wilting_point": 24.0}
}

# --- LIVE WEATHER & ET0 API (Open-Meteo) ---
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

# --- TITLE & SUBHEADER ---
st.title("💧 Aqua Advice: Field-Level Smart Irrigation System")
st.caption("Precision agricultural advisory powered by FAO-56 Penman-Monteith agro-meteorological modeling.")

# --- SIDEBAR: FARMER FRIENDLY LOCATION & FIELD INPUTS ---
with st.sidebar:
    st.header("📍 Field Location (स्थान चुनें)")
    selected_state = st.selectbox("State (राज्य)", list(INDIAN_DISTRICTS.keys()))
    selected_district = st.selectbox("District / Tehsil (ज़िला)", list(INDIAN_DISTRICTS[selected_state].keys()))
    
    lat, lon = INDIAN_DISTRICTS[selected_state][selected_district]
    st.caption(f"Coordinates: `{lat:.4f}°N, {lon:.4f}°E`")
    
    st.markdown("---")
    st.header("🌱 Crop & Soil Profile")
    crop = st.selectbox("Crop Type (फसल)", list(CROPS_KC.keys()))
    stage = st.selectbox("Growth Stage (फसल की अवस्था)", ["Initial (प्रारंभिक)", "Mid (मध्य वृद्धि)", "End (परिपक्वता)"])
    stage_key = "Initial" if "Initial" in stage else ("Mid" if "Mid" in stage else "End")
    soil = st.selectbox("Soil Type (मिट्टी का प्रकार)", list(SOIL_TYPES.keys()))
    
    st.markdown("---")
    st.header("⚙️ Field & Pump Setup")
    field_area_acres = st.number_input("Field Area (खेत का आकार - एकड़)", min_value=0.1, value=1.0, step=0.1)
    current_soil_moisture = st.slider("Soil Moisture Sensor (% Vol / नमी)", min_value=5.0, max_value=50.0, value=18.0)
    pump_flow_rate = st.number_input("Pump Flow Rate (पंप क्षमता - L/Hour)", min_value=500, value=5000, step=500)

# --- COMPUTATION CORE ---
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

area_sq_m = field_area_acres * 4046.86
water_volume_liters = net_irrigation_depth_mm * area_sq_m
pump_runtime_hours = water_volume_liters / pump_flow_rate

# --- DISPLAY LOCATION BADGE & METRICS ---
st.info(f"📍 Active Advisory for **{selected_district}, {selected_state}** | Crop: **{crop}** ({stage_key} stage)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Reference ET (ET₀)", f"{et0_today:.2f} mm/day")
col2.metric("Crop Need (ETc)", f"{etc_today:.2f} mm/day", f"Kc: {kc_val}")
col3.metric("Rainfall Forecast", f"{rain_today:.1f} mm")
col4.metric("Current Soil Moisture", f"{current_soil_moisture:.1f}%", f"Field Capacity: {fc}%")

st.markdown("---")

# --- ADVISORY DECISION & GAUGE ---
left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.subheader("📋 Field Action Plan")
    if current_soil_moisture > fc:
        st.success("🟢 **Soil is at/above Field Capacity.** No irrigation needed. Risk of waterlogging.")
        status_tag = "NO IRRIGATION (पर्याप्त नमी)"
        action_text_en = f"Soil moisture is optimal ({current_soil_moisture}%). No irrigation required today."
        action_text_hi = f"मिट्टी में पर्याप्त नमी है ({current_soil_moisture}%)। आज सिंचाई की आवश्यकता नहीं है।"
    elif current_soil_moisture > mad_threshold and rain_today > etc_today:
        st.info("🟡 **Sufficient Moisture + Rain Expected.** Postpone irrigation to save water.")
        status_tag = "POSTPONE (बारिश की संभावना)"
        action_text_en = f"Rain expected ({rain_today:.1f} mm). Postpone irrigation to save water."
        action_text_hi = f"बारिश की संभावना है ({rain_today:.1f} मिमी)। पानी बचाने के लिए सिंचाई टालें।"
    else:
        st.warning("🔴 **Irrigation Required Today.** Root-zone moisture has depleted below optimal threshold.")
        status_tag = "IRRIGATE TODAY (सिंचाई करें)"
        hours = int(pump_runtime_hours)
        mins = int((pump_runtime_hours % 1) * 60)
        clean_crop = crop.split('(')[0].strip()
        action_text_en = f"Irrigate {clean_crop} today: Run pump for {hours}h {mins}m ({water_volume_liters:,.0f} L). Best window: 05:30 AM - 08:30 AM."
        action_text_hi = f"आज {clean_crop} की सिंचाई करें: मोटर {hours} घंटे {mins} मिनट चलाएं ({water_volume_liters:,.0f} लीटर पानी)। सही समय: सुबह 05:30 से 08:30 बजे।"
        
        st.markdown(f"""
        - **Net Irrigation Depth:** `{net_irrigation_depth_mm:.2f} mm`
        - **Total Water Volume:** `{water_volume_liters:,.0f} Liters` (`{water_volume_liters/1000:.1f} m³`)
        - **Pump Runtime:** `{hours} Hours {mins} Minutes`
        - **Recommended Window:** Early Morning (05:30 AM – 08:30 AM) to minimize evaporation.
        """)

with right_col:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_soil_moisture,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Soil Moisture Level (%)"},
        gauge={
            'axis': {'range': [0, 50]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, wp], 'color': "#ff9999"},
                {'range': [wp, mad_threshold], 'color': "#ffe599"},
                {'range': [mad_threshold, fc], 'color': "#b6d7a8"},
                {'range': [fc, 50], 'color': "#9fc5e8"}
            ],
            'threshold': {'line': {'color': "red", 'width': 3}, 'thickness': 0.75, 'value': mad_threshold}
        }
    ))
    fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- FARMER SMS / WHATSAPP DISPATCH COMPONENT ---
st.markdown("---")
st.subheader("📲 Farmer Alert Dispatch System")
d_col1, d_col2 = st.columns([1.2, 1])

with d_col1:
    f1, f2 = st.columns(2)
    with f1:
        farmer_name = st.text_input("Farmer Name (किसान का नाम)", value="Ramesh Patil")
        farmer_phone = st.text_input("Mobile Number", value="+91 98765 43210")
    with f2:
        channel = st.selectbox("Dispatch Channel", ["WhatsApp Advisory", "SMS Alert"])
        lang = st.radio("Advisory Language (भाषा)", ["English", "Hindi"], horizontal=True)

    selected_body = action_text_hi if lang == "Hindi" else action_text_en
    timestamp_str = datetime.now().strftime("%d-%b-%Y, %I:%M %p")
    clean_crop = crop.split('(')[0].strip()
    
    message_payload = (
        f"💧 *AQUA ADVICE ALERT* 💧\n"
        f"👤 *Farmer:* {farmer_name}\n"
        f"📍 *Location:* {selected_district}, {selected_state}\n"
        f"🌱 *Crop:* {clean_crop} ({stage_key} Stage)\n"
        f"📊 *Status:* {status_tag}\n"
        f"💧 *Recommendation:* {selected_body}\n"
        f"🕒 *Issued:* {timestamp_str}"
    )

    st.markdown("**Advisory Message Preview:**")
    st.info(message_payload)

    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("🚀 Trigger Instant Alert (Simulated)", use_container_width=True, type="primary"):
            with st.spinner(f"Sending via {channel}..."):
                time.sleep(1.0)
            st.session_state.alert_logs.insert(0, {
                "Time": timestamp_str,
                "Recipient": f"{farmer_name} ({farmer_phone})",
                "Channel": channel,
                "Status": "Delivered ✅"
            })
            st.success(f"Alert delivered to {farmer_name}!")
    with btn2:
        clean_phone = farmer_phone.replace("+", "").replace(" ", "").replace("-", "")
        wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(message_payload)}"
        st.link_button("📲 Test on Real WhatsApp", wa_url, use_container_width=True)

with d_col2:
    st.markdown("**Real-Time Dispatch Log**")
    if st.session_state.alert_logs:
        st.dataframe(pd.DataFrame(st.session_state.alert_logs), hide_index=True, use_container_width=True)
        if st.button("Clear Log History", use_container_width=True):
            st.session_state.alert_logs = []
            st.rerun()
    else:
        st.caption("No alerts dispatched in this session yet.")

# --- COST & RESOURCE SAVINGS CALCULATOR ---
st.markdown("---")
st.subheader("💰 Resource & Energy Savings Analytics")

conventional_flood_depth_mm = 60.0
conventional_water_liters = conventional_flood_depth_mm * area_sq_m
conventional_pump_hours = conventional_water_liters / pump_flow_rate

with st.expander("⚡ Configure Tariff & Energy Parameters", expanded=False):
    t1, t2, t3 = st.columns(3)
    with t1:
        pump_hp = st.number_input("Pump Power (HP)", min_value=1.0, value=5.0, step=0.5)
    with t2:
        tariff_per_kwh = st.number_input("Electricity Tariff (₹ / kWh)", min_value=0.0, value=6.50, step=0.5)
    with t3:
        season_cycles = st.slider("Irrigation Cycles / Season", min_value=5, max_value=40, value=15)

pump_kw = pump_hp * 0.746
precision_kwh_event = pump_runtime_hours * pump_kw
conventional_kwh_event = conventional_pump_hours * pump_kw

water_saved_liters = max(0.0, conventional_water_liters - water_volume_liters)
energy_saved_kwh = max(0.0, conventional_kwh_event - precision_kwh_event)
cost_saved_event = energy_saved_kwh * tariff_per_kwh
cost_saved_season = cost_saved_event * season_cycles

s1, s2, s3, s4 = st.columns(4)
s1.metric("Water Saved (Event)", f"{water_saved_liters:,.0f} L")
s2.metric("Power Saved (Event)", f"{energy_saved_kwh:.2f} kWh")
s3.metric("Cost Saved (Event)", f"₹ {cost_saved_event:,.2f}")
s4.metric("Est. Season Savings", f"₹ {cost_saved_season:,.2f}")

comp_df = pd.DataFrame({
    "Metric": ["Water (kL)", "Pump Time (Hrs)", "Energy (kWh)", "Cost (₹)"],
    "Conventional Flood": [conventional_water_liters / 1000, conventional_pump_hours, conventional_kwh_event, conventional_kwh_event * tariff_per_kwh],
    "Aqua Advice": [water_volume_liters / 1000, pump_runtime_hours, precision_kwh_event, precision_kwh_event * tariff_per_kwh]
})

fig_comp = go.Figure()
fig_comp.add_trace(go.Bar(x=comp_df["Metric"], y=comp_df["Conventional Flood"], name="Conventional Flood", marker_color="#EF553B"))
fig_comp.add_trace(go.Bar(x=comp_df["Metric"], y=comp_df["Aqua Advice"], name="Aqua Advice", marker_color="#00CC96"))
fig_comp.update_layout(barmode="group", height=300, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_comp, use_container_width=True)


