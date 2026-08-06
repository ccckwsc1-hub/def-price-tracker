import json
import os
import requests
from datetime import datetime
from groq import Groq

# ==========================================
# CONFIGURATION
# ==========================================
FILE_NAME = "prices.json"
POSTCODE = "MK10 9WH"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            "postcode": POSTCODE,
            "yesterday": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "today": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "tomorrow": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "last_updated": ""
        }

def fetch_edf_data(postcode):
    """直接呼叫 EDF 取得價格資料的 API"""
    formatted_postcode = postcode.replace(" ", "").upper()
    # 這是 EDF 官網前端實際在背景讀取數據的 API 端點
    url = f"https://www.edfenergy.com/api/tariff/free-phase?postcode={formatted_postcode}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    print(f"Fetching from EDF API for {postcode}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # 直接回傳解析後的 JSON 數據
    return response.json()

def parse_prices_with_groq(api_data):
    """讓 Groq 從 API 回傳的複雜 JSON 結構中精準挑出今日與明日的綠/黃/紅價格"""
    print("Asking Groq to structure the prices...")
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
    You are a precise data extraction assistant. I will give you raw JSON data from the EDF API.
    Your task is to extract the pence per kWh rates for TODAY and TOMORROW for three periods: Green, Amber, and Red.
    
    You MUST output ONLY a valid JSON object. Do not include markdown like ```json.
    The format must be strictly like this:
    {{
        "today": {{"green": "...", "amber": "...", "red": "..."}},
        "tomorrow": {{"green": "...", "amber": "...", "red": "..."}}
    }}
    
    Raw API Data:
    {json.dumps(api_data)[:8000]}
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def main():
    data = load_data()
    
    try:
        api_response = fetch_edf_data(POSTCODE)
        extracted = parse_prices_with_groq(api_response)
        
        # 直接更新今日與明日的資料
        if "today" in extracted:
            data["today"] = extracted["today"]
        if "tomorrow" in extracted:
            data["tomorrow"] = extracted["tomorrow"]
            
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Success! Data updated and saved to {FILE_NAME}")
        print(json.dumps(data, indent=4))
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
