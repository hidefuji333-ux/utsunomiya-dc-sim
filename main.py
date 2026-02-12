import streamlit as st
import plotly.graph_objects as go
import math

# --- ページ設定 ---
st.set_page_config(page_title="Professional DC Design Tool", layout="wide")
st.title("🏛️ DC Module Strategic Design & Validation Simulator")
st.markdown("---")

# --- サイドバー：プロフェッショナル・パラメータ ---
with st.sidebar:
    st.header("1. Rack & Aisle Configuration")
    rack_kw = st.number_input("Rack IT Load (kW)", value=30.0, step=1.0)
    racks_per_row = st.number_input("Racks per Row", value=20, step=1)
    cold_aisles_qty = st.number_input("Cold Aisle Count (CAC)", value=4, step=1)
    
    st.header("2. Physical Dimensions (m)")
    r_w, r_d = 0.6, 1.2    # Server Rack Size
    ca_w, ha_w = 1.8, 1.2  # Aisle Widths
    corridor_w = 2.4       # Perimeter Corridor
    
    st.header("3. Cooling & DLC Integration")
    liquid_ratio = st.slider("DLC (Direct Liquid Cooling) Ratio (%)", 0, 100, 30) / 100
    fwu_cap = st.number_input("FWU Cooling Cap (kW/unit)", value=400)
    fwu_pwr = st.number_input("FWU Power Consumption (kW)", value=15.0)
    cooling_type = st.selectbox("Airflow Path", ["Single Side Intake", "Dual Side Intake"])

    st.header("4. Electrical Infrastructure")
    ups_cap = st.number_input("UPS Unit Capacity (kVA)", value=1200)
    ups_n = st.number_input("UPS Unit Count (N+1 Config)", value=6)
    gen_cap = st.number_input("Gen Capacity (kVA)", value=3000)
    gen_n = st.number_input("Gen Count (N-1 Config)", value=4)

# --- 演算ロジック ---
total_racks = int(racks_per_row * cold_aisles_qty * 2)
it_kw = float(total_racks * rack_kw)
it_mw = it_kw / 1000.0

# 空調負荷：DLC分を差し引いた顕熱負荷
air_load_kw = it_kw * (1.0 - liquid_ratio)
fwu_count = math.ceil(air_load_kw / fwu_cap) + 2 # N+2 redundancy
total_cooling_pwr_kw = fwu_count * fwu_pwr

# 設備容量検証
ups_pf = 0.9
eff_ups_kva = ups_cap * (ups_n - 1)
ups_ok = (it_kw / ups_pf) <= eff_ups_kva

total_site_load_kva = (it_kw + total_cooling_pwr_kw) / ups_pf
eff_gen_kva = gen_cap * (gen_n - 1)
gen_ok = total_site_load_kva <= eff_gen_kva

# --- ビジュアル・メトリクス表示 ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total IT Load", f"{it_mw:.2f} MW")
m2.metric("Air Cooling Load", f"{air_load_kw/1000:.2f} MW")
m3.metric("FWU Units (N+2)", f"{fwu_count} Units")
m4.metric("Gen Status (N-1)", "✅ Valid" if gen_ok else "❌ Insufficient")

# --- Plotly 高精細平面図描画 ---
fig = go.Figure()

# ホール内寸計算
h_l = racks_per_row * r_w
h_w = (cold_aisles_qty * 2 * r_d) + (cold_aisles_qty * ca_w) + (cold_aisles_qty * ha_w)
fwu_room_d = 4.0 # 空調機械室奥行

# 配置オフセット
offset_x = corridor_w + fwu_room_d
offset_y = corridor_w

# 1. 建物外郭と廊下
fig.add_shape(type="rect", x0=0, y0=0, x1=h_l + (fwu_room_d * 2) + (corridor_w * 2), y1=h_w + (corridor_w * 2), 
              line=dict(color="black", width=3), fillcolor="white")

# 2. 空調機械室 (Orange)
fig.add_shape(type="rect", x0=corridor_w, y0=corridor_w, x1=corridor_w + fwu_room_d, y1=h_w + corridor_w, 
              fillcolor="rgba(255, 165, 0, 0.3)", line=dict(color="orange"))
if cooling_type == "Dual Side Intake":
    fig.add_shape(type="rect", x0=offset_x + h_l, y0=corridor_w, x1=offset_x + h_l + fwu_room_d, y1=h_w + corridor_w, 
                  fillcolor="rgba(255, 165, 0, 0.3)", line=dict(color="orange"))

# 3. データホール本体 (White/LightGray)
fig.add_shape(type="rect", x0=offset_x, y0=offset_y, x1=offset_x + h_l, y1=offset_y + h_w, 
              fillcolor="rgba(240, 240, 240, 0.5)", line=dict(color="gray", dash="dot"))

# 4. ラック列とアイル (CAC構造)
curr_y = offset_y
for i in range(cold_aisles_qty):
    # Hot Aisle (Red)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + ha_w, 
                  fillcolor="rgba(255, 0, 0, 0.1)", line=dict(color="red", width=1))
    curr_y += ha_w
    # Rack Row A (Yellow)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + r_d, 
                  fillcolor="gold", line=dict(color="black", width=0.5))
    curr_y += r_d
    # Cold Aisle Containment (Cyan)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + ca_w, 
                  fillcolor="rgba(0, 255, 255, 0.3)", line=dict(color="blue", width=2))
    curr_y += ca_w
    # Rack Row B (Yellow)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + r_d, 
                  fillcolor="gold", line=dict(color="black", width=0.5))
    curr_y += r_d

# 5. FWU ユニットシンボル (Inside FWU Room)
fwu_qty_side = math.ceil(fwu_count / 2) if cooling_type == "Dual Side Intake" else fwu_count
for j in range(fwu_qty_side):
    y_pos = offset_y + (j * (h_w / fwu_qty_side))
    # Side A
    fig.add_shape(type="rect", x0=corridor_w + 1, y0=y_pos + 0.2, x1=corridor_w + 3, y1=y_pos + (h_w/fwu_qty_side) - 0.2, fillcolor="orange")
    # Side B
    if cooling_type == "Dual Side Intake":
        fig.add_shape(type="rect", x0=offset_x + h_l + 1, y0=y_pos + 0.2, x1=offset_x + h_l + 3, y1=y_pos + (h_w/fwu_qty_side) - 0.2, fillcolor="orange")

# --- 図面体裁 ---
fig.update_layout(
    xaxis=dict(title="Module Length (m)", scaleanchor="y", scaleratio=1),
    yaxis=dict(title="Module Width (m)"),
    width=1200, height=800, plot_bgcolor='white',
    title="Data Hall Strategic Layout (CAC Design Model)"
)

st.plotly_chart(fig, use_container_width=True)

# --- 解説パネル ---
st.info("💡 **Design Summary:** 黄色(Racks)はコールドアイル(水色:CAC)を挟んで対向配置。熱気は赤い領域(Hot Aisle)から天井リターンされ、オレンジの空調機械室へ戻ります。")
