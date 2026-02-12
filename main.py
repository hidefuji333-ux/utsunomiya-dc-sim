import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

# --- ページ基本設定 ---
st.set_page_config(page_title="Strategic DC Designer Pro", layout="wide")
st.title("🏙️ Strategic DC Module Designer & Validator")
st.markdown("---")

# --- サイドバー：設計変数（Design Parameters） ---
with st.sidebar:
    st.header("1. Rack & Aisle Specs")
    rack_kw = st.number_input("IT Load per Rack (kW)", value=30.0, step=1.0)
    racks_per_row = st.number_input("Racks per Row", value=20, step=1)
    cac_count = st.number_input("Number of Cold Aisles (CAC)", value=4, step=1)
    
    st.header("2. Architecture (m)")
    r_w, r_d = 0.6, 1.2    # Rack Dimensions
    ca_w, ha_w = 1.8, 1.2  # Aisle Widths
    corridor_w = 2.4       # Minimum Corridor [cite: 141]
    fwu_depth = 4.0        # FWU Room Depth
    
    st.header("3. Cooling & DLC")
    liquid_ratio = st.slider("DLC Ratio (%)", 0, 100, 30) / 100
    fwu_cap = st.number_input("FWU Capacity (kW/unit)", value=400)
    cooling_mode = st.selectbox("Cooling Path", ["Single Side", "Dual Side"])

    st.header("4. Power Infrastructure")
    gen_cap = st.number_input("Generator Unit (kVA)", value=3000)
    gen_n = st.number_input("Gen Count (N-1)", value=4)

# --- ロジック演算 ---
total_racks = racks_per_row * cac_count * 2
it_kw = total_racks * rack_kw
air_load_kw = it_kw * (1.0 - liquid_ratio)
fwu_n = math.ceil(air_load_kw / fwu_cap) + 2 # N+2 redundancy

# 設備負荷率計算
total_kva = (it_kw + (fwu_n * 15.0)) / 0.9 # Power factor 0.9
eff_gen_kva = gen_cap * (gen_n - 1)
gen_load_factor = (total_kva / eff_gen_kva) * 100 if eff_gen_kva > 0 else 0

# --- メトリクス・ダッシュボード ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total IT Capacity", f"{it_kw/1000:.2f} MW")
with c2:
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = gen_load_factor,
        title = {'text': "Generator Load Factor (%)"},
        gauge = {'axis': {'range': [0, 120]},
                 'bar': {'color': "darkblue"},
                 'steps': [{'range': [0, 80], 'color': "lightgreen"},
                          {'range': [80, 100], 'color': "orange"},
                          {'range': [100, 120], 'color': "red"}]}))
    fig_gauge.update_layout(height=250, margin=dict(t=0, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)
with c3:
    st.metric("Required FWU Units", f"{fwu_n} (N+2)")

# --- 高精細レイアウト描画 ---
h_l = racks_per_row * r_w
h_w = (cac_count * 2 * r_d) + (cac_count * ca_w) + (cac_count * ha_w)
offset_x = corridor_w + fwu_depth
offset_y = corridor_w

fig_layout = go.Figure()

# 1. 建築外郭 (Structure Outer Line)
fig_layout.add_shape(type="rect", x0=0, y0=0, x1=h_l + (fwu_depth * 2) + (corridor_w * 2), y1=h_w + (corridor_w * 2),
                     line=dict(color="#333", width=4), fillcolor="#f8f9fa")

# 2. 空調機械室 (FWU Corridor)
fig_layout.add_shape(type="rect", x0=corridor_w, y0=corridor_w, x1=corridor_w + fwu_depth, y1=h_w + corridor_w,
                     fillcolor="rgba(255, 165, 0, 0.2)", line=dict(color="orange", width=1))
if cooling_mode == "Dual Side":
    fig_layout.add_shape(type="rect", x0=offset_x + h_l, y0=corridor_w, x1=offset_x + h_l + fwu_depth, y1=h_w + corridor_w,
                         fillcolor="rgba(255, 165, 0, 0.2)", line=dict(color="orange", width=1))

# 3. データホール (Data Hall Floor)
fig_layout.add_shape(type="rect", x0=offset_x, y0=offset_y, x1=offset_x + h_l, y1=offset_y + h_w,
                     fillcolor="white", line=dict(color="#999", width=2))

# 4. ラック・アイル列 (Engineering Layout)
curr_y = offset_y
for i in range(cac_count):
    # Hot Aisle (Exhaust)
    fig_layout.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + ha_w,
                         fillcolor="rgba(255, 0, 0, 0.05)", line=dict(width=0))
    curr_y += ha_w
    # Rack Row A (Yellow)
    fig_layout.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + r_d,
                         fillcolor="#FFD700", line=dict(color="#444", width=1))
    curr_y += r_d
    # Cold Aisle Containment (CAC - Cyan)
    fig_layout.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + ca_w,
                         fillcolor="rgba(0, 200, 255, 0.3)", line=dict(color="blue", width=2))
    curr_y += ca_w
    # Rack Row B (Yellow)
    fig_layout.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x + h_l, y1=curr_y + r_d,
                         fillcolor="#FFD700", line=dict(color="#444", width=1))
    curr_y += r_d

# 5. FWU ユニット配置 (Equipment Symbols)
fwu_per_side = math.ceil(fwu_n / 2) if cooling_mode == "Dual Side" else fwu_n
for k in range(fwu_per_side):
    y_unit = offset_y + (k * (h_w / fwu_per_side))
    fig_layout.add_shape(type="rect", x0=corridor_w + 0.5, y0=y_unit + 0.2, x1=corridor_w + 3.5, y1=y_unit + (h_w/fwu_per_side) - 0.2,
                         fillcolor="orange", line=dict(color="darkorange"))
    if cooling_mode == "Dual Side":
        fig_layout.add_shape(type="rect", x0=offset_x + h_l + 0.5, y0=y_unit + 0.2, x1=offset_x + h_l + 3.5, y1=y_unit + (h_w/fwu_per_side) - 0.2,
                             fillcolor="orange", line=dict(color="darkorange"))

# 図面体裁の調整
fig_layout.update_layout(
    title=dict(text="DC Master Plan: Module Layout Analysis (CAC & FWU Architecture)", font=dict(size=24)),
    xaxis=dict(title="Length (m)", gridcolor="#eee", scaleanchor="y", scaleratio=1),
    yaxis=dict(title="Width (m)", gridcolor="#eee"),
    plot_bgcolor='white', width=1200, height=800,
    margin=dict(l=50, r=50, t=100, b=50)
)

st.plotly_chart(fig_layout, use_container_width=True)

# --- 技術解説 ---
with st.expander("📝 Engineering Notes & References"):
    st.write(f"・**CAC (Cold Aisle Containment)**: 青色のゾーンは密閉された冷気供給路です。これによりPUEを低減します。")
    st.write(f"・**Generator Validation**: IT負荷 {it_kw:.0f}kW と空調負荷を合算し、N-1構成での安全性 {eff_gen_kva:.0f}kVA を検証しています。")
    st.write(f"・**Road & Access**: 外周には2.4mの廊下(Corridor)を確保し、大規模メンテナンスに対応可能な設計としています [cite: 141]。")
