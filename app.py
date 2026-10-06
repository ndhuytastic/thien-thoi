import streamlit as st
from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_J2000
import datetime
import pytz
import pandas as pd
import plotly.graph_objects as go
import math

# ==========================================
# CẤU HÌNH TRANG
# ==========================================
st.set_page_config(page_title="Thiên Thời Sách - PRO", layout="wide", initial_sidebar_state="expanded")

# Thêm CSS để giao diện phẳng, chuyên nghiệp hơn
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {gap: 20px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px 5px 0 0; padding-left: 20px; padding-right: 20px;}
    .stTabs [aria-selected="true"] {background-color: #ffffff; border-bottom: 2px solid #000000;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DỮ LIỆU & CACHE (SKYFIELD)
# ==========================================
@st.cache_resource
def load_astronomy_data():
    # Load dữ liệu Ephemeris JPL (de421 chứa đủ 10 thiên thể bao gồm Pluto)
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = load_astronomy_data()
earth = eph['earth']

# Từ điển 10 Thiên thể (Tên hiển thị, Ký hiệu Hán, Màu sắc Hex, Node Skyfield)
CELESTIAL_BODIES = {
    'Thái Dương':  {'char': '日', 'color': '#D35400', 'node': eph['sun']},
    'Thái Âm':     {'char': '月', 'color': '#7F8C8D', 'node': eph['moon']},
    'Thủy Tinh':   {'char': '水', 'color': '#3498DB', 'node': eph['mercury']},
    'Kim Tinh':    {'char': '金', 'color': '#F1C40F', 'node': eph['venus']},
    'Hỏa Tinh':    {'char': '火', 'color': '#C0392B', 'node': eph['mars']},
    'Mộc Tinh':    {'char': '木', 'color': '#8E44AD', 'node': eph['jupiter barycenter']},
    'Thổ Tinh':    {'char': '土', 'color': '#A67C00', 'node': eph['saturn barycenter']},
    'Thiên Vương': {'char': '天', 'color': '#1ABC9C', 'node': eph['uranus barycenter']},
    'Hải Vương':   {'char': '海', 'color': '#2980B9', 'node': eph['neptune barycenter']},
    'Diêm Vương':  {'char': '冥', 'color': '#2C3E50', 'node': eph['pluto barycenter']}
}

DI_CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
SƠN_24 = ["Tý", "Quý", "Sửu", "Cấn", "Dần", "Giáp", "Mão", "Ất", "Thìn", "Tốn", "Tỵ", "Bính", 
          "Ngọ", "Đinh", "Mùi", "Khôn", "Thân", "Canh", "Dậu", "Tân", "Tuất", "Càn", "Hợi", "Nhâm"]

def get_di_chi(degree): return DI_CHI[int(((degree + 15) % 360) / 30)]
def get_24_son(azimuth): return SƠN_24[int(((azimuth + 7.5) % 360) / 15)]

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
        
        # Tọa độ Hoàng đạo
        astrometric = earth.at(time).observe(body_node)
        lat_ecl, lon_ecl, _ = astrometric.frame_latlon(ecliptic_J2000)
        
        # Tọa độ Phương vị - Góc cao (Azimuth - Altitude)
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
# 3. HÀM VẼ LA BÀN (PLOTLY)
# ==========================================
def draw_professional_luopan(df):
    fig = go.Figure()

    # Tính toán bán kính vẽ (R). 
    # Tâm = Thiên đỉnh (Alt=90) -> r=0. Vành ngoài = Chân trời (Alt=0) -> r=90.
    # Các sao có Alt < 0 (dưới chân trời) sẽ có r > 90 (nằm ngoài vòng la bàn).
    df['r_plot'] = 90 - df['Altitude (°)']
    
    # Chỉ vẽ các sao nằm trên chân trời (hoặc hơi mờ dưới chân trời)
    df_visible = df[df['Altitude (°)'] >= -10].copy()

    for idx, row in df_visible.iterrows():
        # Size lớn hơn cho Nhật/Nguyệt để nhấn mạnh Lực gây triều
        marker_size = 14 if row['Tên'] in ['Thái Dương', 'Thái Âm'] else 10
        
        fig.add_trace(go.Scatterpolar(
            r=[row['r_plot']],
            theta=[row['Azimuth (°)']],
            mode='markers+text',
            marker=dict(size=marker_size, color=row['Màu'], line=dict(width=1, color='white')),
            text=row['Ký Hiệu'],
            textposition="bottom center",
            textfont=dict(size=14, color="black", family="Arial"),
            name=row['Tên'],
            hoverinfo="text",
            hovertext=f"<b>{row['Tên']}</b><br>Azimuth: {row['Azimuth (°)']}° (Sơn {row['Sơn']})<br>Altitude: {row['Altitude (°)']}°"
        ))

    # Cấu hình mặt la bàn chuẩn
    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                direction="clockwise", rotation=90,
                tickmode="array", tickvals=[i * 15 for i in range(24)], ticktext=SƠN_24,
                showline=True, linewidth=2, linecolor='#333333', gridcolor='#E5E7E9'
            ),
            radialaxis=dict(
                visible=True, range=[0, 90],
                showticklabels=False, gridcolor='#E5E7E9', angle=90
            )
        ),
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(t=40, b=40, l=40, r=40),
        height=600
    )
    
    # Vẽ thêm các vòng tròn lưới (Altitude 30, 60)
    fig.add_trace(go.Scatterpolar(r=[30, 30], theta=[0, 360], mode='lines', line=dict(color='#BDC3C7', dash='dash'), hoverinfo='skip'))
    fig.add_trace(go.Scatterpolar(r=[60, 60], theta=[0, 360], mode='lines', line=dict(color='#BDC3C7', dash='dash'), hoverinfo='skip'))

    return fig

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.markdown("## ⚙️ CÀI ĐẶT THÔNG SỐ")

st.sidebar.markdown("### 1. Tọa độ thực địa")
lat = st.sidebar.number_input("Vĩ độ (Lat)", value=21.0285, format="%.4f")
lon = st.sidebar.number_input("Kinh độ (Lon)", value=105.8542, format="%.4f")

st.sidebar.markdown("### 2. Thời gian xem tinh bàn")
target_date = st.sidebar.date_input("Ngày dương lịch", value=datetime.date.today())
target_time = st.sidebar.time_input("Giờ địa phương", value=datetime.datetime.now().time())

st.sidebar.markdown("### 3. Hiển thị Thiên thể")
# Mặc định chọn 7 sao cơ bản
default_bodies = ['Thái Dương', 'Thái Âm', 'Thủy Tinh', 'Kim Tinh', 'Hỏa Tinh', 'Mộc Tinh', 'Thổ Tinh']
active_bodies = st.sidebar.multiselect("Bật/Tắt hiển thị", options=list(CELESTIAL_BODIES.keys()), default=default_bodies)

local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
dt_target = local_tz.localize(datetime.datetime.combine(target_date, target_time))

# Lấy dữ liệu mục tiêu
df_target = calculate_positions(dt_target, lat, lon, active_bodies)

st.markdown("<h2 style='text-align: center;'>HỆ THỐNG PHÂN TÍCH TINH TƯỢNG TRẠCH NHẬT</h2>", unsafe_allow_html=True)
st.markdown("---")

# TẠO 3 TABS CHUYÊN NGHIỆP
tab1, tab2, tab3 = st.tabs(["🧭 1. THIÊN THỂ ĐÁO SƠN", "👤 2. ĐỐI XUNG CÁ NHÂN", "🔭 3. TÌM LIÊN CHÂU (ALIGNMENT)"])

# ----------------- TAB 1: LA BÀN ĐÁO SƠN -----------------
with tab1:
    col_chart, col_data = st.columns([1.5, 1])
    
    with col_chart:
        st.markdown(f"**Đồ hình bầu trời thực tế tại lúc:** {dt_target.strftime('%d/%m/%Y %H:%M')}")
        st.caption("*Tâm biểu đồ = Đỉnh đầu. Viền ngoài = Đường chân trời.*")
        fig = draw_professional_luopan(df_target)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_data:
        st.markdown("**Bảng thông số Tọa độ (Az/Alt)**")
        st.dataframe(df_target[['Tên', 'Ký Hiệu', 'Sơn', 'Azimuth (°)', 'Altitude (°)']], hide_index=True, use_container_width=True)
        
        st.info("💡 **Gợi ý sử dụng:**\n\n- Các sao càng gần tâm là đang treo cao trên đỉnh đầu.\n- Các sao có Altitude < 0 là đang lặn dưới chân trời (ẩn).\n- Dùng góc Azimuth để so khớp với la bàn đo thực tế tại nhà.")

# ----------------- TAB 2: ĐỐI XUNG CÁ NHÂN -----------------
with tab2:
    st.markdown("### SO SÁNH LÁ SỐ BẨM SINH & THỜI ĐIỂM DỰ KIẾN")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        birth_date = st.date_input("Nhập ngày sinh (Dương lịch)", value=datetime.date(1990, 1, 1))
    with col_b2:
        birth_time = st.time_input("Nhập giờ sinh", value=datetime.time(12, 0))
        
    dt_birth = local_tz.localize(datetime.datetime.combine(birth_date, birth_time))
    
    if st.button("Kiểm tra Xung Khắc", type="primary"):
        df_birth = calculate_positions(dt_birth, lat, lon, active_bodies)
        
        def check_xung(c1, c2):
            return abs(DI_CHI.index(c1) - DI_CHI.index(c2)) == 6
            
        try:
            jup_b = df_birth.loc[df_birth['Tên'] == 'Mộc Tinh', 'Chi'].values[0]
            jup_t = df_target.loc[df_target['Tên'] == 'Mộc Tinh', 'Chi'].values[0]
            sun_b = df_birth.loc[df_birth['Tên'] == 'Thái Dương', 'Chi'].values[0]
            sun_t = df_target.loc[df_target['Tên'] == 'Thái Dương', 'Chi'].values[0]
            moon_b = df_birth.loc[df_birth['Tên'] == 'Thái Âm', 'Chi'].values[0]
            moon_t = df_target.loc[df_target['Tên'] == 'Thái Âm', 'Chi'].values[0]
            
            st.markdown("#### KẾT QUẢ QUÉT:")
            has_error = False
            
            if check_xung(jup_b, jup_t): 
                st.error(f"❌ NĂM XUNG: Mộc Tinh dự kiến ({jup_t}) xung với bản mệnh ({jup_b}).")
                has_error = True
            else:
                st.success(f"✅ NĂM HÒA HỢP: Mộc Tinh ({jup_t} / {jup_b})")
                
            if check_xung(sun_b, sun_t): 
                st.error(f"❌ THÁNG XUNG: Thái Dương dự kiến ({sun_t}) xung với bản mệnh ({sun_b}).")
                has_error = True
            else:
                st.success(f"✅ THÁNG HÒA HỢP: Thái Dương ({sun_t} / {sun_b})")
                
            if check_xung(moon_b, moon_t): 
                st.error(f"❌ NGÀY GIỜ XUNG: Thái Âm dự kiến ({moon_t}) xung với bản mệnh ({moon_b}).")
                has_error = True
            else:
                st.success(f"✅ NGÀY GIỜ HÒA HỢP: Thái Âm ({moon_t} / {moon_b})")
                
            if not has_error:
                st.balloons()
                
        except Exception as e:
            st.warning("Vui lòng bật hiển thị Thái Dương, Thái Âm và Mộc Tinh ở Menu bên trái để kiểm tra xung khắc.")

# ----------------- TAB 3: TÌM LIÊN CHÂU -----------------
with tab3:
    st.markdown("### QUÉT HIỆN TƯỢNG ĐA TINH LIÊN CHÂU (MULTI-STAR ALIGNMENT)")
    st.markdown("Tính năng này sẽ quét các ngày trong tương lai có các thiên thể hội tụ (Góc Hoàng đạo chênh lệch hẹp). *Lưu ý: Quá trình quét có thể mất vài giây.*")
    
    sc_col1, sc_col2, sc_col3 = st.columns(3)
    with sc_col1:
        scan_years = st.selectbox("Khung thời gian quét", [1, 3, 5], format_func=lambda x: f"Trong vòng {x} năm tới")
    with sc_col2:
        min_stars = st.selectbox("Số lượng sao tối thiểu", [4, 5, 6, 7], index=1, format_func=lambda x: f">= {x} sao thẳng hàng")
    with sc_col3:
        arc_limit = st.slider("Độ rộng cung hội tụ (Độ)", min_value=10, max_value=45, value=30, step=5, help="Các sao nằm trong một cung có độ rộng nhỏ hơn mức này sẽ được coi là thẳng hàng (Liên châu).")
        
    if st.button("Bắt đầu Quét dữ liệu", type="primary"):
        # Cảnh báo mô phỏng vì tính năng quét nhiều năm rất nặng trên web
        st.warning("Đang chạy thuật toán quét quỹ đạo... (Trên môi trường Web Cloud, thuật toán quét sẽ lấy mẫu mỗi 5 ngày để tránh quá tải server).")
        
        progress_bar = st.progress(0)
        
        # MÔ PHỎNG QUÉT (Simplified algorithm for web performance)
        start_date = dt_target
        results_lc = []
        days_to_scan = scan_years * 365
        step_days = 5 # Bước nhảy 5 ngày để tăng tốc
        
        for day in range(0, days_to_scan, step_days):
            progress_bar.progress(day / days_to_scan)
            check_time = start_date + datetime.timedelta(days=day)
            
            # Tính tọa độ hoàng đạo của các sao đang bật
            df_check = calculate_positions(check_time, lat, lon, active_bodies)
            
            # Logic tìm liên châu (đơn giản hóa): Tìm cụm sao lớn nhất rơi vào cung < arc_limit
            lons = df_check['Hoàng Đạo (°)'].tolist()
            names = df_check['Tên'].tolist()
            
            max_cluster_size = 0
            best_cluster = []
            
            # Duyệt qua từng sao làm mốc, đếm số sao nằm trong vùng cung độ
            for i, base_lon in enumerate(lons):
                cluster = []
                for j, check_lon in enumerate(lons):
                    # Tính khoảng cách góc (ngắn nhất trên vòng tròn)
                    diff = min((base_lon - check_lon) % 360, (check_lon - base_lon) % 360)
                    if diff <= arc_limit:
                        cluster.append(names[j])
                
                if len(cluster) > max_cluster_size:
                    max_cluster_size = len(cluster)
                    best_cluster = cluster
                    
            if max_cluster_size >= min_stars:
                # Tránh lưu trùng lặp các ngày sát nhau
                if not results_lc or (check_time - results_lc[-1]['Datetime']).days > 10:
                    results_lc.append({
                        "Datetime": check_time,
                        "Thời Gian": check_time.strftime("%d/%m/%Y"),
                        "Số Sao": f"{max_cluster_size}A",
                        "Các Thiên Thể Hội Tụ": ", ".join(best_cluster)
                    })
                    
        progress_bar.progress(100)
        
        if results_lc:
            st.success(f"Đã tìm thấy {len(results_lc)} thời điểm xảy ra Đa Tinh Liên Châu")
            df_res = pd.DataFrame(results_lc).drop(columns=['Datetime'])
            st.dataframe(df_res, use_container_width=True)
        else:
            st.info("Không tìm thấy hiện tượng liên châu nào thỏa mãn điều kiện trong khung thời gian này.")
