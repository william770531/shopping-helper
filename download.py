import os
import time
from PIL import Image, ImageChops 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# ✂️ 設定區：強制去尾像素
# ==========================================
# 在自動裁切後，再額外切掉底部的像素高度。
# 用來對付那些被誤認為內容的下方工具列。
# 建議範圍：40 ~ 80 之間
BOTTOM_CUT_PIXELS = 60
# ==========================================

def trim_background(image_path):
    """
    二段式裁切：先智慧去背，再強制去尾
    """
    try:
        img = Image.open(image_path)
        
        # --- 第一階段：智慧去背景 ---
        # 取得左上角像素作為背景基準色
        bg_color = img.getpixel((0, 0))
        bg = Image.new(img.mode, img.size, bg_color)
        diff = ImageChops.difference(img, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        
        if bbox:
            # 先裁切出包含 DM + 工具列的區域
            intermediate_img = img.crop(bbox)
            
            # --- 第二階段：強制去尾 (切掉工具列) ---
            width, height = intermediate_img.size
            
            # 確保圖片夠高才切，避免切壞小圖
            if height > BOTTOM_CUT_PIXELS * 3:
                # 新的底部邊界 = 目前高度 - 要切掉的像素
                new_bottom = height - BOTTOM_CUT_PIXELS
                # 執行第二刀：從 (0,0) 裁到 (寬度, 新高度)
                final_img = intermediate_img.crop((0, 0, width, new_bottom))
                final_img.save(image_path) # 存檔
                print(f"   ✂️ [雙重裁切] 自動去背 + 強制切除底部 {BOTTOM_CUT_PIXELS}px")
            else:
                # 圖片太小，只執行第一階段存檔
                intermediate_img.save(image_path)
                print(f"   ✂️ [單次裁切] 已自動去背 (圖片過小跳過去尾)")
                
        else:
            print(f"   ⚠️ 圖片全空，跳過裁切")
            
    except Exception as e:
        print(f"   ⚠️ 裁切失敗: {e}")

# ==========================================
# 主程式設定 (維持不變)
# ==========================================
TARGET_WIDTH = 2400
TARGET_HEIGHT = 1600
ZOOM_FACTOR = 0.65

def process_single_dm(url, folder_title):
    folder_name = f"Download_{folder_title}"
    print(f"🚀 [啟動] 準備下載至資料夾: {folder_name}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument(f"--window-size={TARGET_WIDTH},{TARGET_HEIGHT}")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": TARGET_WIDTH,
            "height": TARGET_HEIGHT,
            "deviceScaleFactor": 1, 
            "mobile": False
        })

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        clean_url = url.split('#')[0]
        target_url = f"{clean_url}#view=Fit"

        print(f"🔗 (背景執行中) 前往網址: {target_url}")
        driver.get(target_url)
        
        print("⏳ 等待網頁載入 (10秒)...")
        time.sleep(10) 
        
        try:
            print(f"🔭 正在執行視野縮小：{ZOOM_FACTOR * 100}% ...")
            driver.execute_script(f"document.body.style.zoom='{ZOOM_FACTOR}'")
        except: pass
        
        time.sleep(2) 

        # 模擬滑鼠移除遮擋 (嘗試移到更角落)
        actions = ActionChains(driver)
        try:
            # 先點中間聚焦
            actions.move_by_offset(int(TARGET_WIDTH/2), int(TARGET_HEIGHT/2)).click().perform()
            time.sleep(0.5)
            # 再移到最左上角 (0,0)
            body = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element_with_offset(body, -int(TARGET_WIDTH/2) + 10, -int(TARGET_HEIGHT/2) + 10).perform()
        except:
            pass
        
        time.sleep(3) # 多等一下讓 UI 消失

        max_pages = 80
        print("📸 開始截圖 (含雙重裁切)...")
        
        for page in range(1, max_pages + 1):
            current_filename = f"{folder_name}/page_{page:03d}.png"
            
            driver.save_screenshot(current_filename)
            print(f"   - 已儲存第 {page} 頁 (原始檔)", end="")
            
            # 執行二段式裁切
            trim_background(current_filename)
            
            if page >= 3:
                print("⚡ 策略優化：已達 3 頁上限，停止抓圖。")
                break
            
            # 檢查重複
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
            
            # 翻頁
            try:
                actions_key = ActionChains(driver)
                actions_key.send_keys(Keys.ARROW_RIGHT)
                actions_key.perform()
            except: 
                print("⚠️ 翻頁失敗")
            
            time.sleep(3) 

    except Exception as e:
        print(f"❌ [錯誤]: {e}")
    finally:
        driver.quit()

def main():
    print("===  DM 手動下載器 (強制去尾版) ===")
    
    default_url = "https://www.tsrd.com.tw/online-dm/dmbook?id=cbf9af36-5136-4a34-94c1-cd24d029ed7a&title=2026%E9%87%91%E9%A6%AC%E8%BD%89%E9%B4%BB%E9%81%8B"
    
    target_url = input(f"\n請輸入 DM 網址 (Enter 使用預設南紡網址): ").strip()
    if not target_url:
        target_url = default_url

    print("\n📝 資料夾命名提示：")
    print("   👉 新光三越 請輸入: SKM")
    print("   👉 南紡購物 請輸入: TSMALL")
    title = input("請輸入名稱代號 (直接 Enter 預設 Manual_DM): ").strip()
    
    if not title:
        title = "Manual_DM"
    
    start_time = time.time()
    process_single_dm(target_url, title)
    
    print(f"\n🎉 任務結束！總耗時: {time.time() - start_time:.2f} 秒")

if __name__ == "__main__":
    main()