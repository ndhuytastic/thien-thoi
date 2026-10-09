import streamlit as st
import datetime
import pytz
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import json
import os

# ==========================================
# CẤU HÌNH TRANG & STATE
# ==========================================
st.set_page_config(page_title="Tinh Tượng Trạch Nhật", layout="wide", initial_sidebar_state="expanded")

st.markdown("<h3 style='text-align: center; color: #2C3E50; margin-top: -40px; margin-bottom: 20px; font-weight: bold;'>TINH TƯỢNG TRẠCH NHẬT</h3>", unsafe_allow_html=True)

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {height: 45px; white-space: pre-wrap; background-color: #F8F9F9; border-radius: 2px 2px 0 0; padding: 0 20px; border: 1px solid #E5E7E9; border-bottom: none;}
    .stTabs [aria-selected="true"] {background-color: #FFFFFF; border-top: 3px solid #2C3E50; font-weight: bold;}
    div[data-testid="stMarkdownContainer"] > blockquote {border-left-color: #7F8C8D; background-color: #F2F3F4; padding: 10px 15px;}
    .stCheckbox {margin-bottom: -10px;}
    </style>
""", unsafe_allow_html=True)

try:
    from skyfield.api import load, Topos
except ImportError:
    st.error("HỆ THỐNG YÊU CẦU KHỞI ĐỘNG LẠI MÁY CHỦ (REBOOT).")
    st.stop()

local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.datetime.now(local_tz)
if 'target_date' not in st.session_state: st.session_state.target_date = now.date()
if 'target_time' not in st.session_state: st.session_state.target_time = now.time()
if 'scan_results' not in st.session_state: st.session_state.scan_results = None 
if 'lat' not in st.session_state: st.session_state.lat = 21.0285
if 'lon' not in st.session_state: st.session_state.lon = 105.8542
if 'tz_str' not in st.session_state: st.session_state.tz_str = 'Asia/Ho_Chi_Minh'
if 'search_results' not in st.session_state: st.session_state.search_results = None

LOC_FILE = "saved_locations.json"
def load_saved_locations():
    if os.path.exists(LOC_FILE):
        with open(LOC_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}
def save_location(name, lat, lon, tz):
    data = load_saved_locations()
    data[name] = {'lat': lat, 'lon': lon, 'tz': tz}
    with open(LOC_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)

# ==========================================
# 1. DỮ LIỆU & CACHE
# ==========================================
@st.cache_data(ttl=3600)
def load_google_sheets():
    import urllib.request, csv, io
    warnings_list = []
    SHEET_WARNINGS_URL = "https://docs.google.com/spreadsheets/d/12Mq8O7AhR4BCJc_vw3GzRNhjpQp7j53DgJbHY-xyQ34/export?format=csv&gid=0"
    try:
        req = urllib.request.Request(SHEET_WARNINGS_URL)
        with urllib.request.urlopen(req) as response:
            csv_data = response.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_data))
        for row in reader:
            than_a = row.get('Than_A', '').strip()
            quan_he = row.get('Quan_He', '').strip()
            than_b = row.get('Than_B', '').strip()
            y_nghia = row.get('Y_Nghia', '').strip()
            if than_a and than_b: warnings_list.append({"category": than_a, "name": quan_he, "triggers": than_b, "desc": y_nghia})
    except: pass
    return warnings_list

@st.cache_resource
def load_astronomy_data():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = load_astronomy_data()
earth = eph['earth']

CELESTIAL_BODIES = {
    'Thái Dương':  {'char': '日', 'color': '#D35400', 'node': eph['sun']},
    'Thái Âm':     {'char': '月', 'color': '#7F8C8D', 'node': eph['moon']},
    'Thủy Tinh':   {'char': '水', 'color': '#2980B9', 'node': eph['mercury']},
    'Kim Tinh':    {'char': '金', 'color': '#F39C12', 'node': eph['venus']},
    'Hỏa Tinh':    {'char': '火', 'color': '#C0392B', 'node': eph['mars']},
    'Mộc Tinh':    {'char': '木', 'color': '#8E44AD', 'node': eph['jupiter barycenter']},
    'Thổ Tinh':    {'char': '土', 'color': '#8B4513', 'node': eph['saturn barycenter']},
    'Thiên Vương': {'char': '天', 'color': '#16A085', 'node': eph['uranus barycenter']},
    'Hải Vương':   {'char': '海', 'color': '#2E86C1', 'node': eph['neptune barycenter']},
    'Diêm Vương':  {'char': '冥', 'color': '#34495E', 'node': eph['pluto barycenter']}
}

CHAR_TO_VIET = {
    '甲':'Giáp', '乙':'Ất', '丙':'Bính', '丁':'Đinh', '戊':'Mậu', '己':'Kỷ', '庚':'Canh', '辛':'Tân', '壬':'Nhâm', '癸':'Quý',
    '子':'Tý', '丑':'Sửu', '寅':'Dần', '卯':'Mão', '辰':'Thìn', '巳':'Tỵ', '午':'Ngọ', '未':'Mùi', '申':'Thân', '酉':'Dậu', '戌':'Tuất', '亥':'Hợi',
    '乾':'Càn', '坤':'Khôn', '艮':'Cấn', '巽':'Tốn'
}
DI_CHI_ZH = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SƠN_24_ZH = ["子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳", "丙", "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥", "壬"]

def get_24_son(azimuth): return SƠN_24_ZH[int(((azimuth + 7.5) % 360) / 15)]
def get_di_chi_hoang_dao(degree): return DI_CHI_ZH[int(((degree + 105) % 360) / 30)]
def get_angular_diff_vec(a1, a2): return np.minimum(np.abs(a1 - a2), 360 - np.abs(a1 - a2))

# ==========================================
# 2. HÀM TÍNH TOÁN
# ==========================================
def calculate_positions(dt, lat, lon, active_bodies):
    time = ts.from_datetime(dt)
    location = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    results = []
    for name in active_bodies:
        info = CELESTIAL_BODIES[name]
        body_node = info['node']
        astrometric = earth.at(time).observe(body_node)
        try:
            from skyfield.framelib import ecliptic_J2000
            lat_ecl, lon_ecl, _ = astrometric.frame_latlon(ecliptic_J2000)
        except ImportError:
            lat_ecl, lon_ecl, _ = astrometric.ecliptic_latlon()

        alt, az, _ = location.at(time).observe(body_node).apparent().altaz()
        results.append({
            "Tên": name, "Ký Hiệu": info['char'], "Màu": info['color'],
            "Độ Hoàng Đạo": round(lon_ecl.degrees, 2), "Khu Vực Hoàng Đạo": get_di_chi_hoang_dao(lon_ecl.degrees),
            "Azimuth": round(az.degrees, 2), "Altitude": round(alt.degrees, 2), "Sơn Thực Địa": get_24_son(az.degrees)
        })
    return pd.DataFrame(results)

# ==========================================
# 3. HÀM VẼ ĐỒ HÌNH
# ==========================================
def draw_professional_luopan(df):
    fig = go.Figure()
    df['r_plot'] = 90 - df['Altitude']

    for idx, row in df.iterrows():
        marker_size = 14 if row['Tên'] in ['Thái Dương', 'Thái Âm'] else 10
        text_weight = "bold" if row['Tên'] in ['Thái Dương', 'Thái Âm'] else "normal"
        fig.add_trace(go.Scatterpolar(
            r=[row['r_plot']], theta=[row['Azimuth']], mode='markers+text',
            marker=dict(size=marker_size, color=row['Màu'], symbol='circle', line=dict(width=1, color='white')),
            text=f"<b>{row['Ký Hiệu']}</b>" if text_weight == "bold" else row['Ký Hiệu'],
            textposition="bottom center", textfont=dict(size=14, color="#000000", family="Arial"),
            name=row['Tên'], hoverinfo="text", hovertext=f"{row['Tên']}<br>Sơn: {row['Sơn Thực Địa']}<br>Azimuth: {row['Azimuth']}°<br>Altitude: {row['Altitude']}°"
        ))

    for i in range(24):
        border_angle = i * 15 + 7.5
        fig.add_trace(go.Scatterpolar(r=[0, 180], theta=[border_angle, border_angle], mode='lines', line=dict(color='#BDC3C7', width=1), hoverinfo='skip'))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(direction="clockwise", rotation=-90, tickmode="array", tickvals=[i * 15 for i in range(24)], ticktext=SƠN_24_ZH, showline=False, showgrid=False),
            radialaxis=dict(visible=False, range=[0, 180])
        ),
        showlegend=False, paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=20, b=20, l=20, r=20), height=500
    )
    fig.add_trace(go.Scatterpolar(r=[90, 90], theta=[0, 360], mode='lines', line=dict(color='#7F8C8D', width=1.5), hoverinfo='skip'))
    fig.add_trace(go.Scatterpolar(r=[180, 180], theta=[0, 360], mode='lines', line=dict(color='#333333', width=2), hoverinfo='skip'))
    return fig

def draw_ecliptic_chart(df_birth, df_target, clash_pairs):
    fig = go.Figure()
    tickvals = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
    ticktext = ["卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅"]
    
    for i in range(12):
        border_angle = i * 30 + 15
        fig.add_trace(go.Scatterpolar(r=[0, 100], theta=[border_angle, border_angle], mode='lines', line=dict(color='#E5E7E9', width=1, dash='solid'), hoverinfo='skip'))

    for idx, row in df_birth.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[50], theta=[row['Độ Hoàng Đạo']], mode='markers+text',
            marker=dict(size=10, color='#BDC3C7', symbol='circle'), 
            text=f"{row['Ký Hiệu']}", textposition="top center", textfont=dict(size=12, color="#7F8C8D"),
            name=f"{row['Tên']} (Sinh)", hoverinfo="text", hovertext=f"BẨM SINH: {row['Tên']}<br>Cung: {row['Khu Vực Hoàng Đạo']}<br>Độ: {row['Độ Hoàng Đạo']}°"
        ))

    for idx, row in df_target.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[80], theta=[row['Độ Hoàng Đạo']], mode='markers+text',
            marker=dict(size=12, color=row['Màu'], symbol='circle', line=dict(width=1, color='white')),
            text=f"<b>{row['Ký Hiệu']}</b>", textposition="bottom center", textfont=dict(size=14, color="#000000"),
            name=f"{row['Tên']} (Hiện)", hoverinfo="text", hovertext=f"DỰ KIẾN: {row['Tên']}<br>Cung: {row['Khu Vực Hoàng Đạo']}<br>Độ: {row['Độ Hoàng Đạo']}°"
        ))

    for clash in clash_pairs:
        fig.add_trace(go.Scatterpolar(r=[50, 80], theta=[clash['birth_deg'], clash['target_deg']], mode='lines', line=dict(color='red', width=2), hoverinfo='skip'))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(direction="clockwise", rotation=180, tickmode="array", tickvals=tickvals, ticktext=ticktext, showline=False, showgrid=False),
            radialaxis=dict(visible=False, range=[0, 100])
        ),
        showlegend=False, paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=20, b=20, l=20, r=20), height=500
    )
    fig.add_trace(go.Scatterpolar(r=[50, 50], theta=[0, 360], mode='lines', line=dict(color='#E5E7E9', width=1), hoverinfo='skip'))
    fig.add_trace(go.Scatterpolar(r=[80, 80], theta=[0, 360], mode='lines', line=dict(color='#E5E7E9', width=1), hoverinfo='skip'))
    fig.add_trace(go.Scatterpolar(r=[100, 100], theta=[0, 360], mode='lines', line=dict(color='#333333', width=2), hoverinfo='skip'))
    return fig

def draw_empty_luopan(selected_son_idx):
    fig = go.Figure()
    start_angle = selected_son_idx * 15 - 7.5
    end_angle = selected_son_idx * 15 + 7.5
    
    fig.add_trace(go.Scatterpolar(
        r=[0, 180, 180, 0], theta=[start_angle, start_angle, end_angle, end_angle],
        fill='toself', fillcolor='rgba(241, 196, 15, 0.4)',
        line=dict(color='rgba(255,255,255,0)'), showlegend=False, hoverinfo='skip'
    ))

    for i in range(24):
        border_angle = i * 15 + 7.5
        fig.add_trace(go.Scatterpolar(r=[0, 180], theta=[border_angle, border_angle], mode='lines', line=dict(color='#BDC3C7', width=1), hoverinfo='skip'))
        degree_text = f"{border_angle % 360}°"
        if degree_text == "0.0°": degree_text = "0/360°"
        fig.add_trace(go.Scatterpolar(
            r=[195], theta=[border_angle], mode='text',
            text=degree_text, textfont=dict(size=10, color="#7F8C8D"), hoverinfo='skip'
        ))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(direction="clockwise", rotation=-90, tickmode="array", tickvals=[i * 15 for i in range(24)], ticktext=SƠN_24_ZH, showline=False, showgrid=False),
            radialaxis=dict(visible=False, range=[0, 210])
        ),
        showlegend=False, paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=10, b=10, l=10, r=10), height=380
    )
    fig.add_trace(go.Scatterpolar(r=[90, 90], theta=[0, 360], mode='lines', line=dict(color='#7F8C8D', width=1.5), hoverinfo='skip'))
    fig.add_trace(go.Scatterpolar(r=[180, 180], theta=[0, 360], mode='lines', line=dict(color='#333333', width=2), hoverinfo='skip'))
    return fig

# ==========================================
# 4. SIDEBAR & ĐỊA LÝ
# ==========================================
geolocator = Nominatim(user_agent="thien_thoi_app_vn")
tf = TimezoneFinder()

st.sidebar.markdown("### VỊ TRÍ")
saved_locations = load_saved_locations()

# Menu chọn địa điểm đã lưu
if saved_locations:
    loc_names = ["-- Đã lưu --"] + list(saved_locations.keys())
    sel_loc = st.sidebar.selectbox("Tải tọa độ", loc_names, label_visibility="collapsed")
    if sel_loc != "-- Đã lưu --":
        if st.sidebar.button("Áp dụng", use_container_width=True):
            st.session_state.lat = saved_locations[sel_loc]['lat']
            st.session_state.lon = saved_locations[sel_loc]['lon']
            st.session_state.tz_str = saved_locations[sel_loc]['tz']
            st.rerun()

# Tìm kiếm Google Map
address_input = st.sidebar.text_input("Tìm địa chỉ:", placeholder="Enter...")
col_btn1, col_btn2 = st.sidebar.columns([1, 1]) 
if col_btn1.button("Tìm", use_container_width=True, type="primary"):
    try:
        locations = geolocator.geocode(address_input, exactly_one=False, limit=5)
        if locations: st.session_state.search_results = {loc.address: (loc.latitude, loc.longitude) for loc in locations}
        else: st.session_state.search_results = None
    except: pass
if col_btn2.button("Xóa", use_container_width=True):
    st.session_state.search_results = None

if st.session_state.search_results:
    selected_address = st.sidebar.selectbox("Kết quả:", list(st.session_state.search_results.keys()))
    if st.sidebar.button("Lưu & Chốt", use_container_width=True, type="secondary"):
        sel_lat, sel_lon = st.session_state.search_results[selected_address]
        st.session_state.lat = sel_lat
        st.session_state.lon = sel_lon
        auto_tz = tf.timezone_at(lng=sel_lon, lat=sel_lat)
        if auto_tz: st.session_state.tz_str = auto_tz
        
        name_short = selected_address.split(',')[0]
        save_location(name_short, sel_lat, sel_lon, st.session_state.tz_str)
        st.session_state.search_results = None
        st.rerun()

st.sidebar.markdown("---")
# Nhập tay Tọa độ & Tính năng lưu thủ công
lat = st.sidebar.number_input("Vĩ độ", value=st.session_state.lat, format="%.4f")
lon = st.sidebar.number_input("Kinh độ", value=st.session_state.lon, format="%.4f")

with st.sidebar.expander("💾 Lưu tọa độ này"):
    custom_name = st.text_input("Đặt tên địa điểm:")
    if st.button("Lưu vào danh sách", use_container_width=True):
        if custom_name:
            auto_tz = tf.timezone_at(lng=lon, lat=lat)
            if not auto_tz: auto_tz = 'UTC'
            save_location(custom_name, lat, lon, auto_tz)
            st.session_state.lat = lat
            st.session_state.lon = lon
            st.session_state.tz_str = auto_tz
            st.success("Đã lưu!")
            st.rerun()
        else:
            st.error("Vui lòng nhập tên!")

all_timezones = pytz.all_timezones
tz_index = all_timezones.index(st.session_state.tz_str) if st.session_state.tz_str in all_timezones else all_timezones.index('UTC')
selected_tz = st.sidebar.selectbox("Múi giờ", all_timezones, index=tz_index)

st.session_state.lat = lat
st.session_state.lon = lon
st.session_state.tz_str = selected_tz

st.sidebar.markdown("### THỜI GIAN")
st.session_state.target_date = st.sidebar.date_input("Ngày", value=st.session_state.target_date, min_value=datetime.date(1900, 1, 1))
st.session_state.target_time = st.sidebar.time_input("Giờ", value=st.session_state.target_time)

st.sidebar.markdown("### THIÊN THỂ")
col_cb1, col_cb2 = st.sidebar.columns(2)
active_bodies = []
for i, (name, info) in enumerate(CELESTIAL_BODIES.items()):
    is_checked = True if i < 7 else False
    if i % 2 == 0:
        if col_cb1.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)
    else:
        if col_cb2.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)

local_tz = pytz.timezone(st.session_state.tz_str)
dt_target = local_tz.localize(datetime.datetime.combine(st.session_state.target_date, st.session_state.target_time))
df_target = calculate_positions(dt_target, lat, lon, active_bodies)

tab1, tab2, tab3, tab4 = st.tabs(["THỰC ĐỊA", "LÁ SỐ ĐỐI XUNG", "TRẠCH NHẬT QUÉT TỐI ƯU", "TUYẾN KHÍ 24 SƠN"])

# ----------------- TAB 1 -----------------
with tab1:
    st.markdown(f"**THỜI ĐIỂM: {dt_target.strftime('%H:%M %d/%m/%Y')}**")
    col1_1, col1_2, col1_3 = st.columns([1, 2, 1])
    with col1_2:
        fig1 = draw_professional_luopan(df_target)
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': True}) 

# ----------------- TAB 2 -----------------
with tab2:
    if saved_locations:
        sel_loc_b = st.selectbox("Tải nơi sinh đã lưu:", ["-- Tự nhập --"] + list(saved_locations.keys()), label_visibility="collapsed")
        if sel_loc_b != "-- Tự nhập --":
            b_lat_default = saved_locations[sel_loc_b]['lat']
            b_lon_default = saved_locations[sel_loc_b]['lon']
            b_tz_default = saved_locations[sel_loc_b]['tz']
        else:
            b_lat_default, b_lon_default, b_tz_default = 21.0285, 105.8542, 'Asia/Ho_Chi_Minh'
    else:
        b_lat_default, b_lon_default, b_tz_default = 21.0285, 105.8542, 'Asia/Ho_Chi_Minh'
    
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1: birth_date = st.date_input("Ngày sinh", value=datetime.date(1993, 1, 7), min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
    with col_b2: birth_time = st.time_input("Giờ sinh", value=datetime.time(8, 15))
    with col_b3: birth_tz_str = st.selectbox("Múi giờ", all_timezones, index=all_timezones.index(b_tz_default) if b_tz_default in all_timezones else all_timezones.index('Asia/Ho_Chi_Minh'))
        
    col_b4, col_b5 = st.columns(2)
    with col_b4: birth_lat = st.number_input("Vĩ độ sinh", value=b_lat_default, format="%.4f")
    with col_b5: birth_lon = st.number_input("Kinh độ sinh", value=b_lon_default, format="%.4f")
        
    birth_tz = pytz.timezone(birth_tz_str)
    dt_birth = birth_tz.localize(datetime.datetime.combine(birth_date, birth_time))
    
    st.markdown("---")
    df_birth_3 = calculate_positions(dt_birth, birth_lat, birth_lon, ['Thái Dương', 'Thái Âm', 'Mộc Tinh'])
    df_target_3 = calculate_positions(dt_target, lat, lon, ['Thái Dương', 'Thái Âm', 'Mộc Tinh'])
    
    def check_xung(c1, c2): return abs(DI_CHI_ZH.index(c1) - DI_CHI_ZH.index(c2)) == 6

    clash_pairs = []
    for star in ['Mộc Tinh', 'Thái Dương', 'Thái Âm']:
        chi_b = df_birth_3.loc[df_birth_3['Tên'] == star, 'Khu Vực Hoàng Đạo'].values[0]
        chi_t = df_target_3.loc[df_target_3['Tên'] == star, 'Khu Vực Hoàng Đạo'].values[0]
        if check_xung(chi_b, chi_t):
            clash_pairs.append({'name': star, 'birth_deg': df_birth_3.loc[df_birth_3['Tên'] == star, 'Độ Hoàng Đạo'].values[0], 'target_deg': df_target_3.loc[df_target_3['Tên'] == star, 'Độ Hoàng Đạo'].values[0]})

    col2_chart, col2_info = st.columns([1.5, 1])
    with col2_chart:
        st.markdown("**ĐỒ HÌNH HOÀNG ĐẠO**")
        fig2 = draw_ecliptic_chart(df_birth_3, df_target_3, clash_pairs)
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': True})
    
    with col2_info:
        st.markdown("**BÁO CÁO PHÂN TÍCH**")
        jup_b = df_birth_3.loc[df_birth_3['Tên'] == 'Mộc Tinh', 'Khu Vực Hoàng Đạo'].values[0]
        jup_t = df_target_3.loc[df_target_3['Tên'] == 'Mộc Tinh', 'Khu Vực Hoàng Đạo'].values[0]
        if check_xung(jup_b, jup_t): st.markdown(f"> **CẢNH BÁO [NĂM]** Mộc Tinh (Dự kiến: {jup_t} - Sinh: {jup_b})")
        else: st.markdown(f"> **HỢP LỆ [NĂM]** Mộc Tinh")
            
        sun_b = df_birth_3.loc[df_birth_3['Tên'] == 'Thái Dương', 'Khu Vực Hoàng Đạo'].values[0]
        sun_t = df_target_3.loc[df_target_3['Tên'] == 'Thái Dương', 'Khu Vực Hoàng Đạo'].values[0]
        if check_xung(sun_b, sun_t): st.markdown(f"> **CẢNH BÁO [THÁNG]** Thái Dương (Dự kiến: {sun_t} - Sinh: {sun_b})")
        else: st.markdown(f"> **HỢP LỆ [THÁNG]** Thái Dương")
            
        moon_b = df_birth_3.loc[df_birth_3['Tên'] == 'Thái Âm', 'Khu Vực Hoàng Đạo'].values[0]
        moon_t = df_target_3.loc[df_target_3['Tên'] == 'Thái Âm', 'Khu Vực Hoàng Đạo'].values[0]
        if check_xung(moon_b, moon_t): st.markdown(f"> **CẢNH BÁO [NGÀY]** Thái Âm (Dự kiến: {moon_t} - Sinh: {moon_b})")
        else: st.markdown(f"> **HỢP LỆ [NGÀY]** Thái Âm")

# ----------------- TAB 3 -----------------
with tab3:
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        target_son = st.selectbox("Sơn mục tiêu", SƠN_24_ZH)
        son_center_deg = SƠN_24_ZH.index(target_son) * 15
    with col_t2:
        action_type = st.selectbox("Mục đích", ["KÍCH HOẠT (Triều Vượng)", "THÁO DỠ (Triều Suy)"])
    with col_t3:
        if action_type == "KÍCH HOẠT (Triều Vượng)":
            level = st.selectbox("Cấp độ", ["Thái Âm", "Đa Tinh Đáo Sơn", "Sóc/Vọng Nguyệt"])
            scan_days = 30 if level != "Sóc/Vọng Nguyệt" else 180
        else:
            st.markdown("<div style='margin-top: 30px;'>Quét Thượng/Hạ Huyền (90°)</div>", unsafe_allow_html=True)
            scan_days = 60
            
    if st.button("Tìm Kiếm", type="primary"):
        progress = st.progress(0)
        location = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
        results = []
        scan_bodies = active_bodies if len(active_bodies) >= 2 else list(CELESTIAL_BODIES.keys())
        
        def get_t_arr(day_date):
            local_dt = local_tz.localize(datetime.datetime.combine(day_date, datetime.time(0, 0)))
            utc_dt = local_dt.astimezone(pytz.utc)
            return ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute + np.arange(1440))
        
        def get_daily_azimuth(day_date, body_name):
            _, az, _ = location.at(get_t_arr(day_date)).observe(CELESTIAL_BODIES[body_name]['node']).apparent().altaz()
            return az.degrees
            
        def get_daily_ecliptic(day_date, body_name):
            astrometric = earth.at(get_t_arr(day_date)).observe(CELESTIAL_BODIES[body_name]['node'])
            try:
                from skyfield.framelib import ecliptic_J2000
                _, lon_ecl, _ = astrometric.frame_latlon(ecliptic_J2000)
            except:
                _, lon_ecl, _ = astrometric.ecliptic_latlon()
            return lon_ecl.degrees

        if action_type == "THÁO DỠ (Triều Suy)":
            for d in range(scan_days):
                progress.progress(d / scan_days)
                check_day = (datetime.datetime.combine(st.session_state.target_date, datetime.time(0,0)) + datetime.timedelta(days=d)).date()
                sun_ecl_arr = get_daily_ecliptic(check_day, 'Thái Dương')
                moon_ecl_arr = get_daily_ecliptic(check_day, 'Thái Âm')
                diff_arr = get_angular_diff_vec(sun_ecl_arr, moon_ecl_arr)
                
                if np.any((diff_arr >= 80) & (diff_arr <= 100)): 
                    sun_az_arr = get_daily_azimuth(check_day, 'Thái Dương')
                    moon_az_arr = get_daily_azimuth(check_day, 'Thái Âm')
                    best_min = np.argmin(np.abs(diff_arr - 90)) 
                    if np.abs(diff_arr[best_min] - 90) > 5: best_min = np.argmin(np.abs(diff_arr - 270))
                    
                    sun_s, moon_s = get_24_son(sun_az_arr[best_min]), get_24_son(moon_az_arr[best_min])
                    if sun_s != target_son and moon_s != target_son:
                        exact_time = local_tz.localize(datetime.datetime.combine(check_day, datetime.time(best_min // 60, best_min % 60)))
                        results.append({"Ngày": exact_time.strftime("%d/%m/%Y"), "Giờ": exact_time.strftime("%H:%M"), "Hiện Tượng": "Nhật Nguyệt 90°", "Ghi Chú": f"Nhật: {sun_s}, Nguyệt: {moon_s}", "Raw_Time": exact_time})
        else:
            for d in range(scan_days):
                progress.progress(d / scan_days)
                check_day = (datetime.datetime.combine(st.session_state.target_date, datetime.time(0,0)) + datetime.timedelta(days=d)).date()
                
                is_soc_vong = False
                if level == "Sóc/Vọng Nguyệt":
                    sun_ecl_noon = get_daily_ecliptic(check_day, 'Thái Dương')[720]
                    moon_ecl_noon = get_daily_ecliptic(check_day, 'Thái Âm')[720]
                    phase_diff = get_angular_diff_vec(sun_ecl_noon, moon_ecl_noon)
                    if phase_diff < 15 or phase_diff > 165: is_soc_vong = True
                    if not is_soc_vong: continue 
                
                moon_az_arr = get_daily_azimuth(check_day, 'Thái Âm')
                start_deg, end_deg = son_center_deg - 7.5, son_center_deg + 7.5
                if start_deg < 0: in_son_mask = (moon_az_arr >= 360 + start_deg) | (moon_az_arr < end_deg)
                else: in_son_mask = (moon_az_arr >= start_deg) & (moon_az_arr < end_deg)
                    
                valid_mins = np.where(in_son_mask)[0]
                if len(valid_mins) > 0:
                    best_events_today = []
                    if level == "Thái Âm":
                        diffs = get_angular_diff_vec(moon_az_arr[valid_mins], son_center_deg)
                        best_local_idx = np.argmin(diffs)
                        best_min = valid_mins[best_local_idx]
                        exact_time = local_tz.localize(datetime.datetime.combine(check_day, datetime.time(best_min // 60, best_min % 60)))
                        best_events_today.append((diffs[best_local_idx], exact_time, "Thái Âm chính trung", "-"))
                        
                    elif level == "Đa Tinh Đáo Sơn":
                        other_bodies_az = {ob: get_daily_azimuth(check_day, ob) for ob in scan_bodies if ob != 'Thái Âm'}
                        for m in valid_mins:
                            moon_az = moon_az_arr[m]
                            bodies_in_son = [ob for ob, az_arr in other_bodies_az.items() if (start_deg < 0 and (az_arr[m] >= 360 + start_deg or az_arr[m] < end_deg)) or (start_deg >= 0 and start_deg <= az_arr[m] < end_deg)]
                            if len(bodies_in_son) >= 1:
                                exact_time = local_tz.localize(datetime.datetime.combine(check_day, datetime.time(m // 60, m % 60)))
                                if len(bodies_in_son) >= 2:
                                    sum_diff = sum([get_angular_diff_vec(moon_az, other_bodies_az[b][m]) for b in bodies_in_son])
                                    best_events_today.append((sum_diff, exact_time, "Trọng tâm Đa tinh", ", ".join(bodies_in_son)))
                                for b in bodies_in_son:
                                    diff_pair = get_angular_diff_vec(moon_az, other_bodies_az[b][m])
                                    best_events_today.append((diff_pair, exact_time, f"Thái Âm khớp {b}", ", ".join(bodies_in_son)))

                    elif level == "Sóc/Vọng Nguyệt" and is_soc_vong:
                        sun_az_arr = get_daily_azimuth(check_day, 'Thái Dương')
                        for m in valid_mins:
                            moon_az = moon_az_arr[m]
                            sun_az = sun_az_arr[m]
                            sun_s = get_24_son(sun_az)
                            exact_time = local_tz.localize(datetime.datetime.combine(check_day, datetime.time(m // 60, m % 60)))
                            
                            others = []
                            t_m = ts.utc(exact_time.astimezone(pytz.utc))
                            for ob in scan_bodies:
                                if ob not in ['Thái Âm', 'Thái Dương']:
                                    _, ob_az, _ = location.at(t_m).observe(CELESTIAL_BODIES[ob]['node']).apparent().altaz()
                                    if get_24_son(ob_az.degrees) == target_son: others.append(ob)
                            
                            if sun_s == target_son:
                                diff = get_angular_diff_vec(moon_az, sun_az)
                                best_events_today.append((diff, exact_time, "Sóc Nguyệt", ", ".join(others) if others else "-"))
                            elif abs(SƠN_24_ZH.index(sun_s) - SƠN_24_ZH.index(target_son)) == 12:
                                diff = abs(180 - get_angular_diff_vec(moon_az, sun_az))
                                best_events_today.append((diff, exact_time, "Vọng Nguyệt", ", ".join(others) if others else "-"))

                    if best_events_today:
                        df_events = pd.DataFrame(best_events_today, columns=['Diff', 'Time', 'Type', 'Others'])
                        for idx in df_events.groupby('Type')['Diff'].idxmin():
                            row = df_events.loc[idx]
                            results.append({"Ngày": row['Time'].strftime("%d/%m/%Y"), "Giờ": row['Time'].strftime("%H:%M"), "Hiện Tượng": row['Type'], "Sai số": f"{round(row['Diff'], 2)}°", "Thiên thể khác": row['Others'], "Raw_Time": row['Time']})

        progress.progress(100)
        st.session_state.scan_results = results if results else []
            
    st.markdown("---")
    if st.session_state.scan_results is not None:
        if len(st.session_state.scan_results) > 0:
            res_list = st.session_state.scan_results
            st.markdown(f"**TÌM THẤY {len(res_list)} THỜI ĐIỂM:**")
            st.dataframe(pd.DataFrame(res_list).drop(columns=['Raw_Time']), use_container_width=True)
            
            options = {f"{r['Ngày']} {r['Giờ']} - {r['Hiện Tượng']}": r['Raw_Time'] for r in res_list}
            selected_option = st.selectbox("Chọn mốc thời gian xem đồ hình & Đồng bộ:", list(options.keys()))
            
            if st.button("Vẽ Đồ Hình & Đồng Bộ", type="primary"):
                selected_time = options[selected_option]
                st.session_state.target_date = selected_time.date()
                st.session_state.target_time = selected_time.time()
                st.session_state.preview_time = selected_time
                st.rerun() 
                
            if 'preview_time' in st.session_state and st.session_state.preview_time is not None:
                st.markdown(f"**ĐỒ HÌNH TẠI: {st.session_state.preview_time.strftime('%H:%M %d/%m/%Y')}**")
                df_preview = calculate_positions(st.session_state.preview_time, lat, lon, active_bodies)
                col_p1, col_p2, col_p3 = st.columns([1,1.5,1])
                with col_p2:
                    fig_preview = draw_professional_luopan(df_preview)
                    st.plotly_chart(fig_preview, use_container_width=True, config={'displayModeBar': False}, key=f"preview_{st.session_state.preview_time.timestamp()}")
        else:
            st.markdown("> **Không tìm thấy thời điểm phù hợp.**")

# ----------------- TAB 4 -----------------
with tab4:
    warnings_list = load_google_sheets()
    col_4a, col_4b = st.columns([1, 1.2])
    
    with col_4b:
        selected_son_tab4 = st.selectbox("Chọn Sơn Hướng:", SƠN_24_ZH)
        sel_idx = SƠN_24_ZH.index(selected_son_tab4)
        viet_name = CHAR_TO_VIET.get(selected_son_tab4, "")
        
        st.markdown("**Thông Tin**")
        st.markdown("---")
        
        if warnings_list:
            grouped_data = {}
            for w in warnings_list:
                if viet_name in w['triggers']:
                    cat = w['category'].upper()
                    if cat not in grouped_data: grouped_data[cat] = []
                    grouped_data[cat].append(w)
            
            if grouped_data:
                html_output = ""
                for cat, items in grouped_data.items():
                    html_output += f"<div style='margin-bottom: 20px;'><div style='font-weight: bold; font-size: 16px; color: #2C3E50; border-bottom: 1px solid #333; padding-bottom: 4px; margin-bottom: 12px; display: inline-block;'>{cat}</div>"
                    for item in items:
                        desc_html = f"<div style='color: #444; font-size: 14.5px; margin-top: 3px; line-height: 1.5;'>{item['desc']}</div>" if item['desc'] else ""
                        html_output += f"<div style='margin-bottom: 15px;'><span style='font-weight: bold; font-size: 15px; color: #000;'>{item['name']}</span> <span style='font-style: italic; color: #7F8C8D; font-size: 14px;'>{item['triggers']}</span>{desc_html}</div>"
                    html_output += "</div>"
                st.markdown(html_output, unsafe_allow_html=True)
            else:
                st.info("Không có ghi chú tuyến khí.")
        else:
            st.warning("Đang tải dữ liệu từ Google Sheets.")
            
    with col_4a:
        st.markdown("<br>", unsafe_allow_html=True)
        fig4 = draw_empty_luopan(sel_idx)
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})
