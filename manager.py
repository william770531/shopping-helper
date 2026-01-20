import os
import shutil
import time

# ==========================================
# 🔧 設定區
# ==========================================
STORE_MAP = {
    "1": {
        "name": "南紡購物中心",
        "dl_folder": "Download_TSMALL",  # 南紡專用資料夾
        "json": "data_ts.json"
    },
    "2": {
        "name": "新光三越",
        "dl_folder": "Download_SKM",     # 新光專用資料夾
        "json": "data_skm.json"
    }
}

# 👇👇👇 修正這裡：設定為實際產出的檔名 "final_data.json" 👇👇👇
GENERATED_FILE_NAME = "final_data.json"

def main():
    print("=== 🛍️  百貨 DM 全自動更新機器人 (最終修正版) ===")
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

    # 只清理「目前要更新」的那間百貨的舊圖片
    if os.path.exists(dl_folder):
        print(f"🧹 清理舊的 {dl_folder} 資料夾...")
        shutil.rmtree(dl_folder)

    print(f"\n⬇️  [1/3] 正在啟動抓圖... (請依 download.py 提示操作)")
    os.system("python3 download.py")
    
    # 檢查目標資料夾是否有東西
    if not os.path.exists(dl_folder) or not os.listdir(dl_folder):
        print(f"⚠️  未發現圖片！請確認 download.py 是否成功下載至 {dl_folder}")
        return
    else:
        print(f"✅ 圖片檢查 OK！資料夾：{dl_folder}")

    # ------------------------------------------------
    # 2. 分析
    # ------------------------------------------------
    print(f"\n🧠 [2/3] 正在啟動 AI 分析...")
    print(f"👉 請在彈出的視窗中，選擇這個資料夾：【 {dl_folder} 】")
    
    # 清理舊的產出檔，避免誤抓
    if os.path.exists(GENERATED_FILE_NAME):
        os.remove(GENERATED_FILE_NAME)

    os.system("python3 analyze.py")

    # 檢查是否產生結果 (這次檔名對了，應該就會抓到了)
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
    else:
        print("⚠️ 上傳失敗，請檢查網路或 GitHub 權限。")

if __name__ == "__main__":
    main()