import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# ページ設定
st.set_page_config(page_title="DC設計・設備検証ツール", layout="wide")

st.title("🏗️ DCモジュール設計・詳細可視化ツール")

# --- サイドバー：入力パラメータ ---
with st.sidebar:
    st.header("1. IT・ラック構成")
    rack_kw = st.number_input("1ラックIT容量 (kW)", value=30.0)
    racks_per_row = st.number_input("1列のラック数", value=20)
    cold_aisles = st.number_input("コールドアイル数 (1CA=2列)", value=4)
    
    st.header("2. 空間・冷却設計")
    ca_width = st.number_input("コールドアイル幅 (m)", value=1.8)
    ha_width = st.number_input("ホットアイル幅 (m)", value=1.2)
    liquid_ratio = st.slider("液冷(DLC)比率 (%)", 0, 100, 30) / 100
    fw_side = st.selectbox("空調配置", ["片側配置", "対面配置"])
    fwu_cap = st.number_input("FWU1台の冷却能力 (kW)", value=400)
    fwu_pwr = st.number_input("FWU1台の消費電力 (kW)", value=15.0) 
    
    st.header("3. 電気設備スペック")
    ups_capacity_kva = st.number_input("UPS 1ユニット容量 (kVA)", value=1200)
    ups_n = st.number_input("UPSユニット数 (N)", value=4)
    ups_redundancy = st.selectbox("UPS冗長方式", ["N+1", "2N", "N単独"])
    
    gen_capacity_kva = st.number_input("発電機 1台容量 (kVA)", value=3000)
    gen_n = st.number_input("発電機台数", value=3)

# --- 計算ロジック ---
total_racks = int(racks_per_row * cold_aisles * 2)
total_it_kw = float(total_racks * rack_kw)
total_it_mw = total_it_kw / 1000.0

# 空調負荷計算
air_heat_load_kw = total_it_kw * (1.0 - liquid_ratio)
fwu_needed_qty = math.ceil(air_heat_load_kw / fwu_cap) + 2 # N+2
total_cooling_pwr_kw = fwu_needed_qty * fwu_pwr

# 設備検証(UPS/GEN)
ups_pf = 0.9
total_load_kva = (total_it_kw + total_cooling_pwr_kw) / ups_pf
if ups_redundancy == "N+1": effective_ups_kva = ups_capacity_kva * (ups_n - 1)
elif ups_redundancy == "2N": effective_ups_kva = (ups_capacity_kva * ups_n) / 2
else: effective_ups_kva = ups_capacity_kva * ups_n
ups_ok = (total_it_kw / ups_pf) <= effective_ups_kva
gen_ok = (gen_capacity_kva * (gen_n - 1)) >= total_load_kva

# --- ビジュアル表示 (平面図) ---
fig = go.Figure()

# 寸法設定
r_w, r_d = 0.6, 1.2
hall_length = racks_per_row * r_w
hall_width = (cold_aisles * 2 * r_d) + (cold_aisles * ca_width) + (cold_aisles * ha_width)

# 1. データホール外枠
fig.add_shape(type="rect", x0=0, y0=0, x1=hall_length, y1=hall_width, line=dict(color="black", width=3), fillcolor="white")

# 2. アイルとラック列の描画
current_y = 0
for i in range(int(cold_aisles)):
    # ホットアイル(HA)領域
    fig.add_shape(type="rect", x0=0, y0=current_y, x1=hall_length, y1=current_y + ha_width, fillcolor="rgba(255,0,0,0.1)", line_width=0)
    current_y += ha_width
    
    # ラック列1 (Hot側)
    fig.add_shape(type="rect", x0=0, y0=current_y, x1=hall_length, y1=current_y + r_d, fillcolor="red", opacity=0.8)
    current_y += r_d
    
    # コールドアイル(CA)領域
    fig.add_shape(type="rect", x0=0, y0=current_y, x1=hall_length, y1=current_y + ca_width, fillcolor="rgba(0,0,255,0.1)", line_width=0)
    current_y += ca_width
    
    # ラック列2 (Cold側)
    fig.add_shape(type="rect", x0=0, y0=current_y, x1=hall_length, y1=current_y + r_d, fillcolor="blue", opacity=0.8)
    current_y += r_d

# 3. Fan Wall Unit (FWU) の描画
fwu_visual_w = 2.0
if fw_side == "対面配置":
    qty_per_side = math.ceil(fwu_needed_qty / 2)
    sides = [(-2.5, -0.5), (hall_width + 0.5, hall_width + 2.5)]
else:
    qty_
