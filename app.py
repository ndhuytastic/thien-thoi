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
    
    /* Làm đẹp khu vực checkbox Sidebar */
    .stCheckbox {margin-bottom: -10px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# XỬ LÝ LỖI MÔI TRƯỜNG SKYFIELD
# ==========================================
try:
    from skyfield.api import load, Topos
except ImportError:
    st.error("HỆ THỐNG YÊU CẦU KHỞI ĐỘNG LẠI MÁY CHỦ (REBOOT)")
    st.stop()

# ==========================================
# 1. DỮ LIỆU & CACHE (SKYFIELD)
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

# Tiếng Trung cho Địa chi và 24 Sơn
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
# 3. HÀM VẼ LA BÀN 24 SƠN (PLOTLY)
# ==========================================
def draw_professional_luopan(df):
    fig = go.Figure()
    
    # Tâm (Alt=90) -> R=0. Chân trời (Alt=0) -> R=90. Dưới chân trời (Alt=-90) -> R=180.
    # Tính R sao cho tất cả thiên thể đều hiển thị được
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

    # Vẽ ranh giới 24 Sơn (Các đường thẳng cắt từ tâm ra rìa ở các góc 7.5, 22.5...)
    for i in range(24):
        border_angle = i * 15 + 7.5
        fig.add_trace(go.Scatterpolar(
            r=[0, 180], 
            theta=[border_angle, border_angle],
            mode='lines', 
            line=dict(color='#BDC3C7', width=1), 
            hoverinfo='skip'
        ))

    # Cấu hình mặt la bàn
    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                direction="clockwise", rotation=90,
                tickmode="array", tickvals=[i * 15 for i in range(24)], ticktext=SƠN_24_ZH,
                showline=False, showgrid=False # Tắt grid mặc định vì đã tự vẽ ranh giới ở trên
            ),
            radialaxis=dict(visible=False, range=[0, 180]) # Mở rộng bán kính đến 180 để bao trọn sao dưới chân trời
        ),
        showlegend=False, paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=30, b=30, l=30, r=30), height=600
    )
    
    # Vẽ các vòng tròn đồng tâm (Mô phỏng các tầng của La kinh)
    fig.add_trace(go.Scatterpolar(r=[90, 90], theta=[0, 360], mode='lines', line=dict(color='#7F8C8D', width=1.5), hoverinfo='skip')) # Đường chân trời
    fig.add_trace(go.Scatterpolar(r=[180, 180], theta=[0, 360], mode='lines', line=dict(color='#333333', width=2), hoverinfo='skip')) # Viền ngoài cùng

    return fig

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.markdown("### CÀI ĐẶT THÔNG SỐ")

st.sidebar.markdown("**1. Tọa độ thực địa**")
lat = st.sidebar.number_input("Vĩ độ (Lat)", value=21.0285, format="%.4f")
lon = st.sidebar.number_input("Kinh độ (Lon)", value=105.8542, format="%.4f")

st.sidebar.markdown("**2. Thời gian xem tinh bàn**")
target_date = st.sidebar.date_input("Ngày (Dương lịch)", value=datetime.date.today())
target_time = st.sidebar.time_input("Giờ địa phương", value=datetime.datetime.now().time())

st.sidebar.markdown("**3. Hiển thị Thiên thể**")
# Làm lại giao diện Bật/Tắt dễ nhìn hơn bằng 2 cột
col_cb1, col_cb2 = st.sidebar.columns(2)
active_bodies = []

for i, (name, info) in enumerate(CELESTIAL_BODIES.items()):
    # Mặc định bật 7 sao đầu tiên
    is_checked = True if i < 7 else False
    if i % 2 == 0:
        if col_cb1.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)
    else:
        if col_cb2.checkbox(f"{info['char']} {name}", value=is_checked): active_bodies.append(name)

local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
dt_target = local_tz.localize(datetime.datetime.combine(target_date, target_time))

df_target = calculate_positions(dt_target, lat, lon, active_bodies)

st.markdown("<h2 style='text-align: center; color: #2C3E50; margin-bottom: 30px;'>HỆ THỐNG PHÂN TÍCH TINH TƯỢNG TRẠCH NHẬT</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["I. THIÊN THỂ ĐÁO SƠN", "II. ĐỐI XUNG CÁ NHÂN", "III. TRA CỨU LIÊN CHÂU (CÙNG SƠN)"])

# ----------------- TAB 1 -----------------
with tab1:
    col_chart, col_data = st.columns([1.5, 1])
    with col_chart:
        st.markdown(f"**ĐỒ HÌNH BẦU TRỜI TẠI THỰC ĐỊA** | *{dt_target.strftime('%d/%m/%Y %H:%M')}*")
        fig = draw_professional_luopan(df_target)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    with col_data:
        st.markdown("**BẢNG THÔNG SỐ TỌA ĐỘ**")
        st.dataframe(df_target[['Tên', 'Ký Hiệu', 'Sơn', 'Azimuth (°)', 'Altitude (°)']], hide_index=True, use_container_width=True)

# ----------------- TAB 2 -----------------
with tab2:
    st.markdown("### ĐỐI CHIẾU LÁ SỐ BẨM SINH & THỜI ĐIỂM DỰ KIẾN")
    st.markdown("Kiểm tra nguyên tắc Xung Đối (Cách 180 độ / 6 Địa chi) giữa tinh bàn thời điểm làm việc và lá số bẩm sinh.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        birth_date = st.date_input("Ngày sinh (Dương lịch)", value=datetime.date(1990, 1, 1))
    with col_b2:
        birth_time = st.time_input("Giờ sinh", value=datetime.time(12, 0))
        
    dt_birth = local_tz.localize(datetime.datetime.combine(birth_date, birth_time))
    
    if st.button("Thực Thi Kiểm Tra", type="primary"):
        # Phải đảm bảo tính đủ 10 sao cho lá số để không bị lỗi nếu người dùng tắt ở Menu
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
            
        if not has_error:
            st.markdown("<br>**KẾT LUẬN:** Thời điểm dự kiến hòa hợp với lá số cá nhân, không xuất hiện hiện tượng đối xung.", unsafe_allow_html=True)

# ----------------- TAB 3 -----------------
with tab3:
    st.markdown("### TÌM KIẾM CÁC THIÊN THỂ CÙNG NẰM TRONG 1 SƠN HƯỚNG")
    st.markdown("Thuật toán quét các ngày có nhiều hành tinh cùng tụ hội vào **chung một Sơn (15 độ)** trên La bàn 24 Sơn.")
    
    sc_col1, sc_col2 = st.columns(2)
    with sc_col1:
        scan_years = st.selectbox("Khung thời gian", [1, 3, 5], format_func=lambda x: f"Quét trong {x} năm tới")
    with sc_col2:
        align_type = st.selectbox("Điều kiện hội tụ", [
            "Sóc Nguyệt (Nhật - Nguyệt cùng 1 Sơn)",
            "Vọng Nguyệt (Nhật - Nguyệt đối cung)",
            "3 Sao cùng 1 Sơn",
            "4 Sao cùng 1 Sơn",
            "5 Sao cùng 1 Sơn"
        ])
        
    if st.button("Thực Thi Quét Dữ Liệu", type="primary"):
        st.markdown("> Đang truy xuất dữ liệu quỹ đạo (Lấy mẫu 1 ngày/lần)...")
        progress_bar = st.progress(0)
        
        start_date = dt_target
        results_lc = []
        days_to_scan = scan_years * 365
        step_days = 1 # Quét mỗi ngày 1 lần
        
        # Chỉ quét các sao người dùng đang bật ở menu trái
        scan_bodies = active_bodies if len(active_bodies) >= 2 else list(CELESTIAL_BODIES.keys())
        
        for day in range(0, days_to_scan, step_days):
            progress_bar.progress(day / days_to_scan)
            check_time = start_date + datetime.timedelta(days=day)
            
            df_check = calculate_positions(check_time, lat, lon, scan_bodies)
            
            is_match = False
            match_details = ""
            
            # Logic 1: Sóc Nguyệt (Nhật Nguyệt cùng Sơn)
            if align_type == "Sóc Nguyệt (Nhật - Nguyệt cùng 1 Sơn)":
                sun_son = df_check.loc[df_check['Tên'] == 'Thái Dương', 'Sơn'].values[0]
                moon_son = df_check.loc[df_check['Tên'] == 'Thái Âm', 'Sơn'].values[0]
                if sun_son == moon_son:
                    is_match = True
                    match_details = f"Cùng tại Sơn {sun_son}"
            
            # Logic 2: Vọng Nguyệt (Nhật Nguyệt đối cung - cách nhau 12 sơn)
            elif align_type == "Vọng Nguyệt (Nhật - Nguyệt đối cung)":
                sun_son = df_check.loc[df_check['Tên'] == 'Thái Dương', 'Sơn'].values[0]
                moon_son = df_check.loc[df_check['Tên'] == 'Thái Âm', 'Sơn'].values[0]
                if abs(SƠN_24_ZH.index(sun_son) - SƠN_24_ZH.index(moon_son)) == 12:
                    is_match = True
                    match_details = f"Nhật Sơn {sun_son} - Nguyệt Sơn {moon_son}"
                    
            # Logic 3: Đa tinh cùng 1 Sơn
            else:
                target_count = int(align_type[0]) # Lấy số 3, 4, hoặc 5 từ chuỗi string
                # Đếm số thiên thể trong từng Sơn
                son_counts = df_check.groupby('Sơn')['Tên'].apply(list).to_dict()
                
                for son, bodies in son_counts.items():
                    if len(bodies) >= target_count:
                        is_match = True
                        match_details = f"Sơn {son}: {', '.join(bodies)}"
                        break # Chỉ cần tìm thấy 1 cụm là đạt
            
            if is_match:
                # Tránh lưu 2 ngày liên tiếp của cùng 1 hiện tượng dài ngày
                if not results_lc or (check_time - results_lc[-1]['Datetime']).days > 5:
                    results_lc.append({
                        "Datetime": check_time,
                        "Ngày Dương Lịch": check_time.strftime("%d/%m/%Y"),
                        "Hiện Tượng": align_type.split(" (")[0],
                        "Chi Tiết Hội Tụ": match_details
                    })
                    
        progress_bar.progress(100)
        st.markdown("---")
        if results_lc:
            st.markdown(f"**KẾT QUẢ:** Tìm thấy {len(results_lc)} ngày thỏa mãn điều kiện.")
            df_res = pd.DataFrame(results_lc).drop(columns=['Datetime'])
            st.dataframe(df_res, use_container_width=True)
        else:
            st.markdown("> **[THÔNG BÁO]** Không phát hiện hiện tượng nào thỏa mãn trong khung thời gian này.")
