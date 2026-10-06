import streamlit as st
import datetime
import pytz
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# CẤU HÌNH TRANG CHUYÊN NGHIỆP
# ==========================================
st.set_page_config(page_title="Thiên Thời Sách - Phân Tích Tinh Tượng", layout="wide", initial_sidebar_state="expanded")

# Đưa tiêu đề lên cao nhất, chữ nhỏ, chuyên nghiệp
st.markdown("<h3 style='text-align: center; color: #2C3E50; margin-top: -40px; margin-bottom: 20px; font-weight: bold;'>HỆ THỐNG PHÂN TÍCH TINH TƯỢNG TRẠCH NHẬT</h3>", unsafe_allow_html=True)

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
    st.error("HỆ THỐNG YÊU CẦU KHỞI ĐỘNG LẠI MÁY CHỦ (REBOOT). Vui lòng bấm 'Manage app' góc dưới bên phải -> Chọn dấu 3 chấm -> Reboot app.")
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
def get_angular_diff(a1, a2): return min((a1 - a2) % 360, (a2 - a1) % 360)

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
            "Hoàng Đạo (°)": round(lon_ecl.degrees, 4),
            "Chi": get_di_chi(lon_ecl.degrees),
            "Azimuth (°)": round(az.degrees, 4),
            "Altitude (°)": round(alt.degrees, 4),
            "Sơn": get_24_son(az.degrees)
        })
    return pd.DataFrame(results)

# ==========================================
# 3. HÀM VẼ LA BÀN (NAM Ở TRÊN, NHỎ GỌN)
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

    # Cấu hình mặt la bàn: rotation=-90 để Nam (180 độ, Ngọ) lên trên cùng
    fig.update_layout(
        polar=dict(
            angularaxis=dict(
                direction="clockwise", rotation=-90,
                tickmode="array", tickvals=[i * 15 for i in range(24)], ticktext=SƠN_24_ZH,
                showline=False, showgrid=False
            ),
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

tab1, tab2, tab3 = st.tabs(["I. THIÊN THỂ ĐÁO SƠN", "II. LÁ SỐ ĐỐI XUNG", "III. TRẠCH NHẬT KÍCH HOẠT / THÁO DỠ"])

# ----------------- TAB 1 -----------------
with tab1:
    col1_1, col1_2, col1_3 = st.columns([1, 2, 1]) # Ép biểu đồ vào giữa, nhỏ gọn
    with col1_2:
        st.markdown(f"**ĐỒ HÌNH BẦU TRỜI (NAM LÊN TRÊN)** | *{dt_target.strftime('%d/%m/%Y %H:%M')}*")
        fig = draw_professional_luopan(df_target)
        st.plotly_chart(fig, use_container_width=True)

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

# ----------------- TAB 3 -----------------
with tab3:
    st.markdown("### THUẬT TOÁN QUÉT CHI TIẾT TỪNG PHÚT")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        target_son = st.selectbox("1. Chọn Sơn mục tiêu", SƠN_24_ZH)
    with col_t2:
        action_type = st.selectbox("2. Hành động", ["KÍCH HOẠT (Lực Triều Vượng)", "THÁO DỠ (Lực Triều Suy)"])
    with col_t3:
        if action_type == "KÍCH HOẠT (Lực Triều Vượng)":
            level = st.selectbox("3. Cấp độ", ["Sơ cấp (Chỉ Thái Âm)", "Trung cấp (Đa Tinh Đáo Sơn)", "Cao cấp (Sóc/Vọng Nguyệt)"])
            scan_days = 30 if level != "Cao cấp (Sóc/Vọng Nguyệt)" else 180
        else:
            st.info("Chỉ quét ngày Thượng/Hạ Huyền (Nhật Nguyệt 90°)")
            scan_days = 30
            
    if st.button("Thực Thi Quét Phân Tích", type="primary"):
        st.markdown(f"> Đang áp dụng thuật toán Two-Pass Filtering quét trong {scan_days} ngày...")
        progress = st.progress(0)
        
        start_date_scan = dt_target
        results = []
        scan_bodies = active_bodies if len(active_bodies) >= 2 else list(CELESTIAL_BODIES.keys())
        
        # --- LOGIC THÁO DỠ ---
        if action_type == "THÁO DỠ (Lực Triều Suy)":
            for d in range(scan_days):
                progress.progress(d / scan_days)
                check_day = start_date_scan + datetime.timedelta(days=d)
                
                # Quét thô tìm ngày vuông góc (sai số 5 độ trên Hoàng đạo)
                df_rough = calculate_positions(check_day.replace(hour=12, minute=0), lat, lon, ['Thái Dương', 'Thái Âm'])
                diff_ecl = get_angular_diff(df_rough.loc[0, 'Hoàng Đạo (°)'], df_rough.loc[1, 'Hoàng Đạo (°)'])
                
                if 80 <= diff_ecl <= 100: # Xung quanh 90 độ (Thượng/Hạ Huyền)
                    best_minute = None
                    best_diff = 999
                    
                    # Quét tinh từng phút tìm lúc 90 độ chuẩn xác nhất
                    for m in range(0, 24*60, 5):
                        exact_time = check_day.replace(hour=0, minute=0) + datetime.timedelta(minutes=m)
                        df_exact = calculate_positions(exact_time, lat, lon, ['Thái Dương', 'Thái Âm'])
                        current_diff = abs(90 - get_angular_diff(df_exact.loc[0, 'Hoàng Đạo (°)'], df_exact.loc[1, 'Hoàng Đạo (°)']))
                        
                        if current_diff < best_diff:
                            best_diff = current_diff
                            best_minute = exact_time
                            
                    # Kiểm tra an toàn: Tại phút chuẩn 90 độ đó, Nhật & Nguyệt có nằm ngoài Sơn tháo dỡ không?
                    df_final = calculate_positions(best_minute, lat, lon, ['Thái Dương', 'Thái Âm'])
                    sun_s = df_final.loc[0, 'Sơn']
                    moon_s = df_final.loc[1, 'Sơn']
                    
                    if sun_s != target_son and moon_s != target_son:
                        results.append({
                            "Ngày": best_minute.strftime("%d/%m/%Y"),
                            "Giờ Cực Đỉnh": best_minute.strftime("%H:%M"),
                            "Hiện Tượng": f"Vuông góc chuẩn (Sai số {round(best_diff, 2)}°)",
                            "Ghi Chú": f"An toàn. Thái Dương ở {sun_s}, Thái Âm ở {moon_s}",
                            "Các sao khác tại Sơn": "Không xét"
                        })
                        
        # --- LOGIC KÍCH HOẠT ---
        else:
            for d in range(scan_days):
                progress.progress(d / scan_days)
                check_day = start_date_scan + datetime.timedelta(days=d)
                
                if level == "Cao cấp (Sóc/Vọng Nguyệt)":
                    df_rough = calculate_positions(check_day.replace(hour=12, minute=0), lat, lon, ['Thái Dương', 'Thái Âm'])
                    diff_ecl = get_angular_diff(df_rough.loc[0, 'Hoàng Đạo (°)'], df_rough.loc[1, 'Hoàng Đạo (°)'])
                    # Bỏ qua nếu không phải mùng 1 (diff~0) hoặc rằm (diff~180)
                    if not (diff_ecl < 10 or diff_ecl > 170): continue

                # Quét thô mỗi 1 tiếng xem Thái Âm có vào Sơn mục tiêu không
                moon_entered_hours = []
                for h in range(24):
                    rough_time = check_day.replace(hour=h, minute=0)
                    df_rough = calculate_positions(rough_time, lat, lon, ['Thái Âm'])
                    if df_rough.loc[0, 'Sơn'] == target_son:
                        moon_entered_hours.append(h)
                
                # Nếu có, quét tinh từng phút trong các giờ đó
                if moon_entered_hours:
                    start_h = min(moon_entered_hours)
                    end_h = max(moon_entered_hours)
                    
                    best_events = []
                    
                    for m in range(start_h * 60, (end_h + 1) * 60):
                        exact_time = check_day.replace(hour=0, minute=0) + datetime.timedelta(minutes=m)
                        df_exact = calculate_positions(exact_time, lat, lon, scan_bodies)
                        
                        moon_row = df_exact[df_exact['Tên'] == 'Thái Âm'].iloc[0]
                        if moon_row['Sơn'] != target_son: continue
                        
                        moon_az = moon_row['Azimuth (°)']
                        bodies_in_son = df_exact[df_exact['Sơn'] == target_son]['Tên'].tolist()
                        other_bodies = [b for b in bodies_in_son if b != 'Thái Âm']
                        
                        # Xử lý theo từng cấp độ
                        if level == "Sơ cấp (Chỉ Thái Âm)":
                            # Tìm phút Thái Âm vào chính giữa Sơn (Góc trung tâm = Index * 15)
                            center_az = SƠN_24_ZH.index(target_son) * 15
                            diff_to_center = get_angular_diff(moon_az, center_az)
                            best_events.append((diff_to_center, exact_time, "Thái Âm chính trung Sơn", other_bodies))
                            
                        elif level == "Trung cấp (Đa Tinh Đáo Sơn)" and len(other_bodies) > 0:
                            # 1. Trùng khớp từng sao
                            for ob in other_bodies:
                                ob_az = df_exact[df_exact['Tên'] == ob].iloc[0]['Azimuth (°)']
                                diff = get_angular_diff(moon_az, ob_az)
                                best_events.append((diff, exact_time, f"Trùng khớp {ob}", other_bodies))
                            
                            # 2. Trọng tâm phân tán (Sum sai số)
                            if len(other_bodies) > 1:
                                sum_diff = sum([get_angular_diff(moon_az, df_exact[df_exact['Tên'] == b].iloc[0]['Azimuth (°)']) for b in other_bodies])
                                best_events.append((sum_diff, exact_time, "Trọng tâm Đa tinh (Trung tâm năng lượng)", other_bodies))
                                
                        elif level == "Cao cấp (Sóc/Vọng Nguyệt)":
                            sun_row = df_exact[df_exact['Tên'] == 'Thái Dương'].iloc[0]
                            sun_az = sun_row['Azimuth (°)']
                            sun_s = sun_row['Sơn']
                            
                            # Điều kiện Sóc (Nhật Nguyệt cùng Sơn)
                            if sun_s == target_son:
                                diff = get_angular_diff(moon_az, sun_az)
                                best_events.append((diff, exact_time, "Sóc Nguyệt: Nhật Nguyệt trùng khớp", other_bodies))
                            # Điều kiện Vọng (Nhật đối diện Nguyệt)
                            elif abs(SƠN_24_ZH.index(sun_s) - SƠN_24_ZH.index(target_son)) == 12:
                                diff_180 = abs(180 - get_angular_diff(moon_az, sun_az))
                                best_events.append((diff_180, exact_time, "Vọng Nguyệt: Nhật Nguyệt đối đỉnh chuẩn", other_bodies))

                    # Lọc ra các kết quả tốt nhất (Sai số nhỏ nhất) trong ngày đó để hiển thị
                    if best_events:
                        # Gom nhóm theo "Hiện Tượng" và tìm Min sai số
                        df_events = pd.DataFrame(best_events, columns=['Diff', 'Time', 'Type', 'Others'])
                        best_idx = df_events.groupby('Type')['Diff'].idxmin()
                        for idx in best_idx:
                            row = df_events.loc[idx]
                            results.append({
                                "Ngày": row['Time'].strftime("%d/%m/%Y"),
                                "Giờ Cực Đỉnh": row['Time'].strftime("%H:%M"),
                                "Hiện Tượng": row['Type'],
                                "Ghi Chú": f"Sai số góc thấp nhất",
                                "Các sao khác tại Sơn": ", ".join(row['Others']) if row['Others'] else "Không có"
                            })

        progress.progress(100)
        st.markdown("---")
        if results:
            st.markdown(f"**TÌM THẤY CÁC THỜI ĐIỂM TỐI ƯU (ĐÃ TÌM ĐỈNH TỪNG PHÚT):**")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.markdown("> **[THÔNG BÁO]** Không tìm thấy thời điểm nào thỏa mãn điều kiện trong khung thời gian quét.")
