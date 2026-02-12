import streamlit as st
import math

# ページ設定
st.set_page_config(page_title="DCモジュール最適化シミュレーター", layout="wide")

st.title("🏛️ DC モジュール詳細設計・最適化ツール")
st.caption("ラック構成・空調機械室・電気設備を統合した最短設計シミュレーション")

# --- サイドバー：変数入力 ---
with st.sidebar:
    st.header("1. ラック・アイル構成")
    rack_kw = st.number_input("ラックIT容量 (kW/台)", value=30.0)
    rack_w = st.number_input("ラック幅 (m)", value=0.6)
    rack_d = st.number_input("ラック奥行 (m)", value=1.2)
    racks_per_row = st.number_input("1列のラック数", value=20)
    cold_aisles = st.number_input("コールドアイル数", value=4)
    
    st.header("2. 通路・空間設計")
    ca_width = st.number_input("コールドアイル幅 (m)", value=1.8)
    ha_width = st.number_input("ホットアイル幅 (m)", value=1.2)
    perimeter_corridor = st.number_input("外周廊下幅 (m)", value=2.4)
    
    st.header("3. 冷却システム (FWU設計)")
    cooling_type = st.selectbox("空調配置方式", ["片側吹き (Single Side)", "対面吹き (Dual Side)"])
    fwu_cap = st.number_input("FWU1台の冷却能力 (kW)", value=400)
    fwu_w = st.number_input("FWU1台の幅 (m)", value=2.4)
    fwu_d = st.number_input("FWU機械室の奥行 (m)", value=4.0)
    liquid_ratio = st.slider("液冷(DLC)比率 (%)", 0, 100, 30) / 100

    st.header("4. 電気・冗長性")
    ups_n_plus = st.selectbox("UPS冗長構成", ["N+1", "2N", "Distributed Redundancy"])
    gen_redundancy = st.slider("発電機冗長(N+x)", 1, 2, 1)

# --- 計算ロジック ---

# A. IT容量計算
rows = cold_aisles * 2
total_racks = racks_per_row * rows
total_it_mw = (total_racks * rack_kw) / 1000
air_heat_load_kw = total_it_mw * 1000 * (1 - liquid_ratio)

# B. データホール内寸計算 (ラック・アイル領域)
# 長手方向 (Length) = ラック幅 * 台数 + 余裕
hall_length = (racks_per_row * rack_w) + 2.0 

# 短手方向 (Width) = (ラック奥行*列) + (CA幅*CA数) + (HA幅*HA数)
hall_width_pure = (rows * rack_d) + (cold_aisles * ca_width) + (cold_aisles * ha_width)
hall_width_with_corridor = hall_width_pure + (perimeter_corridor * 2)

# C. 空調機械室 (FWU) 計算
fwu_needed_qty = math.ceil(air_heat_load_kw / fwu_cap) + 2 # N+2 冗長
if cooling_type == "対面吹き (Dual Side)":
    fwu_per_side = math.ceil(fwu_needed_qty / 2)
    fwu_room_width = fwu_per_side * fwu_w
    # 長手方向に収まるかチェック
    room_length_check = "OK" if fwu_room_width <= hall_length else "要調整 (壁面長不足)"
    total_module_length = hall_length + (fwu_d * 2)
else: # 片側
    fwu_room_width = fwu_needed_qty * fwu_w
    room_length_check = "OK" if fwu_room_width <= hall_length else "要調整 (壁面長不足)"
    total_module_length = hall_length + fwu_d

# D. 全体面積
total_area = total_module_length * hall_width_with_corridor

# --- 結果表示 ---
st.header("🏢 モジュール設計最適化結果")
c1, c2, c3, c4 = st.columns(4)
c1.metric("総IT容量", f"{total_it_mw:.2f} MW")
c2.metric("総ラック数", f"{total_racks} 台")
c3.metric("モジュール総面積", f"{total_area:.1f} m2")
c4.metric("空冷負荷", f"{air_heat_load_kw:,.0f} kW")

st.divider()

# 詳細分析
col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("📐 平面構成の詳細")
    st.write(f"**データホール内寸:** {hall_length:.1f}m (L) × {hall_width_with_corridor:.1f}m (W)")
    st.write(f"**空調機械室:** {fwu_d}m (D) × {hall_width_with_corridor:.1f}m (W) ※{cooling_type}")
    
    st.info(f"💡 **設計チェック:** FWU設置壁面の有効長さは {hall_length:.1f}m です。必要幅 {fwu_room_width:.1f}m に対して **{room_length_check}** です。")

with col_b:
    st.subheader("⚙️ 設備構成")
    st.write(f"**FWU必要台数:** {fwu_needed_qty} 台 (N+2込)")
    st.write(f"**UPS想定:** {(total_it_mw * 1.2):.1f} MVA (IT負荷+マージン)")
    st.write(f"**液冷分受熱量:** {total_it_mw * liquid_ratio * 1000:,.0f} kW")

# 断面イメージの代わりの表
st.subheader("📋 スペース効率分析")
eff_df = pd.DataFrame({
    "項目": ["IT面積比率", "空調/設備面積比率", "ラック密度"],
    "数値": [f"{(hall_length*hall_width_pure)/total_area:.1%}", 
            f"{(total_area - hall_length*hall_width_pure)/total_area:.1%}",
            f"{total_it_mw*1000/total_area:.2f} kW/m2"]
})
st.table(eff_df)
