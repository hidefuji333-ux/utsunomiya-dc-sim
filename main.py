import streamlit as st
import plotly.graph_objects as go
import math

# 1. ページ基本設定
st.set_page_config(page_title="DC設計・検証ツール", layout="wide")
st.title("🏛️ DCモジュール詳細設計・可視化シミュレーター")

# 2. 入力パラメータ (サイドバー)
with st.sidebar:
    st.header("1. IT・ラック構成")
    rack_kw = st.number_input("1ラックIT容量 (kW)", value=30.0)
    racks_per_row = st.number_input("1列のラック数", value=20)
    cold_aisles = st.number_input("コールドアイル数 (1CA=2列)", value=4)
    
    st.header("2. 物理寸法設定 (m)")
    r_w, r_d = 0.6, 1.2    # ラック寸法
    ca_w, ha_w = 1.8, 1.2  # 通路幅
    corridor_w = 2.4       # 外周廊下幅
    
    st.header("3. 冷却システム")
    liquid_ratio = st.slider("DLC(液冷)比率 (%)", 0, 100, 30) / 100
    fwu_cap = st.number_input("FWU1台の冷却能力 (kW)", value=400)
    fwu_pwr = st.number_input("FWU1台の消費電力 (kW)", value=15.0)
    fwu_depth = 2.0        # FWUの設置スペース奥行
    cooling_type = st.selectbox("空調配置", ["片面吹き", "両面吹き(対面)"])

    st.header("4. 電気設備スペック")
    gen_cap = st.number_input("発電機 1台容量 (kVA)", value=3000)
    gen_n = st.number_input("発電機台数 (N-1想定)", value=3)

# 3. 計算ロジック
total_racks = int(racks_per_row * cold_aisles * 2)
it_kw = float(total_racks * rack_kw)
air_load_kw = it_kw * (1.0 - liquid_ratio)
fwu_count = math.ceil(air_load_kw / fwu_cap) + 2
total_load_kva = (it_kw + (fwu_count * fwu_pwr)) / 0.9

# 4. 指標表示
c1, c2, c3, c4 = st.columns(4)
c1.metric("総IT容量", f"{it_kw/1000:.2f} MW")
c2.metric("空冷負荷", f"{air_load_kw/1000:.2f} MW")
c3.metric("FWU必要台数", f"{fwu_count} 台")
gen_ok = total_load_kva <= (gen_cap * (gen_n - 1))
c4.metric("発電機判定", "✅ 適合" if gen_ok else "❌ 不足")

# 5. レイアウト描画
fig = go.Figure()

# ホール寸法計算
h_l = racks_per_row * r_w
h_w = (cold_aisles * 2 * r_d) + (cold_aisles * (ca_w + ha_w))

# 全体外寸
total_box_l = h_l + (fwu_depth * (2 if cooling_type=="両面吹き(対面)" else 1)) + (corridor_w * 2)
total_box_w = h_w + (corridor_w * 2)

# 外枠
fig.add_shape(type="rect", x0=0, y0=0, x1=total_box_l, y1=total_box_w, line=dict(color="black"))

# 配置オフセット
offset_x = corridor_w + fwu_depth
offset_y = corridor_w

# アイル・ラックのループ描画
curr_y = offset_y
for i in range(int(cold_aisles)):
    # ホットアイル (赤)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x+h_l, y1=curr_y+ha_w, fillcolor="rgba(255,0,0,0.1)", line=dict(color="red"))
    curr_y += ha_w
    # ラック列1 (黄)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x+h_l, y1=curr_y+r_d, fillcolor="gold", line=dict(color="orange"))
    curr_y += r_d
    # コールドアイル (水色)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x+h_l, y1=curr_y+ca_w, fillcolor="rgba(0,255,255,0.1)", line=dict(color="deepskyblue"))
    curr_y += ca_w
    # ラック列2 (黄)
    fig.add_shape(type="rect", x0=offset_x, y0=curr_y, x1=offset_x+h_l, y1=curr_y+r_d, fillcolor="gold", line=dict(color="orange"))
    curr_y += r_d

# FWUの配置
qty_side = math.ceil(fwu_count / 2) if cooling_type == "両面吹き(対面)" else fwu_count
for j in range(qty_side):
    y_p = offset_y + (j * (h_w / qty_side))
    h_unit = (h_w / qty_side) * 0.8
    # 左側
    fig.add_shape(type="rect", x0=corridor_w, y0=y_p, x1=corridor_w+fwu_depth, y1=y_p+h_unit, fillcolor="orange")
    # 右側 (対面時)
    if cooling_type == "両面吹き(対面)":
        fig.add_shape(type="rect", x0=offset_x+h_l, y0=y_p, x1=offset_x+h_l+fwu_depth, y1=y_p+h_unit, fillcolor="orange")

fig.update_layout(xaxis=dict(scaleanchor="y", scaleratio=1), width=1000, height=800, plot_bgcolor='white')
st.plotly_chart(fig, use_container_width=True)
st.info("黄色:ラック / 水色:コールドアイル / 赤:ホットアイル / 橙:空調機")
