import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="宇都宮DCマスタープラン・シミュレーター", layout="wide")

st.title("🏗️ 宇都宮GXデジタルキャンパス・シミュレーター")
st.caption("プロフェッショナル設計・インフラ需要・コスト分析ツール")

# --- サイドバー：主要変数 ---
with st.sidebar:
    st.header("1. 基本構成")
    total_phases = st.slider("総フェーズ数", 1, 5, 5)
    target_it_mw = st.number_input("最終IT容量合計 (MW)", value=333.0)
    
    st.header("2. データホール・ラック設計")
    rack_power = st.slider("1ラック当たりIT容量 (kW)", 10.0, 50.0, 30.0)
    racks_per_row = st.number_input("1列当たりのラック数", value=24)
    rows_per_hall = st.number_input("1ホールの列数 (6の倍数推奨)", value=6, step=6)
    
    st.header("3. 空調・インフラ設定")
    pue = st.slider("目標PUE", 1.1, 1.5, 1.2)
    air_cool_ratio = st.slider("空冷負荷比率 (%)", 50, 100, 70)
    fwu_capacity = st.number_input("Fan Wall Unit単機能力 (kW)", value=400)
    coc = st.slider("冷却水濃縮倍数 (CoC)", 3.0, 6.0, 4.0)

# --- 計算ロジック ---
# 1モジュール（データホール）あたりのIT容量
module_racks = racks_per_row * rows_per_hall
module_it_kw = module_racks * rack_power
num_modules = (target_it_mw * 1000) / module_it_kw

# 物理寸法（概算）
hall_width = (rows_per_hall * 1.2) + (3 * 1.8) + (4 * 1.6) + (2.4 * 2)
hall_length = (racks_per_row * 0.6) + 5.0
module_area = hall_width * hall_length

# 水量計算
total_heat_kw = target_it_mw * 1000 * (1 + (pue - 1) * 0.7) # 簡易熱負荷計算
evap_l_h = total_heat_kw * 1.6
makeup_l_h = evap_l_h * (coc / (coc - 1))
daily_water_m3 = (makeup_l_h * 24) / 1000

# --- メイン画面表示 ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("最終IT容量", f"{target_it_mw} MW")
col2.metric("必要ラック総数", f"{int(target_it_mw * 1000 / rack_power)} 台")
col3.metric("1日の必要水量", f"{daily_water_m3:,.0f} m3")
col4.metric("データホール数", f"{num_modules:.1f} 室")

# 水量アラート
if daily_water_m3 > 19000:
    st.error(f"⚠️ 警告: 水量が市の供給上限 (19,000 m3) を超えています！ (現在: {daily_water_m3:,.0f} m3)")
else:
    st.success("✅ 水量は市の供給範囲内です。")

# --- タブ分け詳細表示 ---
tab1, tab2, tab3 = st.tabs(["📊 フェーズ別推移", "📐 モジュール詳細設計", "📝 市役所提出用数値"])

with tab1:
    st.subheader("段階的増強計画")
    phases = [f"Phase {i+1}" for i in range(total_phases)]
    it_steps = [target_it_mw / total_phases * (i+1) for i in range(total_phases)]
    water_steps = [daily_water_m3 / total_phases * (i+1) for i in range(total_phases)]
    df = pd.DataFrame({"IT容量 (MW)": it_steps, "必要水量 (m3/day)": water_steps}, index=phases)
    st.line_chart(df)
    st.table(df)

with tab2:
    st.subheader("1データホール（モジュール）の構成")
    c1, c2 = st.columns(2)
    c1.write(f"**IT容量:** {module_it_kw:,.0f} kW")
    c1.write(f"**ラック数:** {module_racks} 台")
    c1.write(f"**概算面積:** {module_area:.1f} m2")
    
    fwu_needed = (module_it_kw * air_cool_ratio / 100) / fwu_capacity
    c2.write(f"**必要Fan Wall台数:** {fwu_needed:.1f} 台 (N+2を推奨)")
    c2.write(f"**UPS必要容量:** {module_it_kw * 1.1 / 0.9:.0f} kVA")

with tab3:
    st.subheader("市役所ヒアリング用サマリー")
    st.code(f"""
    【事業計画概要】
    ・最終IT負荷: {target_it_mw} MW
    ・最大使用水量: {daily_water_m3:,.0f} m3/day
    ・排水量(推定): {daily_water_m3 * 0.25:,.0f} m3/day
    ・受電電圧: 154kV
    ・建物構造: 免震構造推奨
    """)
