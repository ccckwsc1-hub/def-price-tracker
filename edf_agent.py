import json
import os
import requests
from bs4 import BeautifulSoup
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

def fetch_edf_page(postcode):
    """抓取 EDF 頁面，並嘗試用行動版或標準版過濾"""
    url = f"https://www.edfenergy.com/tariff-information-labels/freePhase?postcode={postcode.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    # 移除 script 和 style 標籤
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text(separator=' ', strip=True)

def extract_prices_with_groq(raw_text):
    print("Asking Groq to extract prices...")
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
    You are an expert data extractor. The following text is from the EDF FreePhase electricity webpage.
    Even if the page mentions enabling JavaScript, look closely at the text or any embedded pricing info. 
    If you can find pence per kWh rates for Green, Amber, and Red for today and tomorrow, extract them.
    If the text is truly empty or lacks data, return "N/A" for the prices.
    
    You MUST output ONLY a valid JSON object without markdown. Format:
    {{
        "today": {{"green": "...", "amber": "...", "red": "..."}},
        "tomorrow": {{"green": "...", "amber": "...", "red": "..."}}
    }}
    
    Text:
    {raw_text[:8000]}
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
        raw_text = fetch_edf_page(POSTCODE)
        extracted = extract_prices_with_groq(raw_text)
        
        if "today" in extracted:
            data["today"] = extracted["today"]
        if "tomorrow" in extracted:
            data["tomorrow"] = extracted["tomorrow"]
            
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
