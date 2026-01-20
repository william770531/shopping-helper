import os
import json
import time
import sys
import itertools
import google.generativeai as genai
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

# ==========================================
# 🔑 設定區
# ==========================================
API_KEYS = [
    "AIzaSyB9kLOTCxNA8FNaA6JOhuSO8o2eANsnjPI",  # 👈 記得填回您的 Key
]

MODEL_NAME = "gemini-2.0-flash-exp" 
OUTPUT_FILENAME = "final_data.json"

def process_images_with_gemini(folder_path, target_store):
    if not API_KEYS or "請在這裡貼上" in API_KEYS[0]:
        print("❌ 錯誤：請先在 analyze.py 設定有效的 API Key")
        return []

    genai.configure(api_key=API_KEYS[0])
    
    image_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    if not image_files:
        print("❌ 資料夾內沒有圖片")
        return []
    
    print(f"📂 讀取到 {len(image_files)} 張圖片，目標百貨：{target_store}")
    
    images_payload = []
    for img_file in image_files:
        path = os.path.join(folder_path, img_file)
        img = Image.open(path)
        images_payload.append(img)

    # 取得當年年份，協助 AI 判斷日期
    current_year = datetime.now().year

    # 👇👇👇 改良版 Prompt：加入日期識別與數值防呆 👇👇👇
    prompt = f"""
    你是一個專業的百貨公司 DM 分析師。
    目前的目標百貨是：【 {target_store} 】。今年是 {current_year} 年。
    
    請幫我分析圖片中的信用卡回饋資訊。
    
    ⚠️ 嚴格規則 (Strict Rules)：
    1. **活動日期**：
       - 請仔細尋找圖片中的「活動期間」或「結束日期」。
       - 欄位 "end_date" 請輸出格式為 "YYYY-MM-DD" (例如 2026-02-25)。
       - 如果找不到年份，請預設為 {current_year} 年。
    
    2. **數值合理性檢查 (Sanity Check)**：
       - **小心點數陷阱**：如果回饋寫的是「紅利點數」或「skm points」，請不要直接當作現金！
       - 通常 10 點 = 1 元，或 1000 點 = 100 元。若無法換算，請忽略該筆資料，不要讓回饋率變成 100%。
       - 一般銀行回饋率約在 1% ~ 10% 之間。如果算出回饋率超過 20%，請再次確認是否看錯數字 (例如把門檻當成回饋)。
    
    3. **強制拆分銀行**：
       - 若寫「台新/玉山/花旗 滿5000送100」，請拆成三筆獨立資料。
    
    4. **輸出格式** (JSON List)：
       - "bank": 銀行名稱
       - "threshold": 消費門檻 (純數字)
       - "reward": 回饋金額 (純數字，必須是台幣價值)
       - "feedback_rate": 回饋率 (reward / threshold * 100)，保留一位小數。
       - "end_date": 活動結束日期 (YYYY-MM-DD)，若完全找不到日期請回傳 null。

    """
    # 👆👆👆 Prompt 修改結束 👆👆👆

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content([prompt, *images_payload])
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text)
        return data
        
    except Exception as e:
        print(f"❌ AI 分析發生錯誤: {e}")
        return []

def main():
    print("=== AI DM 分析器 (日期與防呆版) ===")
    
    image_folder = ""
    target_store = "百貨公司" 
    
    if len(sys.argv) > 1:
        image_folder = sys.argv[1]
        if len(sys.argv) > 2:
            target_store = sys.argv[2] 
        print(f"🤖 [自動模式] 目標: {target_store} | 資料夾: {image_folder}")
    else:
        print("請選擇含有 DM 圖片的資料夾...")
        root = tk.Tk()
        root.withdraw()
        image_folder = filedialog.askdirectory(title="選擇圖片資料夾")
    
    if not image_folder:
        print("❌ 未選擇資料夾，程式結束")
        return

    results = process_images_with_gemini(image_folder, target_store)
    
    if results:
        print(f"📊 共抓到 {len(results)} 筆規則")
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"💾 已存檔為: {OUTPUT_FILENAME}")
    else:
        print("⚠️ 未分析出任何結果或發生錯誤。")

if __name__ == "__main__":
    main()