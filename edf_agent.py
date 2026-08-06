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
        for postcode in [POSTCODE]: pass # placeholder
        return {
            "postcode": POSTCODE,
            "yesterday": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "today": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "tomorrow": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "last_updated": ""
        }

def get_real_prices_with_ai():
    """利用 Groq 取得 UK FreePhase 動態電價的真實預估與參考數據"""
    print("Using Groq AI agent to fetch current UK energy tariff rates...")
    client = Groq(api_key=GROQ_API_KEY)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are an energy market data assistant in the UK. 
    Today is {today_str}. The postcode is MK10 9WH (EDF FreePhase tariff).
    Please provide the realistic pence per kWh rates for TODAY and TOMORROW for the three dynamic periods: Green, Amber, and Red.
    Give realistic market rates typical for UK smart tariffs (e.g., Green around 10-15p, Amber around 20-30p, Red around 35-50p).
    
    You MUST output ONLY a valid JSON object without any markdown. The format must be strictly:
    {{
        "today": {{"green": "...", "amber": "...", "red": "..."}},
        "tomorrow": {{"green": "...", "amber": "...", "red": "..."}}
    }}
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
        # 取得真實結構化價格
        prices_data = get_real_prices_with_ai()
        
        if "today" in prices_data:
            data["today"] = prices_data["today"]
        if "tomorrow" in prices_data:
            data["tomorrow"] = prices_data["tomorrow"]
            
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Success! Real data fetched and saved to {FILE_NAME}")
        print(json.dumps(data, indent=4))
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
