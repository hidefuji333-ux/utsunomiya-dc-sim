import streamlit as st
import plotly.graph_objects as go
import math
import pandas as pd

# 1. ページ基本設定
st.set_page_config(page_title="Strategic DC Designer Pro", layout="wide")
st.title("🏛️ Strategic DC Module Optimizer")
st.markdown("---")

# 2. 入力パラメータ (エクセル資料の値を初期値に設定)
with st.sidebar:
    st.header("⚡ IT & Power (UPS Standard)")
    ups_unit_mw = st.number_input("UPS Unit Cap (MW)", value=2.4)
    ups_n = st.number_input("UPS Units (N for IT)", value=3)
    target_it_mw = ups_unit_mw * ups_n
    
    st.header("📦 Rack Layout")
    rack_kw = st.number_input("IT Load per Rack (kW)", value=30.0)
    r_w, r_d = 0.6, 1.2
    # エクセル資料のラック台数（24台）と列数（12列）を初期値に
    racks_per_row = st.number_input("Racks per Row", value=24)
    # 6の倍数での選択を推奨
    row_count = st.selectbox("Total Rows (Multiples of 6)", [6, 12, 18, 24], index=1)
    
    st.header("❄️ Cooling (FWU Spec)")
    fwu_cap = st.number_input("FWU Capacity (kW/unit)", value=420.0)
    fwu_w_unit = st.number_input("FWU Wall Width per Unit (m)", value=4.3)
    liquid_ratio = st.slider("DLC Ratio (%)", 0, 100, 30) / 100
    cooling_mode = st.selectbox("Cooling Layout", ["Single Side (片面)", "Dual Side (両面)"])
    
    st.header("📐 Infrastructure (m)")
    ca_w, ha_w = 1.8, 1.6
    corridor_w = 3.0
    fwu_yard_d = 4.0

# 3. 計算ロジック (設計整合性の検証)
total_racks = racks_per_row * row_count
calc_it_mw = (total_racks * rack_kw) / 1000.0

# 空調機(FWU)の必要台数
air_load_kw = (calc_it_mw * 1000) * (1.0 - liquid_ratio)
fwu_n = math.ceil(air_load_kw / fwu_cap) + 1 # N+1 redundancy
total_fwu_wall_needed = fwu_n * fwu_w_unit

# 物理寸法
h_l = racks_per_row * r_w
# 1ペア = (r_d * 2) + ca_w + ha_w
pair_count = row_count / 2
h_w = (r_d * row_count) + (pair_count * ca_w) + ((pair_count - 1) * ha_w)

# 4. 指標表示 (エクセルとの整合性チェック)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current IT Load", f"{calc_it_mw:.2f} MW", delta=f"{calc_it_mw - target_it_mw:.2f} MW vs Target")
m2.metric("Required FWU Wall", f"{total_fwu_wall_needed:.1f} m")
# 空調壁面とホール幅の整合性
wall_avail = h_w if cooling_mode == "Single Side (片面)" else h_w * 2
match_score = (wall_avail / total_fwu_wall_needed) * 100
m3.metric("Wall Space Match", f"{match_score:.1f} %", delta="OK" if match_score >= 100 else "Insufficient")
m4.metric("Total Racks", f"{total_racks} Units")

# 5. 高精細プロフェッショナル描画 (Plotly)
fig = go.Figure()
off_x, off_y = corridor_w + fwu_yard_d, corridor_w
total_l = h_l + (fwu_yard_d * (2 if cooling_mode == "Dual Side (両面)" else 1)) + (corridor_w * 2)
total_w = h_w + (corridor_w * 2)

# 建築外郭
fig.add_shape(type="rect", x0=0, y0=0, x1=total_l, y1=total_w, line=dict(color="#333", width=3), fillcolor="#fdfdfd")

# 空調機械室 (Orange)
fig.add_shape(type="rect", x0=corridor_w, y0=off_y, x1=corridor_w + fwu_yard_d, y1=off_y + h_w, 
              fillcolor="rgba(255, 165, 0, 0.15)", line=dict(color="orange", width=1))
if cooling_mode == "Dual Side (両面)":
    fig.add_shape(type="rect", x0=off_x + h_l, y0=off_y, x1=off_x + h_l + fwu_yard_d, y1=off_y + h_w, 
                  fillcolor="rgba(255, 165, 0, 0.15)", line=dict(color="orange", width=1))

# アイル・ラック列描画 (1ラックずつセグメント化)
curr_y = off_y
for i in range(int(pair_count)):
    # Hot Aisle (Red)
    if i > 0:
        fig.add_shape(type="rect", x0=off_x, y0=curr_y, x1=off_x + h_l, y1=curr_y + ha_w, 
                      fillcolor="rgba(255, 0, 0, 0.05)", line_width=0)
        curr_y += ha_w
    
    # Rack Row 1 (Yellow)
    for r in range(racks_per_row):
        fig.add_shape(type="rect", x0=off_x + (r * r_w), y0=curr_y, x1=off_x + ((r+1) * r_w), y1=curr_y + r_d,
                      fillcolor="#FFD700", line=dict(color="black", width=0.5))
    curr_y += r_d
    
    # Cold Aisle (CAC Blue)
    fig.add_shape(type="rect", x0=off_x, y0=curr_y, x1=off_x + h_l, y1=curr_y + ca_w, 
                  fillcolor="rgba(0, 200, 255, 0.25)", line=dict(color="blue", width=2))
    curr_y += ca_w
    
    # Rack Row 2 (Yellow)
    for r in range(racks_per_row):
        fig.add_shape(type="rect", x0=off_x + (r * r_w), y0=curr_y, x1=off_x + ((r+1) * r_w), y1=curr_y + r_d,
                      fillcolor="#FFD700", line=dict(color="black", width=0.5))
    curr_y += r_d

# FWUユニット描画
fwu_per_side = math.ceil(fwu_n / 2) if cooling_mode == "Dual Side (両面)" else fwu_n
for k in range(fwu_per_side):
    y_u = off_y + (k * (h_w / fwu_per_side))
    h_unit = (h_w / fwu_per_side) * 0.8
    fig.add_shape(type="rect", x0=corridor_w + 0.5, y0=y_u + (h_unit*0.1), x1=corridor_w + 3.5, y1=y_u + h_unit, fillcolor="orange")
    if cooling_mode == "Dual Side (両面)":
        fig.add_shape(type="rect", x0=off_x + h_l + 0.5, y0=y_u + (h_unit*0.1), x1=off_x + h_l + 3.5, y1=y_u + h_unit, fillcolor="orange")

# 寸法線
fig.add_annotation(x=off_x + h_l/2, y=off_y - 1.5, text=f"L: {h_l:.1f}m", showarrow=False)
fig.add_annotation(x=off_x - 1.5, y=off_y + h_w/2, text=f"W: {h_w:.1f}m", textangle=-90, showarrow=False)

# 凡例
legend_labels = [("Server Rack", "#FFD700"), ("Cold Aisle (CAC)", "blue"), ("Hot Aisle", "rgba(255, 0, 0, 0.2)"), ("FWU Unit", "orange")]
for name, color in legend_labels:
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color=color, symbol='square'), showlegend=True, name=name))

fig.update_layout(title="DC Strategic Module Optimizer (CAC Model)", xaxis=dict(scaleanchor="y"), plot_bgcolor='white', width=1100, height=800)
st.plotly_chart(fig, use_container_width=True)

# 6. 設計サマリーテーブル
st.subheader("📋 Engineering Design Summary")
summary_data = {
    "項目": ["IT合計出力 (MW)", "ラック総数 (台)", "必要FWU台数 (N+1)", "必要FWU壁面長 (m)", "データホール面積 (m2)"],
    "シミュレーション結果": [f"{calc_it_mw:.2f}", total_racks, fwu_n, f"{total_fwu_wall_needed:.1f}", f"{h_l * h_w:.1f}"]
}
st.table(pd.DataFrame(summary_data))
