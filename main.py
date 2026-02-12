import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# ページ設定
st.set_page_config(page_title="DC設計・設備検証ツール", layout="wide")

st.title("🏗️ DCモジュール設計・設備容量検証ツール")

# --- サイドバー：入力パラメータ ---
with st.sidebar:
    st.header("1. IT・ラック構成")
    rack_kw = st.number_input("1ラックIT容量 (kW)", value=30.0)
    racks_per_row = st.number_input("1列のラック数", value=20)
    cold_aisles = st.number_input("コールドアイル数 (1CA=2列)", value=4)
    
    st.header("2. 空調・冷却スペック")
    liquid_ratio = st.slider("液冷(DLC)比率 (%)", 0, 100, 30) / 100
    fwu_cap = st.number_input("FWU1台の冷却能力 (kW)", value=400)
    fwu_pwr = st.number_input("FWU1台の消費電力 (kW)", value=15.0) # 空調自体の電力
    
    st.header("3. 電気設備スペック")
    ups_capacity_kva = st.number_input("UPS 1ユニット容量 (kVA)", value=1200)
    ups_pf = 0.9  # パワーファクター
    ups_n = st.number_input("UPSユニット数 (N)", value=4)
    ups_redundancy = st.selectbox("UPS冗長", ["N+1", "2N", "N"])
    
    gen_capacity_kva = st.number_input("発電機 1台容量 (kVA)", value=3000)
    gen_n = st.number_input("発電機台数", value=3)

# --- 計算ロジック ---
# IT負荷
total_racks = racks_per_row * cold_aisles * 2
total_it_kw = total_racks * rack_kw

# 空調負荷 (空冷が必要な分)
air_heat_load_kw = total_it_kw * (1 - liquid_ratio)
fwu_needed_qty = math.ceil(air_heat_load_kw / fwu_cap) + 2 # N+2
total_cooling_pwr_kw = fwu_needed_qty * fwu_pwr

# 総合負荷 (UPS/発電機用)
total_load_kw = total_it_kw + total_cooling_pwr_kw
total_load_kva = total_load_kw / ups_pf

# UPS検証
effective_ups_kva = ups_capacity_kva * (ups_n - (1 if ups_redundancy=="N+1" else 0))
if ups_redundancy == "2N": effective_ups_kva = (ups_capacity_kva * ups_n) / 2
ups_ok = effective_ups_kva >= (total_it_kw / ups_pf)

# 発電機検証
total_gen_kva = gen_capacity_kva * (gen_n - 1) # N+1想定
gen_ok = total_gen_kva >= total_load_kva

# --- ビジュアル表示 (平面図) ---
fig = go.Figure()

# データホール枠
fig.add_shape(type="rect", x0=0, y0=0, x1=50, y1=30, fillcolor="rgba(0,0,0,0)", line=dict(color="Black"))

# ラック列の描画 (ビジュアルイメージ)
for i in range(int(cold_aisles * 2)):
    color = "royalblue" if i % 2 == 0 else "indianred" # コールド/ホットのイメージ
    fig.add_shape(type="rect", x0=5, y0=5 + (i*2.5), x1=45, y1=6.5 + (i*2.5), fillcolor=color, opacity=0.6)

fig.update_layout(title="データホール・ラック配置イメージ", xaxis=dict(visible=False), yaxis=dict(visible=False), width=800, height=400)

# --- 結果表示 ---
st.header("📊 設備容量・バックアップ検証")
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("電力需要")
    st.write(f"IT負荷: **{total_it_mw := total_it_kw/1000:.2f} MW**")
    st.write(f"空調電力: **{total_cooling_pwr_kw:.1f} kW**")
    st.write(f"合計必要容量: **{total_load_kva:.1f} kVA**")

with c2:
    st.subheader("UPS検証")
    status_ups = "✅ 適合" if ups_ok else "❌ 不足"
    st.metric("UPS実効容量", f"{effective_ups_kva:,.0f} kVA", delta=status_ups)
    st.progress(min(1.0, (total_it_kw/ups_pf) / effective_ups_kva))

with c3:
    st.subheader("発電機検証")
    status_gen = "✅ 適合" if gen_ok else "❌ 不足"
    st.metric("発電機(N-1)容量", f"{total_gen_kva:,.0f} kVA", delta=status_gen)
    st.progress(min(1.0, total_load_kva / total_gen_kva))

st.plotly_chart(fig)

with st.expander("設計解説"):
    st.write(f"・液冷比率 {liquid_ratio*100}% により、空冷負荷を {air_heat_load_kw:.1f} kW まで削減。")
    st.write(f"・発電機はIT負荷だけでなく、空調機 {fwu_needed_qty} 台分の電力もカバーする設計としています。")
