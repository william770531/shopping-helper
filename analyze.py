import os
import json
import time
import sys
import itertools
import google.generativeai as genai
from PIL import Image
import tkinter as tk
from tkinter import filedialog

# ==========================================
# 🔑 設定區
# ==========================================
API_KEYS = [
    "AIzaSyB9kLOTCxNA8FNaA6JOhuSO8o2eANsnjPI",  # 👈 記得填回您的 Key
]

MODEL_NAME = "gemini-2.0-flash-exp" 
OUTPUT_FILENAME = "final_data.json"

def process_images_with_gemini(folder_path, target_store):
    """
    讀取資料夾圖片並傳送給 Gemini 分析
    target_store: "南紡購物中心" 或 "新光三越"
    """
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

    # 👇👇👇 這裡是最重要的 Prompt 修改 👇👇👇
    prompt = f"""
    你是一個專業的百貨公司 DM 分析師。
    目前的目標百貨是：【 {target_store} 】。
    
    請幫我分析圖片中的信用卡回饋資訊。
    
    ⚠️ 重要規則 (Strict Rules)：
    1. **銀行名稱準確性**：
       - 如果是「{target_store}」，請優先尋找該百貨的「聯名卡」 (例如：南紡聯名卡、新光三越聯名卡)。
       - 絕對不要憑空捏造不存在的卡片 (例如：在南紡看到新光三越卡)。
    
    2. **強制拆分銀行 (One Bank per Item)**：
       - 圖片中常會將多家銀行列在同一格 (例如：台新、玉山、花旗 滿5000送100)。
       - 你必須將它們 **拆開** 成多筆獨立的資料，不能合併寫在一起。
       - 例如：不要寫 "台新/玉山"，要寫成兩筆資料：一筆 "bank": "台新銀行", 一筆 "bank": "玉山銀行"。
    
    3. **輸出格式**：
       - 請輸出純 JSON 格式 (List of Dictionary)。
       - 欄位包含：
         - "bank": 銀行名稱 (請寫全名，如 中國信託、台新銀行)
         - "threshold": 消費門檻 (純數字)
         - "reward": 回饋金額 (純數字)
         - "feedback_rate": 回饋率 (reward / threshold * 100)，保留一位小數。

    只抓取「全館滿千送百」或「信用卡刷卡滿額禮」資訊。
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
    print("=== AI DM 分析器 (精準版) ===")
    
    image_folder = ""
    target_store = "百貨公司" # 預設值
    
    # 接收指令參數
    if len(sys.argv) > 1:
        image_folder = sys.argv[1]
        # 嘗試接收第二個參數 (百貨名稱)
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

    # 開始分析 (帶入百貨名稱)
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