import os
import json
import time
import sys  # 👈 這是接收外部指令的關鍵套件
import itertools
import google.generativeai as genai
from PIL import Image
import tkinter as tk
from tkinter import filedialog

# ==========================================
# 🔑 設定區
# ==========================================
# 👇👇👇 請務必在這裡貼上您的 Google Gemini API Key 👇👇👇
API_KEYS = [
    "AIzaSyB9kLOTCxNA8FNaA6JOhuSO8o2eANsnjPI", 
]

# 模型設定
MODEL_NAME = "gemini-2.0-flash-exp" 
OUTPUT_FILENAME = "final_data.json"

def process_images_with_gemini(folder_path):
    """
    讀取資料夾圖片並傳送給 Gemini 分析
    """
    # 檢查 API Key 是否設定
    if not API_KEYS or "請在這裡貼上" in API_KEYS[0]:
        print("❌ 錯誤：請先在 analyze.py 第 16 行設定有效的 API Key")
        return []

    genai.configure(api_key=API_KEYS[0])
    
    # 1. 讀取圖片
    image_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
    if not image_files:
        print("❌ 資料夾內沒有圖片")
        return []
    
    print(f"📂 讀取到 {len(image_files)} 張圖片，準備分析...")
    
    images_payload = []
    for img_file in image_files:
        path = os.path.join(folder_path, img_file)
        img = Image.open(path)
        images_payload.append(img)

    # 2. 設定 Prompt
    prompt = """
    你是一個百貨公司 DM 分析師。請幫我分析這些圖片中的優惠資訊。
    
    請擷取以下資訊，並嚴格輸出為 JSON 格式 (List of Dictionary)：
    1. "bank": 銀行卡片名稱 (例如：新光三越聯名卡、台新銀行、國泰世華...)
    2. "threshold": 消費門檻金額 (請轉為純數字，例如 20000)
    3. "reward": 回饋金額或點數 (請轉為純數字，例如 300)
    4. "feedback_rate": 回饋率 (reward / threshold * 100)，請計算並保留一位小數。

    如果圖片中有多個銀行或多個門檻，請拆分成多筆資料。
    只要抓取「滿千送百」、「刷卡回饋」相關的資訊。
    不要輸出 Markdown 格式 (```json)，只要純文字 JSON。
    """

    # 3. 呼叫 AI
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content([prompt, *images_payload])
        
        # 4. 清理回傳格式
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
    print("=== AI DM 分析器 (自動化版) ===")
    
    # 👇👇👇 自動判斷模式：接球區 👇👇👇
    image_folder = ""
    
    if len(sys.argv) > 1:
        # 情況 A：由 manager.py 傳送指令過來 (自動模式)
        image_folder = sys.argv[1]
        print(f"🤖 [自動模式] 接收到目標資料夾: {image_folder}")
    else:
        # 情況 B：手動執行 (跳出視窗讓您選)
        print("請選擇含有 DM 圖片的資料夾...")
        root = tk.Tk()
        root.withdraw()
        image_folder = filedialog.askdirectory(title="選擇圖片資料夾")
    
    if not image_folder:
        print("❌ 未選擇資料夾，程式結束")
        return

    # 開始分析
    results = process_images_with_gemini(image_folder)
    
    if results:
        print(f"📊 共抓到 {len(results)} 筆規則")
        
        # 存檔
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print(f"💾 已存檔為: {OUTPUT_FILENAME}")
    else:
        print("⚠️ 未分析出任何結果或發生錯誤。")

if __name__ == "__main__":
    main()