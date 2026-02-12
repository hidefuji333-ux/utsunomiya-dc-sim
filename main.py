import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# 1. ページ基本設定
st.set_page_config(page_title="DC設計・検証ツール", layout="wide")
st.title("🏗️ DCモジュール設計・設備容量検証ツール")

# 2. 入力パラメータ (サイドバー)
with st.sidebar:
    st.header("1. IT・ラック構成")
    rack_kw = st.number_input("1ラックIT容量 (kW)", value=30.0)
    racks_per_row = st.number_input("1列のラック数", value=20)
    cold_aisles = st.number_input("コールドアイル数 (1CA=2列)", value=4)
    
    st.header("2. 空間・冷却設計")
    ca_w, ha_w = 1.8, 1.2 # 通路幅固定
    liquid_ratio = st.slider("液冷(DLC)比率 (%)", 0, 100, 30) / 100
    fwu_cap = st.number_input("FWU1台の冷却能力 (kW)", value=400)
    fwu_pwr = st.number_input("FWU1台の消費電力 (kW)", value=15.0) 
    
    st.header("3. 電気設備スペック")
    ups_cap = st.number_input("UPS 1台容量 (kVA)", value=1200)
    ups_n = st.number_input("UPS台数", value=4)
    gen_cap = st.number_input("発電機 1台容量 (kVA)", value=3000)
    gen_n = st.number_input("発電機台数", value=3)

# 3. 計算ロジック
total_racks = int(racks_per_row * cold_aisles * 2)
it_kw = float(total_racks * rack_kw)
# 空調計算
air_load_kw = it_kw * (1.0 - liquid_ratio)
fwu_count = math.ceil(air_load_kw / fwu_cap) + 2 # N+2
total_load_kva = (it_kw + (fwu_count * fwu_pwr)) / 0.9

# 設備検証
ups_ok = (it_kw / 0.9) <= (ups_cap * (ups_n - 1)) # N+1想定
gen_ok = total_load_kva <= (gen_cap * (gen_n - 1)) # N-1想定

# 4. 指標表示
c1, c2, c3 = st.columns(3)
c1.metric("総IT容量", f"{it_kw/1000:.2f} MW")
c2.metric("UPS検証", "✅ 適合" if ups_ok else "❌ 不足")
c3.metric("発電機検証", "✅ 適合" if gen_ok else "❌ 不足")

# 5. レイアウト描画 (Plotly)
fig = go.Figure()
r_w, r_d = 0.6, 1.2
h_l, h_w = racks_per_row * r_w, (cold_aisles * 2 * r_d) + (cold_aisles * (ca_w + ha_w))

# ホール外枠
fig.add_shape(type="rect", x0=0, y0=0, x1=h_l, y1=h_w, line=dict(color="black", width=2))

# アイル・ラック列描画
curr_y = 0
for i in range(int(cold_aisles)):
    fig.add_shape(type="rect", x0=0, y0=curr_y, x1=h_l, y1=curr_y+ha_w, fillcolor="rgba(255,0,0,0.1)", line_width=0)
    curr_y += ha_w
    fig.add_shape(type="rect", x0=0, y0=curr_y, x1=h_l, y1=curr_y+r_d, fillcolor="red", opacity=0.7)
    curr_y += r_d
    fig.add_shape(type="rect", x0=0, y0=curr_y, x1=h_l, y1=curr_y+ca_w, fillcolor="rgba(0,0,255,0.1)", line_width=0)
    curr_y += ca_w
    fig.add_shape(type="rect", x0=0, y0=curr_y, x1=h_l, y1=curr_y+r_d, fillcolor="blue", opacity=0.7)
    curr_y += r_d

# FWU描画
for j in range(fwu_count):
    x_p = (h_l / fwu_count) * j
    fig.add_shape(type="rect", x0=x_p, y0=-2, x1=x_p+(h_l/fwu_count*0.8), y1=-0.5, fillcolor="orange")

fig.update_layout(title="平面図イメージ (赤:排気 / 青:吸気 / 橙:空調機)", xaxis=dict(range=[-2, h_l+2]), yaxis=dict(range=[-3, h_w+2], scaleanchor="x"), width=900, height=600)
st.plotly_chart(fig, use_container_width=True)
