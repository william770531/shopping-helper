import os
import shutil
import time

# ==========================================
# 🔧 設定區
# ==========================================
STORE_MAP = {
    "1": {"name": "南紡購物中心", "json": "data_ts.json"},
    "2": {"name": "新光三越",     "json": "data_skm.json"}
}

# 設定 analyze.py 產出的實際檔名 (根據您的回報是 "final")
GENERATED_FILE_NAME = "final"

def main():
    print("=== 🛍️  百貨 DM 全自動更新機器人 (Git版) ===")
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
    temp_folder = "Temp_DM"
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    
    print(f"\n⬇️  [1/3] 正在啟動抓圖... (請依提示輸入 '{temp_folder}')")
    os.system("python3 download.py")
    
    if not os.path.exists(temp_folder) or not os.listdir(temp_folder):
        print("⚠️  未下載圖片，任務終止。")
        return

    # ------------------------------------------------
    # 2. 分析
    # ------------------------------------------------
    print("\n🧠 [2/3] 正在啟動 AI 分析... (請依提示選擇資料夾)")
    
    # 清理舊的產出檔，避免誤判
    if os.path.exists(GENERATED_FILE_NAME):
        os.remove(GENERATED_FILE_NAME)

    os.system("python3 analyze.py")

    # 檢查 analyze.py 是否真的產生了檔案
    if not os.path.exists(GENERATED_FILE_NAME):
        print(f"❌ 分析失敗，找不到產出檔案 '{GENERATED_FILE_NAME}'")
        return

    # ------------------------------------------------
    # 3. 上傳與更名
    # ------------------------------------------------
    target_filename = target['json']
    
    # 如果目標檔案已存在，先刪除，避免 Windows 下有時 move 會報錯
    if os.path.exists(target_filename):
        os.remove(target_filename)

    # 將 'final' 改名為 'data_skm.json' (或 data_ts.json)
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