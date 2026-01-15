import json
import os

# ==========================================
# 🔧 設定區 1：黑名單
# ==========================================
BLOCK_LIST = ["MUJI", "UNIQLO", "H&M", "GAP", "NET", "ZARA", "餐廳", "服飾"]

# ==========================================
# 🔧 設定區 2：上帝之手 (手動補完 - 區分日期)
# ==========================================
# 我們把聯名卡拆成不同日期的「策略」，讓使用者自己選要哪一天去
MANUAL_PATCH = {
    # 根據 DM 圖片：12/26 ~ 1/4 (只有一階)
    "南紡聯名卡 (12/26-1/4)": [
        [10000, 300]
    ],
    # 根據 DM 圖片：1/5 ~ 1/21 (有三階)
    "南紡聯名卡 (1/5-1/21)": [
        [6000, 100],
        [15000, 300],
        [27000, 600]
    ]
}

def load_data(filename="final_data.json"):
    if not os.path.exists(filename):
        print("❌ 找不到資料檔！")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_number(value):
    if isinstance(value, int): return value
    if isinstance(value, str):
        clean = value.replace(",", "").replace(" ", "").replace("$", "").replace("元", "")
        if "%" in clean: return 0 
        try:
            return int(clean)
        except:
            return 0
    return 0

def calculate_best_deal(amount):
    raw_data = load_data()
    if not raw_data: return

    print(f"\n💰 預計消費金額: {amount:,} 元")
    print("-" * 75)

    general_rules = []
    bank_rules_map = {}
    general_keywords = ["全館", "會員", "General", "FUN點", "給利"] 
    
    # 1. 注入手動資料 (這裡會自動變成兩個不同的銀行選項)
    for name, rules in MANUAL_PATCH.items():
        bank_rules_map[name] = []
        for r in rules:
            bank_rules_map[name].append({"threshold": r[0], "reward": r[1]})

    # 2. 處理 AI 抓到的資料
    for item in raw_data:
        raw_bank_name = item.get("bank", "Unknown") or "Unknown"
        bank_name = raw_bank_name.strip()
        
        threshold = clean_number(item.get("threshold", 0))
        reward = clean_number(item.get("reward", 0))

        if threshold == 0 or reward == 0: continue
        
        if any(bad_word in bank_name.upper() for bad_word in BLOCK_LIST): continue
        if bank_name == "Unknown" or bank_name in ["銀行", "滿額禮"]: continue
        if "聯名卡" in bank_name or "Part" in bank_name: continue

        # 分類
        is_general = False
        for k in general_keywords:
            if k in bank_name: 
                is_general = True
                break
        
        if is_general:
            general_rules.append({"threshold": threshold, "reward": reward, "name": bank_name})
        else:
            if bank_name not in bank_rules_map:
                bank_rules_map[bank_name] = []
            bank_rules_map[bank_name].append({"threshold": threshold, "reward": reward})

    # 3. 計算全館基本盤
    base_reward = 0
    base_rule_desc = "無全館活動"
    valid_general = [r for r in general_rules if amount >= r['threshold']]
    if valid_general:
        best_gen = max(valid_general, key=lambda x: (amount // x['threshold']) * x['reward'])
        count = amount // best_gen['threshold']
        base_reward = count * best_gen['reward']
        base_rule_desc = f"{best_gen['name']} (滿{best_gen['threshold']}送{best_gen['reward']})"

    print(f"🎁 全館/會員共同回饋: {base_reward} 元")
    if base_reward > 0:
        print(f"   └─ 來源: {base_rule_desc}")
    print("-" * 75)

    # 4. 計算各家銀行
    final_results = []

    # 加入現金選項
    final_results.append({
        "card": "現金/其他",
        "special_gift": 0,
        "total": base_reward,
        "note": ""
    })

    for bank, offers in bank_rules_map.items():
        best_special_gift = 0
        rule_note = ""
        
        for offer in offers:
            if amount >= offer['threshold']:
                if offer['reward'] > best_special_gift:
                    best_special_gift = offer['reward']
                    rule_note = f"滿{offer['threshold']}送{offer['reward']}"
        
        total = base_reward + best_special_gift
        
        # 只要有設定規則的卡片都列出來 (即使沒達到門檻顯示0，方便比較)
        # 特別是我們手動加入的聯名卡，一定要顯示
        if best_special_gift > 0 or "聯名卡" in bank or amount > 5000:
             # 只列出有拿到禮券的，或者它是聯名卡(為了顯示日期區別)
            if best_special_gift > 0 or "聯名卡" in bank:
                final_results.append({
                    "card": bank,
                    "special_gift": best_special_gift,
                    "total": total,
                    "note": rule_note if best_special_gift > 0 else "未達門檻"
                })

    # 5. 排序與輸出
    final_results.sort(key=lambda x: x['total'], reverse=True)

    print(f"{'刷卡策略 (含日期)':<22} | {'銀行禮':<8} | {'總回饋':<8} | {'回饋率'}")
    print("-" * 75)
    
    for res in final_results:
        rate = (res['total'] / amount) * 100
        
        # 處理備註顯示
        gift_str = str(res['special_gift'])
        if res['special_gift'] == 0: gift_str = "-"
        
        # 顯示名稱 (截斷過長的)
        name_display = res['card']
        if len(name_display) > 20: name_display = name_display[:18] + ".."
        
        print(f"{name_display:<25} | {gift_str:<10} | {res['total']:<10} | {rate:.2f}%")
        
        # 如果有備註，換行印出來比較清楚
        if res.get('note') and res['note'] != "未達門檻":
             print(f"   └─ {res['note']}")

    print("-" * 75)
    if final_results:
        winner = final_results[0]
        print(f"🏆 冠軍策略: 刷【{winner['card']}】")
        print(f"   可拿 {winner['total']} 元")

if __name__ == "__main__":
    while True:
        try:
            val = input("\n請輸入消費金額 (輸入 q 離開): ")
            if val.lower() == 'q': break
            amount = int(val)
            calculate_best_deal(amount)
        except ValueError:
            print("請輸入數字！")