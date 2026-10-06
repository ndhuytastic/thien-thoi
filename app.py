import streamlit as st
import datetime
import pytz
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# CẤU HÌNH TRANG CHUYÊN NGHIỆP
# ==========================================
st.set_page_config(page_title="Thiên Thời Sách - Phân Tích Tinh Tượng", layout="wide", initial_sidebar_state="expanded")

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
    st.error("HỆ THỐNG YÊU CẦU KHỞI ĐỘNG LẠI MÁY CHỦ (REBOOT)")
    st.stop()

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
            "Tên": name,
            "Ký Hiệu": info['char'],
            "Màu": info['color'],
            "Hoàng Đạo (°)": round(lon_ecl.degrees, 2),
            "Chi": get_di_chi(lon_ecl.degrees),
            "Azimuth (°)": round(az.degrees, 2),
            "Altitude (°)": round(alt.degrees, 2),
            "Sơn": get_24_son(az.degrees)
        })
    return pd.DataFrame(results)

# ==========================================
# 3. HÀM VẼ LA BÀN (NAM Ở TRÊN)
# ==========================================
def draw_professional_luopan(df):
    fig = go.Figure()
    df['r_plot'] = 90 - df['Altitude (°)']

    for idx, row in df.iterrows():
        marker_size = 14 if row['Tên'] in ['Thái Dương', 'Thái Âm'] else 10
        text_weight = "bold" if row['Tên'] in ['Thái Dương', 'Thái Âm'] else "normal"
        
        fig.add_trace(go.Scatterpolar(
            r=[row['r_plot']],
            theta=[row['Azimuth (°)']],
            mode='markers+text',
            marker=dict(size=marker_size, color=row['Màu'], symbol='circle', line=dict(width=1, color='white')),
            text=f"<b>{row['Ký Hiệu']}</b>" if text_weight == "bold" else row['Ký Hiệu'],
            textposition="bottom center",
            textfont=dict(size=14, color="#000000", family="Arial"),
            name=row['Tên'],
            hoverinfo="text",
            hovertext=f"{row['Tên']}<br>Azimuth: {row['Azimuth (°)']}° (Sơn {row['Sơn']})<br>Altitude: {row['Altitude (°)']}°"
        ))

    for i in range(24):
        border_angle = i * 15 + 7.5
        fig.add_trace(go.Scatterpolar(
            r=[0, 180], theta=[border_angle, border_angle], mode='lines', line=dict(color='#BDC3C7', width=1), hoverinfo='skip'
        ))

    # Cấu hình mặt la bàn: rotation=-90 để Nam (180 độ) lên trên cùng
    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                direction="clockwise", rotation=-90,
                tickmode="array", tickvals=[i * 15 for i in range(24)], ticktext=SƠN_24_ZH,
                showline=False, showgrid=False
            ),
            radialaxis=dict(visible=False, range=[0, 180])
        ),
        showlegend=False, paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=30, l=30, r=30), height=700
    )
    
    fig.add_trace(go.Scatterpolar(r=[90, 90], theta=[0, 360], mode='lines', line=dict(color='#7F8C8D', width=1.5), hoverinfo='skip'))
    fig.add_trace(go.Scatterpolar(r=[180, 180], theta=[0, 360], mode='lines', line=dict(color='#333333', width=2), hoverinfo='skip'))

    return fig

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.markdown("### CÀI ĐẶT THÔNG SỐ")
lat = st.sidebar.number_input("Vĩ độ (Lat)", value=21.0285, format="%.4f")
lon = st.sidebar.number_input("Kinh độ (Lon)", value=105.8542, format="%.4f")

target_date = st.sidebar.date_input("Ngày (Dương lịch)", value=datetime.date.today(), min_value=datetime.date(1900, 1, 1))
target_time = st.sidebar.time_input("Giờ địa phương", value=datetime.datetime.now().time())

st.sidebar.markdown("**Hiển thị Thiên thể**")
col_cb1, col_cb2 = st.sidebar.columns(2)
active_bodies = []

for i, (name, info) in enumerate(CELESTIAL_BODIES.items()):
    is_checked = True if i < 7 else False
    if i % 2 == 0:
        if col_cb1.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)
    else:
        if col_cb2.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)

local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
dt_target = local_tz.localize(datetime.datetime.combine(target_date, target_time))

df_target = calculate_positions(dt_target, lat, lon, active_bodies)

st.markdown("<h2 style='text-align: center; color: #2C3E50; margin-bottom: 30px;'>HỆ THỐNG PHÂN TÍCH TINH TƯỢNG TRẠCH NHẬT</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["I. THIÊN THỂ ĐÁO SƠN", "II. ĐỐI XUNG CÁ NHÂN", "III. TRẠCH NHẬT KÍCH HOẠT SƠN HƯỚNG"])

# ----------------- TAB 1 -----------------
with tab1:
    st.markdown(f"**ĐỒ HÌNH BẦU TRỜI TẠI THỰC ĐỊA** | *{dt_target.strftime('%d/%m/%Y %H:%M')}*")
    fig = draw_professional_luopan(df_target)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ----------------- TAB 2 -----------------
with tab2:
    st.markdown("### ĐỐI CHIẾU LÁ SỐ BẨM SINH & THỜI ĐIỂM DỰ KIẾN")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        birth_date = st.date_input("Ngày sinh (Dương lịch)", value=datetime.date(1990, 1, 1), min_value=datetime.date(1900, 1, 1))
    with col_b2:
        birth_time = st.time_input("Giờ sinh", value=datetime.time(12, 0))
        
    dt_birth = local_tz.localize(datetime.datetime.combine(birth_date, birth_time))
    
    if st.button("Thực Thi Kiểm Tra", type="primary"):
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
        st.markdown("#### BÁO CÁO PHÂN TÍCH")
        has_error = False
        
        if check_xung(jup_b, jup_t): 
            st.markdown(f"> **[CẢNH BÁO - NĂM]** Mộc Tinh dự kiến (Khu {jup_t}) TRỰC XUNG với Mộc Tinh bản mệnh (Khu {jup_b}).")
            has_error = True
        else:
            st.markdown(f"> **[HỢP LỆ - NĂM]** Mộc Tinh ({jup_t} / {jup_b})")
            
        if check_xung(sun_b, sun_t): 
            st.markdown(f"> **[CẢNH BÁO - THÁNG]** Thái Dương dự kiến (Khu {sun_t}) TRỰC XUNG với Thái Dương bản mệnh (Khu {sun_b}).")
            has_error = True
        else:
            st.markdown(f"> **[HỢP LỆ - THÁNG]** Thái Dương ({sun_t} / {sun_b})")
            
        if check_xung(moon_b, moon_t): 
            st.markdown(f"> **[CẢNH BÁO - NGÀY]** Thái Âm dự kiến (Khu {moon_t}) TRỰC XUNG với Thái Âm bản mệnh (Khu {moon_b}).")
            has_error = True
        else:
            st.markdown(f"> **[HỢP LỆ - NGÀY]** Thái Âm ({moon_t} / {moon_b})")

# ----------------- TAB 3 -----------------
with tab3:
    st.markdown("### TRẠCH NHẬT THEO CẤP ĐỘ KÍCH HOẠT (QUÉT ĐẾN TỪNG PHÚT)")
    st.markdown("Xác định thời điểm tối ưu để kích hoạt Cát khí (Hội tụ) hoặc Tháo dỡ Hung khí (Vuông góc) tại một Sơn cụ thể.")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        target_son = st.selectbox("1. Chọn Sơn cần tác động", SƠN_24_ZH)
    with col_t2:
        action_type = st.selectbox("2. Mục đích", ["Kích Hoạt Đồ Tốt (Cần Lực Triều Mạnh)", "Tháo Dỡ Đồ Xấu (Cần Lực Triều Yếu)"])
    with col_t3:
        if action_type == "Kích Hoạt Đồ Tốt (Cần Lực Triều Mạnh)":
            level = st.selectbox("3. Cấp độ kích hoạt (Dễ -> Khó)", [
                "Sơ cấp (Thái Âm đáo Sơn)",
                "Trung cấp (Thái Âm + 1 sao khác đáo Sơn)",
                "Cao cấp (Sóc/Vọng Nguyệt đáo Sơn)"
            ])
            scan_days = 30 if "Cao cấp" not in level else 180
        else:
            level = st.selectbox("3. Điều kiện Tháo dỡ", ["Thượng/Hạ Huyền (Nhật Nguyệt vuông góc 90°)"])
            scan_days = 30
            
    st.caption(f"*Hệ thống sẽ quét tự động trong **{scan_days} ngày** tính từ ngày dự kiến ở Menu bên trái.*")
    
    if st.button("Thực Thi Quét Phân Tích", type="primary"):
        st.markdown("> Đang chạy thuật toán quét chi tiết (Two-pass algorithm)...")
        progress = st.progress(0)
        
        start_date_scan = dt_target
        results = []
        
        # --- LOGIC THÁO DỠ (NHẬT NGUYỆT VUÔNG GÓC 90 ĐỘ) ---
        if action_type == "Tháo Dỡ Đồ Xấu (Cần Lực Triều Yếu)":
            for d in range(scan_days):
                progress.progress(d / scan_days)
                check_day = start_date_scan + datetime.timedelta(days=d)
                
                # Quét thô mỗi 6 tiếng để tìm ngày Thượng/Hạ Huyền (Vuông góc ~ 6 sơn)
                df_check = calculate_positions(check_day, lat, lon, ['Thái Dương', 'Thái Âm'])
                sun_s = df_check.loc[0, 'Sơn']
                moon_s = df_check.loc[1, 'Sơn']
                
                # Tính khoảng cách Sơn (Vuông góc = cách nhau 6 sơn)
                diff = abs(SƠN_24_ZH.index(sun_s) - SƠN_24_ZH.index(moon_s))
                if diff in [5, 6, 7, 17, 18, 19]: # Cho phép biên độ sai số nhẹ của 90 độ
                    
                    # Quét tinh (Từng 15 phút) trong ngày đó
                    for m in range(0, 24*60, 15):
                        exact_time = check_day.replace(hour=0, minute=0) + datetime.timedelta(minutes=m)
                        df_exact = calculate_positions(exact_time, lat, lon, ['Thái Dương', 'Thái Âm'])
                        s_exact = df_exact.loc[0, 'Sơn']
                        m_exact = df_exact.loc[1, 'Sơn']
                        
                        # Điều kiện: Vuông góc VÀ cả 2 sao đều KHÔNG nằm ở Sơn cần tháo dỡ
                        diff_exact = abs(SƠN_24_ZH.index(s_exact) - SƠN_24_ZH.index(m_exact))
                        if diff_exact in [6, 18] and s_exact != target_son and m_exact != target_son:
                            results.append({
                                "Ngày": exact_time.strftime("%d/%m/%Y"),
                                "Giờ Tuyệt Đối": exact_time.strftime("%H:%M"),
                                "Tình Trạng": f"Nhật ở {s_exact}, Nguyệt ở {m_exact} (An toàn tháo {target_son})"
                            })
                            break # Tìm được 1 khung giờ trong ngày là đủ
                            
        # --- LOGIC KÍCH HOẠT ĐỒ TỐT ---
        else:
            if level == "Sơ cấp (Thái Âm đáo Sơn)":
                for d in range(7): # Sơ cấp dễ tìm, chỉ cần quét 7 ngày
                    progress.progress(d / 7)
                    for m in range(0, 24*60, 10): # Quét mỗi 10 phút
                        exact_time = start_date_scan + datetime.timedelta(days=d, minutes=m)
                        df_exact = calculate_positions(exact_time, lat, lon, ['Thái Âm'])
                        if df_exact.loc[0, 'Sơn'] == target_son:
                            results.append({"Ngày": exact_time.strftime("%d/%m/%Y"), "Giờ Kích Hoạt": exact_time.strftime("%H:%M"), "Hiện Tượng": f"Thái Âm nhập Sơn {target_son}"})
                            break # Chuyển sang ngày tiếp theo
                            
            elif level == "Trung cấp (Thái Âm + 1 sao khác đáo Sơn)":
                for d in range(scan_days):
                    progress.progress(d / scan_days)
                    for m in range(0, 24*60, 30):
                        exact_time = start_date_scan + datetime.timedelta(days=d, minutes=m)
                        df_exact = calculate_positions(exact_time, lat, lon, ['Thái Âm', 'Mộc Tinh', 'Kim Tinh', 'Thủy Tinh', 'Hỏa Tinh', 'Thổ Tinh'])
                        
                        bodies_in_son = df_exact[df_exact['Sơn'] == target_son]['Tên'].tolist()
                        if 'Thái Âm' in bodies_in_son and len(bodies_in_son) >= 2:
                            results.append({"Ngày": exact_time.strftime("%d/%m/%Y"), "Giờ Kích Hoạt": exact_time.strftime("%H:%M"), "Hiện Tượng": f"Hội tụ tại {target_son}: {', '.join(bodies_in_son)}"})
                            break
                            
            elif level == "Cao cấp (Sóc/Vọng Nguyệt đáo Sơn)":
                for d in range(scan_days):
                    progress.progress(d / scan_days)
                    check_day = start_date_scan + datetime.timedelta(days=d)
                    df_check = calculate_positions(check_day, lat, lon, ['Thái Dương', 'Thái Âm'])
                    
                    sun_chi = df_check.loc[0, 'Chi']
                    moon_chi = df_check.loc[1, 'Chi']
                    
                    # Tìm ngày Sóc (Cùng Chi) hoặc Vọng (Xung Chi)
                    if sun_chi == moon_chi or abs(DI_CHI_ZH.index(sun_chi) - DI_CHI_ZH.index(moon_chi)) == 6:
                        for m in range(0, 24*60, 15):
                            exact_time = check_day.replace(hour=0, minute=0) + datetime.timedelta(minutes=m)
                            df_exact = calculate_positions(exact_time, lat, lon, ['Thái Dương', 'Thái Âm'])
                            
                            # Kiểm tra xem lúc đó Nhật hoặc Nguyệt có nằm đúng Sơn mục tiêu không
                            if df_exact.loc[0, 'Sơn'] == target_son or df_exact.loc[1, 'Sơn'] == target_son:
                                phase = "Sóc Nguyệt" if sun_chi == moon_chi else "Vọng Nguyệt"
                                results.append({"Ngày": exact_time.strftime("%d/%m/%Y"), "Giờ Kích Hoạt": exact_time.strftime("%H:%M"), "Hiện Tượng": f"{phase} đáo Sơn {target_son}"})
                                break

        progress.progress(100)
        st.markdown("---")
        if results:
            st.markdown(f"**TÌM THẤY {len(results)} THỜI ĐIỂM TỐI ƯU:**")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.markdown("> **[THÔNG BÁO]** Không tìm thấy thời điểm nào thỏa mãn điều kiện khó này trong khung thời gian quét. Vui lòng hạ cấp độ kích hoạt hoặc mở rộng ngày dự kiến.")
