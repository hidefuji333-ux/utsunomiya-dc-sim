import streamlit as st
import plotly.graph_objects as go
import math

# --- ページ基本設定 ---
st.set_page_config(page_title="Professional DC Design Tool", layout="wide")
st.title("🏙️ DC Strategic Module Designer: Pro-Edition")
st.markdown("---")

# --- サイドバー：設計変数（mm単位の精度） ---
with st.sidebar:
    st.header("1. Rack Configuration")
    rack_kw = st.number_input("IT Load per Rack (kW)", value=30.0, step=1.0)
    r_w = st.number_input("Rack Width (m)", value=0.6, step=0.1)
    r_d = st.number_input("Rack Depth (m)", value=1.2, step=0.1)
    racks_per_row = st.number_input("Racks per Row", value=20, step=1)
    cac_count = st.number_input("Number of Cold Aisles (CAC)", value=4, step=1)
    
    st.header("2. Aisle & Infrastructure (m)")
    ca_w = st.number_input("Cold Aisle Width (m)", value=1.8, step=0.1)
    ha_w = st.number_input("Hot Aisle Width (m)", value=1.2, step=0.1)
    corridor_w = st.number_input("Corridor Width (m)", value=2.4, step=0.1)
    fwu_depth = 4.0        
    
    st.header("3. Cooling Strategy")
    liquid_ratio = st.slider("DLC Ratio (%)", 0, 100, 30) / 100
    fwu_cap = st.number_input("FWU Capacity (kW/unit)", value=400)
    cooling_mode = st.selectbox("Cooling Path", ["Single Side", "Dual Side"])

# --- 演算ロジック ---
total_racks = int(racks_per_row * cac_count * 2)
it_kw = total_racks * rack_kw
air_load_kw = it_kw * (1.0 - liquid_ratio)
fwu_n = math.ceil(air_load_kw / fwu_cap) + 2

# 物理寸法
h_l = racks_per_row * r_w
h_w = (cac_count * 2 * r_d) + (cac_count * ca_w) + (cac_count * ha_w)
total_l = h_l + (fwu_depth * (2 if cooling_mode == "Dual Side" else 1)) + (corridor_w * 2)
total_w = h_w + (corridor_w * 2)

# --- 指標表示 ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total IT Load", f"{it_kw/1000:.2f} MW")
m2.metric("Total Racks", f"{total_racks} units")
m3.metric("Air Cooling Load", f"{air_load_kw/1000:.2f} MW")
m4.metric("Module Area", f"{total_l * total_w:.1f} m2")

# --- 高精細レイアウト描画 ---
fig = go.Figure()

# 基準座標
off_x = corridor_w + fwu_depth
off_y = corridor_w

# 1. 建築外郭と廊下 (Structure & Corridor)
fig.add_shape(type="rect", x0=0, y0=0, x1=total_l, y1=total_w, line=dict(color="#333", width=3), fillcolor="#fdfdfd")

# 2. 空調機械室 (FWU Room)
fig.add_shape(type="rect", x0=corridor_w, y0=off_y, x1=corridor_w + fwu_depth, y1=off_y + h_w, 
              fillcolor="rgba(255, 165, 0, 0.15)", line=dict(color="orange", width=1))
if cooling_mode == "Dual Side":
    fig.add_shape(type="rect", x0=off_x + h_l, y0=off_y, x1=off_x + h_l + fwu_depth, y1=off_y + h_w, 
                  fillcolor="rgba(255, 165, 0, 0.15)", line=dict(color="orange", width=1))

# 3. データホール床 (Data Hall)
fig.add_shape(type="rect", x0=off_x, y0=off_y, x1=off_x + h_l, y1=off_y + h_w, fillcolor="white", line=dict(color="#999", width=2))

# 4. ラック列とアイル (Segmented Layout)
curr_y = off_y
for i in range(cac_count):
    # Hot Aisle (Exhaust)
    fig.add_shape(type="rect", x0=off_x, y0=curr_y, x1=off_x + h_l, y1=curr_y + ha_w, 
                  fillcolor="rgba(255, 0, 0, 0.05)", line=dict(width=0))
    curr_y += ha_w
    
    # Rack Row A (Yellow & Segmented)
    for r in range(racks_per_row):
        fig.add_shape(type="rect", x0=off_x + (r * r_w), y0=curr_y, x1=off_x + ((r+1) * r_w), y1=curr_y + r_d,
                      fillcolor="#FFD700", line=dict(color="black", width=0.5))
    curr_y += r_d
    
    # Cold Aisle Containment (CAC)
    fig.add_shape(type="rect", x0=off_x, y0=curr_y, x1=off_x + h_l, y1=curr_y + ca_w, 
                  fillcolor="rgba(0, 200, 255, 0.25)", line=dict(color="blue", width=2))
    curr_y += ca_w
    
    # Rack Row B (Yellow & Segmented)
    for r in range(racks_per_row):
        fig.add_shape(type="rect", x0=off_x + (r * r_w), y0=curr_y, x1=off_x + ((r+1) * r_w), y1=curr_y + r_d,
                      fillcolor="#FFD700", line=dict(color="black", width=0.5))
    curr_y += r_d

# 5. FWU ユニットシンボル
fwu_per_side = math.ceil(fwu_n / 2) if cooling_mode == "Dual Side" else fwu_n
for k in range(fwu_per_side):
    y_u = off_y + (k * (h_w / fwu_per_side))
    h_u = (h_w / fwu_per_side) * 0.8
    fig.add_shape(type="rect", x0=corridor_w + 0.5, y0=y_u + (h_u*0.1), x1=corridor_w + 3.5, y1=y_pos_end := y_u + h_u, fillcolor="orange")
    if cooling_mode == "Dual Side":
        fig.add_shape(type="rect", x0=off_x + h_l + 0.5, y0=y_u + (h_u*0.1), x1=off_x + h_l + 3.5, y1=y_u + h_u, fillcolor="orange")

# --- 寸法線の追加 (Annotations) ---
dim_style = dict(showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="gray")
# ホール長さ
fig.add_annotation(x=off_x, y=off_y - 0.5, x2=off_x + h_l, y2=off_y - 0.5, text=f"{h_l:.1f}m", **dim_style)
# ホール幅
fig.add_annotation(x=off_x - 0.5, y=off_y, x2=off_x - 0.5, y2=off_y + h_w, text=f"{h_w:.1f}m", textangle=-90, **dim_style)
# 全体外寸
fig.add_annotation(x=0, y=total_w + 1, x2=total_l, y2=total_w + 1, text=f"Total Length: {total_l:.1f}m", **dim_style)

# --- 凡例設定 (Pseudo-legend via scatter) ---
legend_data = [
    ("Server Rack", "#FFD700"), ("Cold Aisle (CAC)", "blue"),
    ("Hot Aisle", "rgba(255, 0, 0, 0.2)"), ("FWU (Cooling Unit)", "orange"),
    ("FWU Mechanical Room", "rgba(255, 165, 0, 0.2)")
]
for name, color in legend_data:
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=15, color=color, symbol='square'), showlegend=True, name=name))

fig.update_layout(
    title=dict(text="Detailed DC Module Layout (Segmented Rack Model)", font=dict(size=24)),
    xaxis=dict(showgrid=False, zeroline=False, scaleanchor="y", scaleratio=1),
    yaxis=dict(showgrid=False, zeroline=False),
    plot_bgcolor='white', width=1200, height=900, legend=dict(yanchor="top", y=0.99, xanchor="right", x=1.2)
)

st.plotly_chart(fig, use_container_width=True)

# --- 寸法・構成リスト ---
st.subheader("📋 Modular Component Specifications")
spec_df = pd.DataFrame({
    "Component": ["Data Hall (Internal)", "FWU Room", "Perimeter Corridor", "Building Envelope"],
    "Length (m)": [h_l, fwu_depth, "-", total_l],
    "Width (m)": [h_w, h_w, corridor_w, total_w],
    "Area (m2)": [h_l*h_w, fwu_depth*h_w, "-", total_l*total_w]
})
st.table(spec_df)
