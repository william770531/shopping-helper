import os
import json
import time
import itertools
import google.generativeai as genai
from PIL import Image
import tkinter as tk
from tkinter import filedialog

# ==========================================
# 🔑 設定區：Pay-as-you-go 專用
# ==========================================
# 請將您那把顯示為 "Pay-as-you-go" 的新 Key 貼在下面
API_KEYS = [
    "AIzaSyB9kLOTCxNA8FNaA6JOhuSO8o2eANsnjPI", 
]

# 使用目前最快、最聰明的模型
MODEL_NAME = "gemini-2.0-flash-exp"
# ==========================================

# 建立 Key 循環產生器 (雖然付費版一把就夠，但保留此結構方便擴充)
key_cycle = itertools.cycle(API_KEYS)

def configure_genai():
    """設定 API Key"""
    current_key = next(key_cycle)
    genai.configure(api_key=current_key)
    return current_key

def analyze_image(image_path, retry_count=0):
    """
    全速分析模式 (無人工延遲)
    """
    current_key = configure_genai()
    # 隱藏 Key 的大部分字元，只顯示末四碼
    key_display = f"...{current_key[-4:]}"
    
    # 使用 \r 讓進度條在同一行更新，看起來更簡潔
    print(f"   🚀 [{key_display}] 分析: {os.path.basename(image_path)} ...", end="\r")
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        img = Image.open(image_path)

        # 給 AI 的指令 (Prompt)
        prompt = """
        你是一個專業的百貨公司 DM 數據分析師。
        請幫我分析這張圖片，抓取所有的「信用卡滿額禮」或「全館滿千送百」規則。
        請嚴格遵守以下規則：
        1. 只要看到「滿 X 元 送 Y 元/點」，就抓取下來。
        2. 銀行名稱請精簡 (例如 "玉山銀行", "聯名卡", "全館")。
        3. 忽略無關的廣告詞，只專注在數字規則。
        4. 回傳格式必須是標準的 JSON Array，不要 Markdown 標記。
        5. 如果圖片中沒有滿額禮規則，請回傳空陣列 []。
        
        JSON 格式範例：
        [
            {"bank": "玉山銀行", "threshold": 6000, "reward": 100},
            {"bank": "全館", "threshold": 5000, "reward": 500}
        ]
        """

        # 發送請求 (不設 user_prompt 參數，直接傳 list)
        response = model.generate_content([prompt, img])
        
        # 清理回傳文字 (去掉 Markdown 符號)
        text = response.text.replace("```json", "").replace("```", "").strip()
        
        if not text: return []
        data = json.loads(text)
        
        # 成功後印出
        print(f"   ✅ 分析成功: {os.path.basename(image_path)} (抓到 {len(data)} 筆)   ")
        return data

    except Exception as e:
        # 即使是付費版，偶爾還是可能會有網路波動，保留簡單的重試機制 (最多3次)
        if retry_count < 3:
            print(f"   ⚠️ 網路波動，1秒後重試 ({retry_count+1})...             ", end="\r")
            time.sleep(1) 
            return analyze_image(image_path, retry_count + 1)
        else:
            # 放棄該圖片
            print(f"   ❌ 跳過此圖: {e}                         ")
            return []

def select_folder_gui():
    """跳出視窗選擇資料夾"""
    root = tk.Tk()
    root.withdraw() 
    root.attributes('-topmost', True)
    folder_selected = filedialog.askdirectory(title="請選擇包含 DM 圖片的資料夾")
    root.destroy()
    return folder_selected

def main():
    print(f"=== DM 智慧分析器 (🚀 Pay-as-you-go 極速版) ===")
    print(f"🔑 使用 Key 數量: {len(API_KEYS)}")
    print("ℹ️  已解除速度限制，全速運轉中。")
    
    print("\n📂 正在開啟視窗，請選擇資料夾...")
    folder_name = select_folder_gui()
    
    if not folder_name:
        print("❌ 取消選擇")
        return

    try:
        all_files = os.listdir(folder_name)
    except: return

    # 只抓圖檔
    image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_files.sort()

    print(f"\n📂 準備分析 {len(image_files)} 張圖片...\n")
    
    all_rules = []
    start_time = time.time()

    for img_file in image_files:
        full_path = os.path.join(folder_name, img_file)
        
        rules = analyze_image(full_path)
        
        if rules:
            all_rules.extend(rules)
        
        # 極速模式：幾乎不休息，僅保留 0.1 秒緩衝
        time.sleep(0.1) 

    # 存檔
    output_file = "final_data.json"
    print("-" * 50)
    
    if all_rules:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_rules, f, ensure_ascii=False, indent=4)
        
        duration = time.time() - start_time
        print(f"🎉 分析完成！總耗時 {duration:.2f} 秒")
        print(f"📊 共抓到 {len(all_rules)} 筆規則")
        print(f"💾 已存檔為: {output_file}")
        print("💡 下一步：執行 'python -m streamlit run app.py' 查看結果！")
    else:
        print("⚠️ 沒有抓到資料，請確認圖片內容或 Key 是否正確。")

if __name__ == "__main__":
    main()