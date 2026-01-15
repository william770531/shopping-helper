import google.generativeai as genai
import os

# ⚠️ 請填入您的 API KEY
MY_API_KEY = "AIzaSyABUyc8RaVGv6Swl1u8yga8cQLqgYr9K4U".strip()

genai.configure(api_key=MY_API_KEY)

print("正在查詢您的可用模型清單...\n")

try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 發現模型: {m.name}")
            available_models.append(m.name)
            
    if not available_models:
        print("\n❌ 您的帳號似乎沒有任何可用的文字生成模型。")
    else:
        print("\n🎉 查詢完成！請將程式碼中的 model_name 改成上面其中一個。")
        
except Exception as e:
    print(f"\n❌ 查詢失敗: {e}")
    print("這通常代表 API Key 有誤，或網路連線有問題。")
