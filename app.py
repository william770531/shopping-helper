import streamlit as st
import json
import os
import pandas as pd
from datetime import date, datetime

# ==========================================
# 🏪 百貨資料庫 (只保留南紡與新光)
# ==========================================
STORE_DB = {
    "南紡購物中心": {
        "file": "data_ts.json",  # 對應南紡的 JSON 檔
        "rules": {
            "一般商品 (化妝品/服飾/寢具)": {"threshold": 5000, "reward": 500},
            "大家電 / 名品 / 3C":         {"threshold": 10000, "reward": 500}
        }
    },
    "新光三越 (西門店)": {
        "file": "data_skm.json", # 對應新光的 JSON 檔
        "rules": {
            "全館累計 (含化妝品)":   {"threshold": 3000, "reward": 300}, # 新光常見門檻
            "名品 / 大家電 / 法雅客": {"threshold": 10000, "reward": 500}
        }
    }
}

# 銀行白名單 (過濾雜訊用)
VALID_BANK_KEYWORDS = [
    "銀行", "商銀", "庫", "郵局", "信用", "聯名卡", "運通", 
    "國泰", "中信", "台新", "玉山", "富邦", "永豐", "聯邦", "遠東", 
    "華南", "一銀", "兆豐", "合庫", "星展", "滙豐", "渣打", "凱基", 
    "新光", "元大", "彰銀", "土銀", "企銀", "陽信", "板信", "安泰", 
    "樂天", "連線", "王道", "三信", "高雄銀", "台中銀", "京城"
]

st.set_page_config(page_title="百貨刷卡攻略", page_icon="🛍️", layout="wide")

# ==========================================
# 側邊欄：選擇百貨
# ==========================================
st.sidebar.title("🛍️ 選擇百貨")
selected_store_name = st.sidebar.selectbox(
    "請選擇您要計算的商場：",
    list(STORE_DB.keys())
)

# 讀取對應設定
current_config = STORE_DB[selected_store_name]
current_file = current_config["file"]
current_rules = current_config["rules"]

# 顯示目前狀態
file_status = "✅ 檔案就緒" if os.path.exists(current_file) else f"❌ 找不到 {current_file}"
st.sidebar.caption(f"讀取檔案：{current_file}")
st.sidebar.caption(f"狀態：{file_status}")

# ==========================================
# 核心邏輯
# ==========================================
def load_data(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def is_date_in_range(target_date, start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str, "%Y-%m-%d").date()
    return start <= target_date <= end

def calculate(amount, selected_date, selected_category, store_name):
    raw_data = load_data(current_file)
    bank_rules_map = {}

    # 1. 【特殊手動規則】(聯名卡加碼)
    # 南紡規則
    if "南紡" in store_name:
        if is_date_in_range(selected_date, "2025-12-26", "2026-01-04"):
            bank_rules_map["南紡聯名卡 (歲末)"] = [{"threshold": 10000, "reward": 300}]
        elif is_date_in_range(selected_date, "2026-01-05", "2026-01-21"):
            bank_rules_map["南紡聯名卡 (迎新)"] = [{"threshold": 6000, "reward": 100}]
    
    # 新光規則 (範例)
    elif "新光" in store_name:
        if is_date_in_range(selected_date, "2025-11-07", "2025-12-01"): # 假設週年慶
            bank_rules_map["skm pay 限定"] = [{"threshold": 3000, "reward": 300}]

    # 2. 【AI 資料讀取 + 白名單過濾】
    if raw_data:
        for item in raw_data:
            raw_bank_name = item.get("bank", "Unknown") or "Unknown"
            bank_name = raw_bank_name.strip()
            
            try:
                t_val = int(str(item.get("threshold", 0)).replace(",", "").replace("$", ""))
                r_val = int(str(item.get("reward", 0)).replace(",", "").replace("$", ""))
            except: continue

            if t_val == 0 or r_val == 0: continue
            
            # 白名單檢查
            is_valid_bank = False
            for kw in VALID_BANK_KEYWORDS:
                if kw in bank_name:
                    is_valid_bank = True
                    break
            if not is_valid_bank: continue

            # 排除全館/會員字眼
            if any(k in bank_name for k in ["全館", "會員", "General", "FUN點"]):
                continue

            if bank_name not in bank_rules_map:
                bank_rules_map[bank_name] = []
            bank_rules_map[bank_name].append({"threshold": t_val, "reward": r_val})

    # 3. 計算全館回饋
    cat_rule = current_rules.get(selected_category)
    base_reward = 0
    base_desc = "無全館活動"
    
    if cat_rule and amount >= cat_rule['threshold']:
        count = amount // cat_rule['threshold']
        base_reward = count * cat_rule['reward']
        base_desc = f"{selected_category} (滿{cat_rule['threshold']}送{cat_rule['reward']})"

    # 4. 產生結果
    results = []
    results.append({
        "銀行/策略": "現金 / 其他銀行",
        "滿額禮": 0, "全館回饋": base_reward, "總回饋": base_reward, "備註": "無銀行禮"
    })

    for bank, offers in bank_rules_map.items():
        best_gift = 0
        note = "未達門檻"
        for offer in offers:
            if amount >= offer['threshold']:
                if offer['reward'] > best_gift:
                    best_gift = offer['reward']
                    note = f"滿{offer['threshold']}送{offer['reward']}"
        
        total = base_reward + best_gift
        
        # 只顯示有拿到禮券的，或特定的聯名卡
        if best_gift > 0 or "聯名卡" in bank or "skm" in bank:
            results.append({
                "銀行/策略": bank,
                "滿額禮": best_gift, "全館回饋": base_reward, "總回饋": total, "備註": note
            })

    results.sort(key=lambda x: x['總回饋'], reverse=True)
    return results, base_desc

# ==========================================
# 🎨 畫面顯示
# ==========================================
st.title(f"💳 {selected_store_name} 刷卡攻略")

if not os.path.exists(current_file):
    st.warning(f"⚠️ 注意：系統找不到 `{current_file}`")
    st.info(f"💡 請先分析 {selected_store_name} 的 DM，並將結果存為 `{current_file}`")
else:
    t = os.path.getmtime(current_file)
    st.markdown(f"<small style='color:gray'>數據最後更新: {datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')}</small>", unsafe_allow_html=True)

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    user_date = st.date_input("消費日期", value=date.today())
with col2:
    user_cat = st.selectbox("消費業種", list(current_rules.keys()))
with col3:
    amount = st.number_input("預計金額", value=30000, step=1000)

if st.button("🚀 計算回饋", type="primary", use_container_width=True):
    results, base_desc = calculate(amount, user_date, user_cat, selected_store_name)
    
    if results:
        winner = results[0]
        st.divider()
        st.subheader("🏆 冠軍策略")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("推薦", winner['銀行/策略'])
        m2.metric("實拿", f"{winner['總回饋']:,} 元")
        rate = (winner['總回饋'] / amount * 100) if amount > 0 else 0
        m3.metric("回饋率", f"{rate:.2f} %")
        
        st.success(f"**結構**：{base_desc} + 銀行禮 {winner['滿額禮']} 元")
        
        st.divider()
        st.subheader("📊 排行榜")
        st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)
    else:
        st.warning("查無符合條件的資料")