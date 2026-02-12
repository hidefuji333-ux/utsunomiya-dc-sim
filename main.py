import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# ページ設定
st.set_page_config(page_title="DCモジュール最適化ツール", layout="wide")

st.title("🏛️ DCモジュール設計・可視化シミュレーター")
st.caption("高密度・次世代AI対応データセンターの基本設計支援ツール")

# --- サイドバー：変数入力 ---
with st.sidebar:
    st.header("1. ラック・アイル構成")
    rack_kw = st.number_input("ラックIT容量 (kW/台)", value=30.0)
    rack_w = st.number_input("ラック幅 (m)", value=0.6)
    rack_d = st.number_input("ラック奥行 (m)", value=1.2)
    racks_per_row = st.number_input("1列のラック数", value=20)
    cold_aisles = st.number_input("コールドアイル数 (1CA=2列)", value=4)
    
    st.header("2. 空間・冷却設計")
    ca_width = st.number_input("コールドアイル幅 (m)", value=1.8)
    ha_width = st.number_input("ホットアイル幅 (m)", value=1.2)
    corridor = st.number_input("外周廊下幅 (m)", value=2.4)
    cooling_type = st.selectbox("空調配置方式", ["片側吹き (Single Side)", "対面吹き (Dual Side)"])
    fwu_d = st.number_input("空調機械室(FWU)奥行 (m)", value=4.0)
    liquid_ratio = st.slider("液冷(DLC)比率 (%)", 0, 100, 30) / 100

# --- 計算ロジック ---
rows = cold_aisles * 2
total_racks = racks_per_row * rows
total_it_mw = (total_racks * rack_kw) / 1000

# データホール内寸（ラック領域のみ）
inner_length = (racks_per_row * rack_w) 
inner_width = (rows * rack_d) + (cold_aisles * ca_width) + (cold_aisles * ha_width)

# 全体外寸の計算（廊下と空調室を含む）
if cooling_type == "対面吹き (Dual Side)":
    total_length = inner_length + (fwu_d * 2) + (corridor * 2)
    fwu_left_x = corridor
    hall_start_x = corridor + fwu_d
    fwu_right_x = total_length - corridor - fwu_d
else:
    total_length = inner_length + fwu_d + (corridor * 2)
    fwu_left_x = corridor
    hall_start_x = corridor + fwu_d

total_width = inner_width + (corridor * 2)
total_area = total_length * total_width

# --- ビジュアル描画 (Plotly) ---
fig = go.Figure()

# 1. モジュール全体の枠（外壁）
fig.add_shape(type="rect", x0=0, y0=0, x1=total_length, y1=total_width, 
              line=dict(color="Black", width=3), fillcolor="White")

# 2. データホールエリア (青色)
fig.add_shape(type="rect", x0=hall_start_x, y0=corridor, 
              x1=hall_start_x + inner_length, y1=corridor + inner_width, 
              fillcolor="rgba(0, 176, 246, 0.2)", line=dict(color="Blue", width=2))

# 3. 空調機械室 (オレンジ色)
# 左側（または片側）
fig.add_shape(type="rect", x0=fwu_left_x, y0=corridor, x1=fwu_left_x + fwu_d, y1=total_width - corridor, 
              fillcolor="rgba(255, 127, 14, 0.5)", line=dict(color="Orange", width=1))
# 右側（対面の場合）
if cooling_type == "対面吹き (Dual Side)":
    fig.add_shape(type="rect", x0=fwu_right_x, y0=corridor, x1=fwu_right_x + fwu_d, y1=total_width - corridor, 
                  fillcolor="rgba(255, 127, 14, 0.5)", line=dict(color="Orange", width=1))

# レイアウト設定
fig.update_layout(
    title="モジュール簡易平面図 (Top View)",
    xaxis=dict(title="長さ (m)", showgrid=True, zeroline=False),
    yaxis=dict(title="幅 (m)", showgrid=True, zeroline=False, scaleanchor="x", scaleratio=1),
    width=900, height=600,
    plot_bgcolor='white'
)

# --- 表示エリア ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 主要メトリクス")
    st.metric("総IT容量", f"{total_it_mw:.2f} MW")
    st.metric("モジュール総面積", f"{total_area:.1f} ㎡")
    st.write(f"**総ラック数:** {total_racks} 台")
    st.write(f"**建物外寸:** {total_length:.1f}m × {total_width:.1f}m")
    
    st.subheader("💡 設計効率")
    it_efficiency = (inner_length * inner_width) / total_area
    st.write(f"**IT面積効率:** {it_efficiency:.1%}")
    st.write(f"**電力密度:** {total_it_mw*1000/total_area:.2f} kW/㎡")

with col2:
    st.plotly_chart(fig, use_container_width=True)

# 補足情報
with st.expander("詳細な面積内訳を確認"):
    st.write(f"・データホール純面積: {inner_length * inner_width:.1f} ㎡")
    st.write(f"・空調機械室面積: {fwu_d * (total_width - corridor*2) * (2 if cooling_type=='対面吹き (Dual Side)' else 1):.1f} ㎡")
    st.write(f"・廊下/壁体面積: {total_area - (inner_length*inner_width) - (fwu_d*(total_width-corridor*2)*(2 if cooling_type=='対面吹き (Dual Side)' else 1)):.1f} ㎡")
