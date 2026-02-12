import streamlit as st
import plotly.graph_objects as go
import math
import pandas as pd

# --- ページ基本設定 ---
st.set_page_config(page_title="DC Optimization Engine", layout="wide")
st.title("🏙️ DC Module Architecture Optimizer")
st.caption("UPS 7.2MW標準機軸の『建築×設備』整合性シミュレーター")

# --- サイドバー：基準設定 ---
with st.sidebar:
    st.header("⚡ 電力量の基準 (UPS)")
    ups_unit_mw = st.number_input("UPS単機容量 (MW)", value=2.4)
    ups_n = st.number_input("UPS台数 (3+1等の稼働台数N)", value=3)
    target_it_mw = ups_unit_mw * ups_n
    st.info(f"ターゲットIT容量: {target_it_mw:.1f} MW")

    st.header("❄️ 冷却スペック (FWU)")
    fwu_cap = st.number_input("FWU単機冷却能力 (kW)", value=420.0)
    fwu_w_unit = st.number_input("FWU1台の必要壁面幅 (m)", value=4.3)
    liquid_ratio = st.slider("DLC(液冷)比率 (%)", 0, 100, 30) / 100
    cooling_type = st.selectbox("空調配置", ["片面吹き", "両面吹き(対面)"])

    st.header("📦 ラック仕様")
    rack_kw = st.number_input("1ラック容量 (kW)", value=30.0)
    r_w, r_d = 0.6, 1.2
    ca_w, ha_w = 1.8, 1.6
    corridor_w = 3.0

# --- 最適化計算ロジック ---
# 1. 必要なラック総数
total_racks_needed = math.ceil((target_it_mw * 1000) / rack_kw)

# 2. 空調負荷と必要FWU数
air_load_kw = (target_it_mw * 1000) * (1.0 - liquid_ratio)
fwu_count = math.ceil(air_load_kw / fwu_cap) + 1 # N+1
total_fwu_width = fwu_count * fwu_w_unit
if cooling_type == "両面吹き(対面)":
    total_fwu_width /= 2

# 3. レイアウト探索 (6列の倍数で最適な1列台数を探す)
# ターゲット：データホールの長さ(racks * r_w) ≒ total_fwu_width
best_diff = float('inf')
best_racks_per_row = 0
best_rows = 0

for row_option in [6, 12, 18, 24]:
    racks_per_row_calc = math.ceil(total_racks_needed / row_option)
    hall_len = racks_per_row_calc * r_w
    diff = abs(hall_len - total_fwu_width)
    if diff < best_diff:
        best_diff = diff
        best_racks_per_row = racks_per_row_calc
        best_rows = row_option

# 最終確定値
h_l = best_racks_per_row * r_w
h_w = (best_rows * r_d) + (best_rows/2 * (ca_w + ha_w)) # 簡易計算
total_l = h_l + 4.0 + (corridor_w * 2) # 4.0はFWUヤード奥行
total_w = h_w + (corridor_w * 2)

# --- 表示エリア ---
c1, c2, c3 = st.columns(3)
c1.metric("IT Capacity", f"{target_it_mw:.1f} MW")
c2.metric("Rack Count", f"{best_racks_per_row}台 × {best_rows}列")
# 効率判定
space_match = (1 - (best_diff / h_l)) * 100
c3.metric("Space Efficiency", f"{space_match:.1f} %", help="FWU壁面幅とホール長の合致率")

# --- Plotly 描画 ---
fig = go.Figure()
# データホール
fig.add_shape(type="rect", x0=0, y0=0, x1=h_l, y1=h_w, line=dict(color="black", width=2))
# FWUヤード (オレンジ)
fig.add_shape(type="rect", x0=-4.0, y0=0, x1=0, y1=h_w, fillcolor="rgba(255,165,0,0.2)", line=dict(color="orange"))
# ラック列の描画 (簡易)
for r in range(best_rows):
    color = "gold"
    fig.add_shape(type="rect", x0=0, y0=r*2.5, x1=h_l, y1=r*2.5+r_d, fillcolor=color)

fig.update_layout(title="Optimal DH Layout: Space & Cooling Balanced", xaxis=dict(scaleanchor="y"), width=1000, height=600)
st.plotly_chart(fig)

# --- コンサルタントの深掘り質問 ---
st.markdown("---")
st.subheader("🧐 さらなる最適化のための深掘りポイント")
st.write("""
このロジックで「収まり」は見えましたが、実務上以下の点が「本当の悩み」に関わっていませんか？
1. **1列の最大台数制限**: ハイパースケーラーによって「1列は最大24台まで」等の制約がありますか？（現在は無制限に計算）
2. **FWUの『余り』の扱い**: FWU幅がホール長より短い場合、余った壁面をどう活用しますか？（電気室の拡張、予備スペースなど）
3. **DLCの熱回収**: 液冷分の30%〜の熱は、どの経路で外に逃がしますか？（水冷配管ルートの確保が必要）
""")
