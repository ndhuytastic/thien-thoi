import streamlit as st
import datetime
import pytz
import pandas as pd
import plotly.graph_objects as go
import numpy as np

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

# Khởi tạo Session State để kết nối Tab 3 (Kết quả quét) với Tab 1 (La bàn)
local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.datetime.now(local_tz)
if 'target_date' not in st.session_state: st.session_state.target_date = now.date()
if 'target_time' not in st.session_state: st.session_state.target_time = now.time()

# ==========================================
# 1. DỮ LIỆU & CACHE
# ==========================================
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

DI_CHI_ZH = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SƠN_24_ZH = ["子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳", "丙", 
             "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥", "壬"]

def get_di_chi(degree): return DI_CHI_ZH[int(((degree + 15) % 360) / 30)]
def get_24_son(azimuth): return SƠN_24_ZH[int(((azimuth + 7.5) % 360) / 15)]
def get_angular_diff_vec(a1, a2): 
    diff = np.abs(a1 - a2)
    return np.minimum(diff, 360 - diff)

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
            "Hoàng Đạo (°)": round(lon_ecl.degrees, 4), "Chi": get_di_chi(lon_ecl.degrees),
            "Azimuth (°)": round(az.degrees, 4), "Altitude (°)": round(alt.degrees, 4),
            "Sơn": get_24_son(az.degrees)
        })
    return pd.DataFrame(results)

# ==========================================
# 3. HÀM VẼ LA BÀN
# ==========================================
def draw_professional_luopan(df):
    fig = go.Figure()
    df['r_plot'] = 90 - df['Altitude (°)']

    for idx, row in df.iterrows():
        marker_size = 14 if row['Tên'] in ['Thái Dương', 'Thái Âm'] else 10
        text_weight = "bold" if row['Tên'] in ['Thái Dương', 'Thái Âm'] else "normal"
        
        fig.add_trace(go.Scatterpolar(
            r=[row['r_plot']], theta=[row['Azimuth (°)']], mode='markers+text',
            marker=dict(size=marker_size, color=row['Màu'], symbol='circle', line=dict(width=1, color='white')),
            text=f"<b>{row['Ký Hiệu']}</b>" if text_weight == "bold" else row['Ký Hiệu'],
            textposition="bottom center", textfont=dict(size=14, color="#000000", family="Arial"),
            name=row['Tên'], hoverinfo="text",
            hovertext=f"{row['Tên']}<br>Azimuth: {row['Azimuth (°)']}° (Sơn {row['Sơn']})<br>Altitude: {row['Altitude (°)']}°"
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

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.markdown("### THÔNG SỐ")
lat = st.sidebar.number_input("Vĩ độ (Latitude)", value=21.0285, format="%.4f")
lon = st.sidebar.number_input("Kinh độ (Longitude)", value=105.8542, format="%.4f")

# Đọc từ Session State
st.session_state.target_date = st.sidebar.date_input("Ngày", value=st.session_state.target_date, min_value=datetime.date(1900, 1, 1))
st.session_state.target_time = st.sidebar.time_input("Giờ", value=st.session_state.target_time)

st.sidebar.markdown("**Hiển thị Thiên thể**")
col_cb1, col_cb2 = st.sidebar.columns(2)
active_bodies = []

for i, (name, info) in enumerate(CELESTIAL_BODIES.items()):
    is_checked = True if i < 7 else False
    if i % 2 == 0:
        if col_cb1.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)
    else:
        if col_cb2.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)

dt_target = local_tz.localize(datetime.datetime.combine(st.session_state.target_date, st.session_state.target_time))
df_target = calculate_positions(dt_target, lat, lon, active_bodies)

tab1, tab2, tab3 = st.tabs(["I. THIÊN THỂ ĐÁO SƠN", "II. LÁ SỐ ĐỐI XUNG", "III. TRẠCH NHẬT KÍCH HOẠT / THÁO DỠ"])

# ----------------- TAB 1 -----------------
with tab1:
    col1_1, col1_2, col1_3 = st.columns([1, 2, 1])
    with col1_2:
        st.markdown(f"**ĐỒ HÌNH THIÊN THỂ** | *{dt_target.strftime('%d/%m/%Y %H:%M')}*")
        fig = draw_professional_luopan(df_target)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True}) # Bật thanh công cụ để có nút Fullscreen

# ----------------- TAB 2 -----------------
with tab2:
    st.markdown("### ĐỐI CHIẾU LÁ SỐ & THỜI ĐIỂM DỰ KIẾN")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        birth_date = st.date_input("Ngày sinh", value=datetime.date(1993, 1, 7), min_value=datetime.date(1900, 1, 1))
    with col_b2:
        birth_time = st.time_input("Giờ sinh", value=datetime.time(8, 15))
        
    dt_birth = local_tz.localize(datetime.datetime.combine(birth_date, birth_time))
    
    if st.button("Kiểm Tra", type="primary"):
        df_birth = calculate_positions(dt_birth, lat, lon, list(CELESTIAL_BODIES.keys()))
        df_target_full = calculate_positions(dt_target, lat, lon, list(CELESTIAL_BODIES.keys()))
        def check_xung(c1, c2): return abs(DI_CHI_ZH.index(c1) - DI_CHI_ZH.index(c2)) == 6
            
        jup_b = df_birth.loc[df_birth['Tên'] == 'Mộc Tinh', 'Chi'].values[0]
        jup_t = df_target_full.loc[df_target_full['Tên'] == 'Mộc Tinh', 'Chi'].values[0]
        sun_b = df_birth.loc[df_birth['Tên'] == 'Thái Dương', 'Chi'].values[0]
        sun_t = df_target_full.loc[df_target_full['Tên'] == 'Thái Dương', 'Chi'].values[0]
        moon_b = df_birth.loc[df_birth['Tên'] == 'Thái Âm', 'Chi'].values[0]
        moon_t = df_target_full.loc[df_target_full['Tên'] == 'Thái Âm', 'Chi'].values[0]
        
        st.markdown("---")
        has_error = False
        if check_xung(jup_b, jup_t): 
            st.markdown(f"> **[CẢNH BÁO - NĂM]** Mộc Tinh dự kiến (Khu {jup_t}) TRỰC XUNG với Mộc Tinh bản mệnh (Khu {jup_b}).")
            has_error = True
        else: st.markdown(f"> **[HỢP LỆ - NĂM]** Mộc Tinh ({jup_t} / {jup_b})")
            
        if check_xung(sun_b, sun_t): 
            st.markdown(f"> **[CẢNH BÁO - THÁNG]** Thái Dương dự kiến (Khu {sun_t}) TRỰC XUNG với Thái Dương bản mệnh (Khu {sun_b}).")
            has_error = True
        else: st.markdown(f"> **[HỢP LỆ - THÁNG]** Thái Dương ({sun_t} / {sun_b})")
            
        if check_xung(moon_b, moon_t): 
            st.markdown(f"> **[CẢNH BÁO - NGÀY]** Thái Âm dự kiến (Khu {moon_t}) TRỰC XUNG với Thái Âm bản mệnh (Khu {moon_b}).")
            has_error = True
        else: st.markdown(f"> **[HỢP LỆ - NGÀY]** Thái Âm ({moon_t} / {moon_b})")
            
        if not has_error: st.markdown("<br>**KẾT LUẬN:** Thời điểm dự kiến hòa hợp với lá số cá nhân, không xuất hiện hiện tượng đối xung.", unsafe_allow_html=True)

# ----------------- TAB 3 (THUẬT TOÁN VECTOR HÓA SIÊU TỐC) -----------------
with tab3:
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        target_son = st.selectbox("1. Chọn Sơn mục tiêu", SƠN_24_ZH)
        son_idx = SƠN_24_ZH.index(target_son)
        son_center_deg = son_idx * 15
    with col_t2:
        action_type = st.selectbox("2. Mục đích", ["KÍCH HOẠT (Lực Triều Vượng)", "THÁO DỠ (Lực Triều Suy)"])
    with col_t3:
        if action_type == "KÍCH HOẠT (Lực Triều Vượng)":
            level = st.selectbox("3. Cấp độ", ["Thái Âm", "Đa Tinh Đáo Sơn", "Sóc/Vọng Nguyệt"])
            scan_days = 30 if level != "Cao cấp (Sóc/Vọng Nguyệt)" else 180
        else:
            st.info("Chỉ quét ngày Thượng/Hạ Huyền (Nhật Nguyệt 90°)")
            scan_days = 60
            
    if st.button("Tìm Kiếms", type="primary"):
        progress = st.progress(0)
        location = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
        results = []
        scan_bodies = active_bodies if len(active_bodies) >= 2 else list(CELESTIAL_BODIES.keys())
        
        # Hàm hỗ trợ Vectorized: Lấy Azimuth 1440 phút của 1 sao
        def get_daily_azimuth(day_date, body_name):
            t_arr = ts.utc(day_date.year, day_date.month, day_date.day, 0, np.arange(1440))
            _, az, _ = location.at(t_arr).observe(CELESTIAL_BODIES[body_name]['node']).apparent().altaz()
            return az.degrees
            
        # Hàm hỗ trợ Vectorized: Lấy Hoàng Đạo 1440 phút
        def get_daily_ecliptic(day_date, body_name):
            t_arr = ts.utc(day_date.year, day_date.month, day_date.day, 0, np.arange(1440))
            astrometric = earth.at(t_arr).observe(CELESTIAL_BODIES[body_name]['node'])
            try:
                from skyfield.framelib import ecliptic_J2000
                _, lon_ecl, _ = astrometric.frame_latlon(ecliptic_J2000)
            except:
                _, lon_ecl, _ = astrometric.ecliptic_latlon()
            return lon_ecl.degrees

        # ==================================
        # LOGIC THÁO DỠ (VECTOR HÓA)
        # ==================================
        if action_type == "THÁO DỠ (Lực Triều Suy)":
            for d in range(scan_days):
                progress.progress(d / scan_days)
                check_day = (dt_target + datetime.timedelta(days=d)).date()
                
                # Quét nhanh giữa trưa xem Pha Mặt Trăng có gần 90 độ không
                t_noon = ts.utc(check_day.year, check_day.month, check_day.day, 12, 0)
                sun_ecl = earth.at(t_noon).observe(CELESTIAL_BODIES['Thái Dương']['node']).ecliptic_latlon()[1].degrees
                moon_ecl = earth.at(t_noon).observe(CELESTIAL_BODIES['Thái Âm']['node']).ecliptic_latlon()[1].degrees
                phase_diff = get_angular_diff_vec(sun_ecl, moon_ecl)
                
                if 80 <= phase_diff <= 100: # Lọt vào ngày Thượng/Hạ Huyền
                    sun_az_arr = get_daily_azimuth(check_day, 'Thái Dương')
                    moon_az_arr = get_daily_azimuth(check_day, 'Thái Âm')
                    sun_ecl_arr = get_daily_ecliptic(check_day, 'Thái Dương')
                    moon_ecl_arr = get_daily_ecliptic(check_day, 'Thái Âm')
                    
                    diff_arr = get_angular_diff_vec(sun_ecl_arr, moon_ecl_arr)
                    # Tìm phút vuông góc 90 độ chuẩn nhất
                    best_min = np.argmin(np.abs(diff_arr - 90)) 
                    # Nếu 90 độ xa quá thì thử 270 độ
                    if np.abs(diff_arr[best_min] - 90) > 5:
                        best_min = np.argmin(np.abs(diff_arr - 270))
                    
                    # Kiểm tra An toàn: Nhật Nguyệt có nằm trong Sơn mục tiêu không?
                    sun_az = sun_az_arr[best_min]
                    moon_az = moon_az_arr[best_min]
                    sun_s = get_24_son(sun_az)
                    moon_s = get_24_son(moon_az)
                    
                    if sun_s != target_son and moon_s != target_son:
                        exact_time = datetime.datetime.combine(check_day, datetime.time(best_min // 60, best_min % 60))
                        results.append({
                            "Ngày": exact_time.strftime("%d/%m/%Y"),
                            "Giờ Cực Đỉnh": exact_time.strftime("%H:%M"),
                            "Hiện Tượng": "Nhật Nguyệt 90° (Thượng/Hạ Huyền)",
                            "Ghi Chú": f"An toàn. Thái Dương: {sun_s}, Thái Âm: {moon_s}",
                            "Các sao khác tại Sơn": "-",
                            "Raw_Time": exact_time
                        })
                        
        # ==================================
        # LOGIC KÍCH HOẠT (VECTOR HÓA)
        # ==================================
        else:
            for d in range(scan_days):
                progress.progress(d / scan_days)
                check_day = (dt_target + datetime.timedelta(days=d)).date()
                
                # Check nhanh Pha Sóc Vọng nếu là Cấp Cao
                is_soc_vong = False
                if level == "Sóc/Vọng Nguyệt":
                    t_noon = ts.utc(check_day.year, check_day.month, check_day.day, 12, 0)
                    sun_ecl = earth.at(t_noon).observe(CELESTIAL_BODIES['Thái Dương']['node']).ecliptic_latlon()[1].degrees
                    moon_ecl = earth.at(t_noon).observe(CELESTIAL_BODIES['Thái Âm']['node']).ecliptic_latlon()[1].degrees
                    phase_diff = get_angular_diff_vec(sun_ecl, moon_ecl)
                    if phase_diff < 15 or phase_diff > 165: is_soc_vong = True
                    if not is_soc_vong: continue # Bỏ qua ngày nếu không phải Sóc Vọng
                
                # Lấy Azimuth Thái Âm cả ngày
                moon_az_arr = get_daily_azimuth(check_day, 'Thái Âm')
                
                # Xác định các phút Mặt Trăng nằm trong Sơn mục tiêu
                start_deg = son_center_deg - 7.5
                end_deg = son_center_deg + 7.5
                if start_deg < 0:
                    in_son_mask = (moon_az_arr >= 360 + start_deg) | (moon_az_arr < end_deg)
                else:
                    in_son_mask = (moon_az_arr >= start_deg) & (moon_az_arr < end_deg)
                    
                valid_mins = np.where(in_son_mask)[0]
                
                if len(valid_mins) > 0:
                    best_events_today = []
                    
                    if level == "Thái Âm":
                        # Tìm phút góc Trăng gần tâm Sơn nhất
                        diffs = get_angular_diff_vec(moon_az_arr[valid_mins], son_center_deg)
                        best_local_idx = np.argmin(diffs)
                        best_min = valid_mins[best_local_idx]
                        exact_time = datetime.datetime.combine(check_day, datetime.time(best_min // 60, best_min % 60))
                        best_events_today.append((diffs[best_local_idx], exact_time, "Thái Âm chính trung Sơn", "-"))
                        
                    elif level == "Đa Tinh Đáo Sơn":
                        # Lấy data các sao khác trong ngày
                        other_bodies_az = {}
                        for ob in scan_bodies:
                            if ob != 'Thái Âm':
                                other_bodies_az[ob] = get_daily_azimuth(check_day, ob)
                                
                        # Chỉ duyệt các phút Trăng ở trong Sơn
                        for m in valid_mins:
                            moon_az = moon_az_arr[m]
                            bodies_in_son = []
                            for ob, az_arr in other_bodies_az.items():
                                ob_az = az_arr[m]
                                if (start_deg < 0 and (ob_az >= 360 + start_deg or ob_az < end_deg)) or (start_deg >= 0 and start_deg <= ob_az < end_deg):
                                    bodies_in_son.append(ob)
                                    
                            if len(bodies_in_son) >= 1:
                                exact_time = datetime.datetime.combine(check_day, datetime.time(m // 60, m % 60))
                                # Tính sai số Trọng tâm (Sum khoảng cách từ Trăng đến các sao)
                                sum_diff = sum([get_angular_diff_vec(moon_az, other_bodies_az[b][m]) for b in bodies_in_son])
                                best_events_today.append((sum_diff, exact_time, "Trọng tâm Đa tinh", ", ".join(bodies_in_son)))
                                
                                # Tính sai số Trùng khớp từng cặp
                                for b in bodies_in_son:
                                    diff_pair = get_angular_diff_vec(moon_az, other_bodies_az[b][m])
                                    best_events_today.append((diff_pair, exact_time, f"Thái Âm trùng khít {b}", ", ".join(bodies_in_son)))

                    elif level == "Sóc/Vọng Nguyệt" and is_soc_vong:
                        sun_az_arr = get_daily_azimuth(check_day, 'Thái Dương')
                        # Duyệt các phút Trăng ở trong Sơn
                        for m in valid_mins:
                            moon_az = moon_az_arr[m]
                            sun_az = sun_az_arr[m]
                            sun_s = get_24_son(sun_az)
                            
                            exact_time = datetime.datetime.combine(check_day, datetime.time(m // 60, m % 60))
                            
                            # Tìm các sao khác tình cờ có mặt tại Sơn lúc này (để in ra báo cáo)
                            others = []
                            for ob in scan_bodies:
                                if ob not in ['Thái Âm', 'Thái Dương']:
                                    # Get az of ob at minute m. Since we didn't calculate full array to save memory, do it pointwise:
                                    t_m = ts.utc(exact_time.year, exact_time.month, exact_time.day, exact_time.hour, exact_time.minute)
                                    _, ob_az, _ = location.at(t_m).observe(CELESTIAL_BODIES[ob]['node']).apparent().altaz()
                                    if get_24_son(ob_az.degrees) == target_son:
                                        others.append(ob)
                            
                            # Nếu Sóc Nguyệt (Nhật Nguyệt cùng Sơn)
                            if sun_s == target_son:
                                diff = get_angular_diff_vec(moon_az, sun_az)
                                best_events_today.append((diff, exact_time, "Sóc Nguyệt: Nhật Nguyệt đồng cung", ", ".join(others) if others else "-"))
                            
                            # Nếu Vọng Nguyệt (Nhật đối diện)
                            elif abs(SƠN_24_ZH.index(sun_s) - SƠN_24_ZH.index(target_son)) == 12:
                                diff = abs(180 - get_angular_diff_vec(moon_az, sun_az))
                                best_events_today.append((diff, exact_time, "Vọng Nguyệt: Nhật Nguyệt đối đỉnh", ", ".join(others) if others else "-"))

                    # Lọc Đỉnh của ngày (Chỉ lấy kết quả có sai số góc bé nhất)
                    if best_events_today:
                        df_events = pd.DataFrame(best_events_today, columns=['Diff', 'Time', 'Type', 'Others'])
                        best_idx = df_events.groupby('Type')['Diff'].idxmin()
                        for idx in best_idx:
                            row = df_events.loc[idx]
                            results.append({
                                "Ngày": row['Time'].strftime("%d/%m/%Y"),
                                "Giờ Cực Đỉnh": row['Time'].strftime("%H:%M"),
                                "Hiện Tượng": row['Type'],
                                "Ghi Chú": f"Sai số độ lệch thấp nhất: {round(row['Diff'], 2)}°",
                                "Các sao khác tại Sơn": row['Others'],
                                "Raw_Time": row['Time']
                            })

        progress.progress(100)
        st.markdown("---")
        if results:
            st.markdown(f"**ĐÃ TÌM ĐỈNH THÀNH CÔNG:** Có {len(results)} thời điểm tối ưu.")
            df_res = pd.DataFrame(results)
            st.dataframe(df_res.drop(columns=['Raw_Time']), use_container_width=True)
            
            # TÍNH NĂNG CHỌN ĐỂ XEM ĐỒ HÌNH
            st.markdown("XEM TRỰC TIẾP TRÊN LA BÀN")
            options = {f"{r['Ngày']} - {r['Giờ Cực Đỉnh']} ({r['Hiện Tượng']})": r['Raw_Time'] for r in results}
            selected_option = st.selectbox("Chọn một kết quả để cập nhật La Bàn ở TAB 1:", list(options.keys()))
            
            if st.button("Áp dụng lên La Bàn", type="primary"):
                selected_time = options[selected_option]
                st.session_state.target_date = selected_time.date()
                st.session_state.target_time = selected_time.time()
                st.rerun() # Refresh app để vẽ lại biểu đồ
        else:
            st.markdown("> **[THÔNG BÁO]** Không tìm thấy thời điểm nào thỏa mãn điều kiện khó này trong khung thời gian quét. Vui lòng hạ cấp độ kích hoạt hoặc mở rộng ngày dự kiến.")
