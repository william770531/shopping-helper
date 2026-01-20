import os
import shutil
import time

# ==========================================
# 🔧 設定區
# ==========================================
STORE_MAP = {
    "1": {
        "name": "南紡購物中心",
        "dl_folder": "Download_TSMALL",
        "json": "data_ts.json"
    },
    "2": {
        "name": "新光三越",
        "dl_folder": "Download_SKM",
        "json": "data_skm.json"
    }
}

GENERATED_FILE_NAME = "final_data.json"

def main():
    print("=== 🛍️  百貨 DM 全自動更新機器人 (含網頁啟動版) ===")
    print("1. 南紡購物中心")
    print("2. 新光三越")
    
    choice = input("\n請選擇要更新的百貨 (輸入 1 或 2): ").strip()
    target = STORE_MAP.get(choice)
    
    if not target:
        print("❌ 選項錯誤")
        return

    print(f"\n👉 目標: 更新 {target['name']} 的資料")
    
    # ------------------------------------------------
    # 1. 抓圖
    # ------------------------------------------------
    dl_folder = target['dl_folder']

    if os.path.exists(dl_folder):
        print(f"🧹 清理舊的 {dl_folder} 資料夾...")
        shutil.rmtree(dl_folder)

    print(f"\n⬇️  [1/3] 正在啟動抓圖... (只抓前3頁)")
    os.system("python3 download.py")
    
    if not os.path.exists(dl_folder) or not os.listdir(dl_folder):
        print(f"⚠️  未發現圖片！請確認 download.py 是否成功下載至 {dl_folder}")
        return
    else:
        print(f"✅ 圖片檢查 OK！資料夾：{dl_folder}")

    # ------------------------------------------------
    # 2. 分析 (自動傳參數)
    # ------------------------------------------------
    print(f"\n🧠 [2/3] 正在啟動 AI 分析...")
    print(f"👉 系統自動鎖定資料夾：【 {dl_folder} 】，正在傳送給 AI...")
    
    if os.path.exists(GENERATED_FILE_NAME):
        os.remove(GENERATED_FILE_NAME)

    os.system(f'python3 analyze.py "{dl_folder}"')

    if not os.path.exists(GENERATED_FILE_NAME):
        print(f"❌ 分析失敗，找不到產出檔案 '{GENERATED_FILE_NAME}'")
        return

    # ------------------------------------------------
    # 3. 上傳與更名
    # ------------------------------------------------
    target_filename = target['json']
    
    if os.path.exists(target_filename):
        os.remove(target_filename)

    shutil.move(GENERATED_FILE_NAME, target_filename)
    print(f"\n✅  已將 '{GENERATED_FILE_NAME}' 自動改名為: {target_filename}")

    print("\n☁️  [3/3] 正在上傳至雲端...")
    
    os.system("git add .")
    os.system(f'git commit -m "Auto-update {target["name"]} ({time.strftime("%Y-%m-%d")})"')
    push_result = os.system("git push")
    
    if push_result == 0:
        print("\n🎉🎉🎉 成功！手機版已同步更新！ 🎉🎉🎉")
        
        # 👇👇👇 新增功能：詢問是否啟動網站 👇👇👇
        ask_run = input("\n🚀 是否要立即啟動網頁查看結果？(輸入 y 啟動，按其他鍵退出): ").strip().lower()
        if ask_run == 'y':
            print("正在啟動 Streamlit... (按 Ctrl+C 可停止)")
            os.system("python3 -m streamlit run app.py")
        # 👆👆👆 --------------------------- 👆👆👆
    else:
        print("⚠️ 上傳失敗，請檢查網路或 GitHub 權限。")

if __name__ == "__main__":
    main()