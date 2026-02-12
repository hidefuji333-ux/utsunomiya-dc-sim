import streamlit as st
import plotly.graph_objects as go
import math
import pandas as pd

# 1. ページ基本設定
st.set_page_config(page_title="Professional DC Design Tool", layout="wide")
st.title("🏙️ DC Strategic Module Designer: Pro-Edition")
st.markdown("---")

# 2. 入力パラメータ (サイドバー)
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

# 3. 計算ロジック
total_racks = int(racks_per_row * cac_count * 2)
it_kw = float(total_racks * rack_kw)
air_load_kw = it_kw * (1.0 - liquid_ratio)
fwu_n = math.ceil(air_load_kw / fwu_cap) + 2

# 物理寸法
h_l = racks_per_row * r_w
h_w = (cac_count * 2 * r_d) + (cac_count * ca_w) + (cac_count * ha_w)
total_l = h_l + (fwu_depth * (2 if cooling_mode == "Dual Side" else 1)) + (corridor_w * 2)
total_w = h_w + (corridor_w * 2)

# 4. 指標表示
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total IT Load", f"{it_kw/1000:.2f} MW")
m2.metric("Total Racks", f"{total_racks} units")
m3.metric("Air Cooling Load", f"{air_load_kw/1000:.2f} MW")
m4.metric("Module Area", f"{total_l * total_w:.1f} m2")

# 5. 高精細レイアウト描画 (Plotly)
fig = go.Figure()
off_x = corridor_w + fwu_depth
off_y = corridor_w

# 5a. 建築外郭
fig.add_shape(type="rect", x0=0, y0=0, x1=total_l, y1=total_w, line=dict(color="#333", width=3), fillcolor="#fdfdfd")

# 5b. 空調機械室 (Orange)
fig.add_shape(type="rect", x0=corridor_w, y0=off_y, x1=corridor_w + fwu_depth, y1=off_y + h_w, 
              fillcolor="rgba(255, 165, 0, 0.15)", line=dict(color="orange", width=1))
if cooling_mode == "Dual Side":
    fig.add_shape(type="rect", x0=off_x + h_l, y0=off_y, x1=off_x + h_l + fwu_depth, y1=off_y + h_w, 
                  fillcolor="rgba(255, 165, 0, 0.15)", line=dict(color="orange", width=1))

# 5c. アイル・ラック列 (1ラックごとに描画)
curr_y = off_y
for i in range(cac_count):
    # Hot Aisle (Red)
    fig.add_shape(type="rect", x0=off_x, y0=curr_y, x1=off_x + h_l, y1=curr_y + ha_w, 
                  fillcolor="rgba(255, 0, 0, 0.05)", line=dict(width=0))
    curr_y += ha_w
    # Rack Row A (Yellow Segmented)
    for r in range(racks_per_row):
        fig.add_shape(type="rect", x0=off_x + (r * r_w), y0=curr_y, x1=off_x + ((r+1) * r_w), y1
