import streamlit as st
import json
import pandas as pd
from datetime import datetime

# 設定頁面標題
st.set_page_config(page_title="百貨優惠小幫手", page_icon="🛍️")

st.title("🛍️ 百貨週年慶/檔期 刷卡攻略")

# 讀取資料函式
def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# 側邊欄：選擇百貨
store_choice = st.sidebar.radio("請選擇百貨公司", ["新光三越", "南紡購物中心"])

# 根據選擇讀取對應檔案
if store_choice == "新光三越":
    data = load_data('data_skm.json')
elif store_choice == "南紡購物中心":
    data = load_data('data_ts.json')

# 取得今天日期 (用於過濾)
today = pd.to_datetime(datetime.now().date())
st.sidebar.write(f"📅 今天日期：{today.strftime('%Y-%m-%d')}")

# 顯示資料
if data:
    df = pd.DataFrame(data)

    # 1. 處理日期與過濾過期資料
    if 'end_date' in df.columns:
        # 把日期字串轉為時間物件，無法轉換的變成 NaT
        df['end_date_dt'] = pd.to_datetime(df['end_date'], errors='coerce')
        
        # 篩選：只保留 "結束日期 >= 今天" 或是 "沒有寫日期(NaT)" 的資料
        # (沒有寫日期的通常是通用規則，先保留)
        df_active = df[ (df['end_date_dt'] >= today) | (df['end_date_dt'].isna()) ]
        
        # 計算過濾掉了幾筆
        removed_count = len(df) - len(df_active)
        if removed_count > 0:
            st.warning(f"⚠️ 已自動隱藏 {removed_count} 筆已過期的優惠活動 (2/25 前結束的)。")
            df = df_active # 更新顯示的資料表
    
    # 2. 顯示排序選項 (解決玉山銀行排第一但不合理的問題)
    sort_method = st.radio(
        "排序方式：",
        ('🔥 回饋率最高 (CP值)', '💰 回饋金額最高 (拿最多錢)'),
        horizontal=True
    )

    if sort_method == '🔥 回饋率最高 (CP值)':
        df = df.sort_values(by='feedback_rate', ascending=False)
    else:
        df = df.sort_values(by='reward', ascending=False)

    # 3. 找出最佳優惠
    if not df.empty:
        best_offer = df.iloc[0]
        
        st.subheader(f"🏆 {store_choice} 目前最強神卡")
        col1, col2, col3 = st.columns(3)
        col1.metric("推薦銀行", best_offer['bank'])
        col2.metric("回饋金額", f"${best_offer['reward']}")
        col3.metric("回饋率", f"{best_offer['feedback_rate']}%")

        if 'end_date' in best_offer and best_offer['end_date']:
            st.caption(f"⚠️ 此活動至 {best_offer['end_date']} 截止")

        st.divider()

        # 4. 詳細列表
        st.subheader("💳 所有銀行回饋列表")
        
        # 整理顯示欄位 (把醜醜的 end_date_dt 藏起來)
        display_cols = ['bank', 'threshold', 'reward', 'feedback_rate']
        if 'end_date' in df.columns:
            display_cols.append('end_date')
            
        st.dataframe(
            df[display_cols].style.format({
                "threshold": "${:,}",
                "reward": "${:,}",
                "feedback_rate": "{:.1f}%"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("目前沒有符合日期的優惠活動。")

else:
    st.info(f"尚未建立 {store_choice} 的資料，請先執行 Python 程式抓取。")