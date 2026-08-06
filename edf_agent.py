import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pydantic import BaseModel
from groq import Groq

# ==========================================
# CONFIGURATION
# ==========================================
FILE_NAME = "prices.json"
POSTCODE = "MK10 9WH"
# 從 GitHub Actions 的環境變數中讀取 Groq 金鑰
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 

# ==========================================
# FUNCTIONS
# ==========================================
def load_data():
    """Load existing 3-day data, or create a blank structure if it doesn't exist."""
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Initial blank state including the postcode
        return {
            "postcode": POSTCODE,
            "yesterday": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "today": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "tomorrow": {"green": "N/A", "amber": "N/A", "red": "N/A"},
            "last_updated": ""
        }

def fetch_edf_website_text(postcode):
    """Scrape the EDF page and extract just the readable text."""
    url = f"https://www.edfenergy.com/tariff-information-labels/freePhase?postcode={postcode.replace(' ', '%20')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    print(f"Fetching data from EDF for {postcode}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Use BeautifulSoup to strip out all the HTML code and keep only the text
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def extract_prices_with_groq(raw_text):
    """Use Groq (Llama 3.1) to find the exact prices from the messy website text."""
    print("Asking Groq to extract tomorrow's rates...")
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
    You are a data extraction assistant. I am giving you text scraped from the EDF FreePhase electricity webpage.
    Find the pence per kWh (p) rates for the Green, Amber, and Red periods.
    
    You MUST output ONLY a valid JSON object. Do not include markdown formatting like ```json. 
    The JSON must use this exact structure:
    {{
        "green": "...",
        "amber": "...",
        "red": "..."
    }}
    
    Website Text:
    {raw_text[:4000]}
    """
    
    # Generate structured JSON using Groq's extremely fast Llama 3.1 model
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    # Convert Groq's text response into a standard Python dictionary
    return json.loads(response.choices[0].message.content)

def main():
    # 1. Load the historical data
    data = load_data()
    
    # 2. Shift the days (Today becomes Yesterday, Tomorrow becomes Today)
    data["yesterday"] = data["today"]
    data["today"] = data["tomorrow"]
    
    try:
        # 3. Get the new data for tomorrow
        website_text = fetch_edf_website_text(POSTCODE)
        tomorrow_prices = extract_prices_with_groq(website_text)
        
        # 4. Save the new prices into the "tomorrow" slot
        data["tomorrow"] = tomorrow_prices
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 5. Save everything back to the prices.json file
        with open(FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Success! Data updated and saved to {FILE_NAME}")
        print(json.dumps(data, indent=4))
        
    except Exception as e:
        print(f"An error occurred: {e}")

# ==========================================
# RUN SCRIPT
# ==========================================
if __name__ == "__main__":
    main()
