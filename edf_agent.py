import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel

# ==========================================
# CONFIGURATION
# ==========================================
FILE_NAME = "prices.json"
POSTCODE = "MK10 9WH"
# Paste your key from https://aistudio.google.com/ here
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

# ==========================================
# DATA STRUCTURE (PYDANTIC)
# ==========================================
# This acts as an iron-clad blueprint. It forces Gemini to 
# return exactly these three fields and absolutely nothing else.
class PriceData(BaseModel):
    green: str
    amber: str
    red: str

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

def extract_prices_with_gemini(raw_text):
    """Use Gemini to find the exact prices from the messy website text."""
    print("Asking Gemini to extract tomorrow's rates...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are a data extraction assistant. I am giving you text scraped from the EDF FreePhase electricity webpage.
    Find the pence per kWh (p) rates for the Green, Amber, and Red periods.
    
    Website Text:
    {raw_text[:4000]}
    """
    
    # Generate structured JSON using Gemini Flash (fast and cheap)
    response = client.models.generate_content(
        model='gemini-2.0-flash-lite', 
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PriceData,
        )
    )
    
    # Convert Gemini's text response into a standard Python dictionary
    return json.loads(response.text)

def main():
    # 1. Load the historical data
    data = load_data()
    
    # 2. Shift the days (Today becomes Yesterday, Tomorrow becomes Today)
    data["yesterday"] = data["today"]
    data["today"] = data["tomorrow"]
    
    try:
        # 3. Get the new data for tomorrow
        website_text = fetch_edf_website_text(POSTCODE)
        tomorrow_prices = extract_prices_with_gemini(website_text)
        
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
