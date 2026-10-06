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
    </style>
""", unsafe_allow_html=True)

# ==========================================
# XỬ LÝ LỖI MÔI TRƯỜNG CHUYÊN NGHIỆP
# ==========================================
try:
    from skyfield.api import load, Topos
    from skyfield.framelib import ecliptic_J2000
except ImportError:
    st.error("HỆ THỐNG YÊU CẦU KHỞI ĐỘNG LẠI MÁY CHỦ (REBOOT)")
    st.markdown("""
    > **Nguyên nhân:** Máy chủ Streamlit Cloud đang lưu cache phiên bản thư viện cũ.
    > 
    > **Cách khắc phục nhanh:**
    > 1. Nhìn xuống **góc dưới cùng bên phải** màn hình, bấm vào nút **'Manage app'**.
    > 2. Bấm vào biểu tượng **3 dấu chấm (⋮)** ở góc trên thanh menu vừa hiện ra.
    > 3. Chọn **'Reboot app'** hoặc **'Clear cache and deploy'**.
    > 
    > *Sau khi Reboot, hệ thống sẽ tự động cập nhật thư viện từ file requirements.txt và hoạt động bình thường.*
    """)
    st.stop() # Dừng chạy code bên dưới nếu lỗi thư viện

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
    'Thái Dương':  {'char': '日', 'color': '#2C3E50', 'node': eph['sun']},
    'Thái Âm':     {'char': '月', 'color': '#2C3E50', 'node': eph['moon']},
    'Thủy Tinh':   {'char': '水', 'color': '#7F8C8D', 'node': eph['mercury']},
    'Kim Tinh':    {'char': '金', 'color': '#7F8C8D', 'node': eph['venus']},
    'Hỏa Tinh':    {'char': '火', 'color': '#7F8C8D', 'node': eph['mars']},
    'Mộc Tinh':    {'char': '木', 'color': '#7F8C8D', 'node': eph['jupiter barycenter']},
    'Thổ Tinh':    {'char': '土', 'color': '#7F8C8D', 'node': eph['saturn barycenter']},
    'Thiên Vương': {'char': '天', 'color': '#BDC3C7', 'node': eph['uranus barycenter']},
    'Hải Vương':   {'char': '海', 'color': '#BDC3C7', 'node': eph['neptune barycenter']},
    'Diêm Vương':  {'char': '冥', 'color': '#BDC3C7', 'node': eph['pluto barycenter']}
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
        
        astrometric = earth.at(time).observe(body_node)
        lat_ecl, lon_ecl, _ = astrometric.frame_latlon(ecliptic_J2000)
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
# 3. HÀM VẼ LA BÀN ĐƠN SẮC
# ==========================================
def draw_professional_luopan(df):
    fig = go.Figure()
    df['r_plot'] = 90 - df['Altitude (°)']
    df_visible = df[df['Altitude (°)'] >= -10].copy()

    for idx, row in df_visible.iterrows():
        marker_size = 12 if row['Tên'] in ['Thái Dương', 'Thái Âm'] else 8
        text_weight = "bold" if row['Tên'] in ['Thái Dương', 'Thái Âm'] else "normal"
        
        fig.add_trace(go.Scatterpolar(
            r=[row['r_plot']],
            theta=[row['Azimuth (°)']],
            mode='markers+text',
            marker=dict(size=marker_size, color=row['Màu'], symbol='circle'),
            text=f"<b>{row['Ký Hiệu']}</b>" if text_weight == "bold" else row['Ký Hiệu'],
            textposition="bottom center",
            textfont=dict(size=14, color="#2C3E50", family="Arial"),
            name=row['Tên'],
            hoverinfo="text",
            hovertext=f"{row['Tên']}<br>Azimuth: {row['Azimuth (°)']}° (Sơn {row['Sơn']})<br>Altitude: {row['Altitude (°)']}°"
        ))

    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                direction="clockwise", rotation=90,
                tickmode="array", tickvals=[i * 15 for i in range(24)], ticktext=SƠN_24,
                showline=True, linewidth=1, linecolor='#7F8C8D', gridcolor='#E5E7E9'
            ),
            radialaxis=dict(visible=True, range=[0, 90], showticklabels=False, gridcolor='#E5E7E9', angle=90)
        ),
        showlegend=False, paper_bgcolor="white", plot_bgcolor="white", margin=dict(t=40, b=40, l=40, r=40), height=600
    )
    
    fig.add_trace(go.Scatterpolar(r=[30, 30], theta=[0, 360], mode='lines', line=dict(color='#BDC3C7', dash='dot'), hoverinfo='skip'))
    fig.add_trace(go.Scatterpolar(r=[60, 60], theta=[0, 360], mode='lines', line=dict(color='#BDC3C7', dash='dot'), hoverinfo='skip'))
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
default_bodies = ['Thái Dương', 'Thái Âm', 'Thủy Tinh', 'Kim Tinh', 'Hỏa Tinh', 'Mộc Tinh', 'Thổ Tinh']
active_bodies = st.sidebar.multiselect("Bật/Tắt dữ liệu", options=list(CELESTIAL_BODIES.keys()), default=default_bodies)

local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
dt_target = local_tz.localize(datetime.datetime.combine(target_date, target_time))

df_target = calculate_positions(dt_target, lat, lon, active_bodies)

st.markdown("<h2 style='text-align: center; color: #2C3E50; margin-bottom: 30px;'>HỆ THỐNG PHÂN TÍCH TINH TƯỢNG TRẠCH NHẬT</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["I. THIÊN THỂ ĐÁO SƠN", "II. ĐỐI XUNG CÁ NHÂN", "III. TRA CỨU LIÊN CHÂU"])

with tab1:
    col_chart, col_data = st.columns([1.5, 1])
    with col_chart:
        st.markdown(f"**ĐỒ HÌNH BẦU TRỜI TẠI THỰC ĐỊA** | *{dt_target.strftime('%d/%m/%Y %H:%M')}*")
        st.caption("Tâm biểu đồ = Thiên đỉnh (90°). Viền ngoài = Đường chân trời (0°).")
        fig = draw_professional_luopan(df_target)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_data:
        st.markdown("**BẢNG THÔNG SỐ TỌA ĐỘ**")
        st.dataframe(df_target[['Tên', 'Ký Hiệu', 'Sơn', 'Azimuth (°)', 'Altitude (°)']], hide_index=True, use_container_width=True)
        st.markdown("> **Hướng dẫn phân tích:**\n> - Dùng góc Azimuth (0-360) để so khớp với la bàn đo thực tế tại công trình.\n> - Các hành tinh có Altitude < 0 hiện đang nằm dưới chân trời.")

with tab2:
    st.markdown("### ĐỐI CHIẾU LÁ SỐ BẨM SINH & THỜI ĐIỂM DỰ KIẾN")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        birth_date = st.date_input("Ngày sinh (Dương lịch)", value=datetime.date(1990, 1, 1))
    with col_b2:
        birth_time = st.time_input("Giờ sinh", value=datetime.time(12, 0))
        
    dt_birth = local_tz.localize(datetime.datetime.combine(birth_date, birth_time))
    
    if st.button("Thực Thi Kiểm Tra", type="primary"):
        df_birth = calculate_positions(dt_birth, lat, lon, active_bodies)
        def check_xung(c1, c2): return abs(DI_CHI.index(c1) - DI_CHI.index(c2)) == 6
            
        try:
            jup_b = df_birth.loc[df_birth['Tên'] == 'Mộc Tinh', 'Chi'].values[0]
            jup_t = df_target.loc[df_target['Tên'] == 'Mộc Tinh', 'Chi'].values[0]
            sun_b = df_birth.loc[df_birth['Tên'] == 'Thái Dương', 'Chi'].values[0]
            sun_t = df_target.loc[df_target['Tên'] == 'Thái Dương', 'Chi'].values[0]
            moon_b = df_birth.loc[df_birth['Tên'] == 'Thái Âm', 'Chi'].values[0]
            moon_t = df_target.loc[df_target['Tên'] == 'Thái Âm', 'Chi'].values[0]
            
            st.markdown("---")
            st.markdown("#### BÁO CÁO PHÂN TÍCH")
            has_error = False
            
            if check_xung(jup_b, jup_t): 
                st.markdown(f"> **[CẢNH BÁO - NĂM]** Mộc Tinh dự kiến (Khu vực {jup_t}) trực xung với bản mệnh (Khu vực {jup_b}).")
                has_error = True
            else:
                st.markdown(f"> **[HỢP LỆ - NĂM]** Mộc Tinh ({jup_t} / {jup_b})")
                
            if check_xung(sun_b, sun_t): 
                st.markdown(f"> **[CẢNH BÁO - THÁNG]** Thái Dương dự kiến (Khu vực {sun_t}) trực xung với bản mệnh (Khu vực {sun_b}).")
                has_error = True
            else:
                st.markdown(f"> **[HỢP LỆ - THÁNG]** Thái Dương ({sun_t} / {sun_b})")
                
            if check_xung(moon_b, moon_t): 
                st.markdown(f"> **[CẢNH BÁO - NGÀY]** Thái Âm dự kiến (Khu vực {moon_t}) trực xung với bản mệnh (Khu vực {moon_b}).")
                has_error = True
            else:
                st.markdown(f"> **[HỢP LỆ - NGÀY]** Thái Âm ({moon_t} / {moon_b})")
                
            if not has_error:
                st.markdown("<br>**KẾT LUẬN:** Thời điểm dự kiến hòa hợp với lá số cá nhân, không xuất hiện hiện tượng đối xung.", unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown("> **[LỖI DỮ LIỆU]** Vui lòng đảm bảo đã bật hiển thị Thái Dương, Thái Âm và Mộc Tinh ở menu cài đặt để thực hiện thuật toán này.")

with tab3:
    st.markdown("### THUẬT TOÁN QUÉT ĐA TINH LIÊN CHÂU")
    st.markdown("Hệ thống sẽ quét các dữ liệu ephemeris để tìm ra các thời điểm thiên thể hội tụ (Alignment) trong tương lai.")
    
    sc_col1, sc_col2, sc_col3 = st.columns(3)
    with sc_col1:
        scan_years = st.selectbox("Khung thời gian", [1, 3, 5], format_func=lambda x: f"Quét trong {x} năm tới")
    with sc_col2:
        min_stars = st.selectbox("Điều kiện hội tụ", [4, 5, 6, 7], index=1, format_func=lambda x: f"Tối thiểu {x} thiên thể")
    with sc_col3:
        arc_limit = st.slider("Biên độ góc (Độ)", min_value=10, max_value=45, value=30, step=5)
        
    if st.button("Thực Thi Quét Dữ Liệu", type="primary"):
        st.markdown("> Đang truy xuất dữ liệu quỹ đạo. Quá trình này sẽ tính toán theo chu kỳ 5 ngày/lần để tối ưu hóa bộ nhớ máy chủ...")
        progress_bar = st.progress(0)
        
        start_date = dt_target
        results_lc = []
        days_to_scan = scan_years * 365
        step_days = 5
        
        for day in range(0, days_to_scan, step_days):
            progress_bar.progress(day / days_to_scan)
            check_time = start_date + datetime.timedelta(days=day)
            
            df_check = calculate_positions(check_time, lat, lon, active_bodies)
            lons = df_check['Hoàng Đạo (°)'].tolist()
            names = df_check['Tên'].tolist()
            
            max_cluster_size = 0
            best_cluster = []
            
            for i, base_lon in enumerate(lons):
                cluster = []
                for j, check_lon in enumerate(lons):
                    diff = min((base_lon - check_lon) % 360, (check_lon - base_lon) % 360)
                    if diff <= arc_limit:
                        cluster.append(names[j])
                
                if len(cluster) > max_cluster_size:
                    max_cluster_size = len(cluster)
                    best_cluster = cluster
                    
            if max_cluster_size >= min_stars:
                if not results_lc or (check_time - results_lc[-1]['Datetime']).days > 10:
                    results_lc.append({
                        "Datetime": check_time,
                        "Thời Gian": check_time.strftime("%d/%m/%Y"),
                        "Cấp Độ": f"{max_cluster_size} Hành Tinh",
                        "Thiên Thể Hội Tụ": ", ".join(best_cluster)
                    })
                    
        progress_bar.progress(100)
        st.markdown("---")
        if results_lc:
            st.markdown(f"**KẾT QUẢ:** Tìm thấy {len(results_lc)} chu kỳ thỏa mãn điều kiện.")
            df_res = pd.DataFrame(results_lc).drop(columns=['Datetime'])
            st.dataframe(df_res, use_container_width=True)
        else:
            st.markdown("> **[THÔNG BÁO]** Không phát hiện hiện tượng liên châu nào thỏa mãn tham số đầu vào trong khung thời gian này.")
