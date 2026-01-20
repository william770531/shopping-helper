import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

def process_single_dm(url, folder_title):
    """ 
    核心功能：針對單一網址進行截圖 
    """
    # 設定存檔資料夾名稱
    folder_name = f"Download_{folder_title}"
    print(f"🚀 [啟動] 準備下載至資料夾: {folder_name}")

    chrome_options = Options()
    # 使用標準 1920x1200 大螢幕比例，確保橫式跨頁 DM 也能完整顯示
    chrome_options.add_argument("--window-size=1920,1200") 
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        # 處理網址參數：確保以適合閱讀的模式開啟
        target_url = url
        # 如果網址沒有帶參數，自動加上適合截圖的參數
        if "#" not in url:
             target_url += "#view=FitV&toolbar=0&navpanes=0"

        print(f"🔗 前往網址: {target_url}")
        driver.get(target_url)
        time.sleep(8)  # 等待讀取器載入
        
        # --- 嘗試隱藏工具列 (模擬滑鼠移動) ---
        actions = ActionChains(driver)
        try:
            # 1. 點擊畫面中央 (取得焦點)
            actions.move_by_offset(960, 600).click().perform()
            time.sleep(0.5)
            
            # 2. 將滑鼠迅速移到左上角 (0,0) 觸發隱藏
            body = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element_with_offset(body, 0, 0).perform()
        except:
            pass
        
        time.sleep(2) # 等待畫面穩定

        max_pages = 80 # 設定最大頁數防呆
        print("📸 開始截圖...")
        
        for page in range(1, max_pages + 1):
            current_filename = f"{folder_name}/page_{page:03d}.png"
            
            # 截圖
            driver.save_screenshot(current_filename)
            print(f"   - 已儲存第 {page} 頁")
            
            # 👇👇👇 策略優化：只抓前 3 頁 👇👇👇
            if page >= 3:
                print("⚡ 策略優化：已達 3 頁上限，停止抓圖。")
                break
            # 👆👆👆 ----------------------- 👆👆👆

            # --- 檢查重複 (判斷是否到底) ---
            if page > 1:
                prev_filename = f"{folder_name}/page_{page-1:03d}.png"
                try:
                    with open(current_filename, 'rb') as f1, open(prev_filename, 'rb') as f2:
                        if f1.read() == f2.read():
                            print(f"✅ [完成] 發現重複頁面，判斷已結束。")
                            f1.close(); f2.close()
                            os.remove(current_filename) 
                            break
                except: pass
            
            # --- 執行翻頁 (向右鍵) ---
            try:
                ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
            except: 
                print("⚠️ 翻頁失敗")
            
            time.sleep(2.5)

    except Exception as e:
        print(f"❌ [錯誤]: {e}")
    finally:
        driver.quit()

def main():
    print("===  DM 手動下載器 ===")
    
    # 1. 輸入網址
    target_url = input("\n請輸入 DM 網址 (例如 https://...): ").strip()
    if not target_url:
        print("❌ 未輸入網址，程式結束")
        return

    # 2. 輸入名稱
    title = input("請輸入資料夾名稱 (直接按 Enter 會自動命名為 'Manual_DM'): ").strip()
    if not title:
        title = "Manual_DM"
    
    # 3. 開始執行
    start_time = time.time()
    process_single_dm(target_url, title)
    
    print(f"\n🎉 任務結束！總耗時: {time.time() - start_time:.2f} 秒")

if __name__ == "__main__":
    main()