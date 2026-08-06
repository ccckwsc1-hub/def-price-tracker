import json
import os
from datetime import datetime

FILE_NAME = "prices.json"
POSTCODE = "MK10 9WH"

def main():
    # 測試用的真實感價格數據（確保手機和小工具能正常顯示）
    data = {
        "postcode": POSTCODE,
        "yesterday": {"green": "12.4p", "amber": "24.5p", "red": "42.1p"},
        "today": {"green": "13.1p", "amber": "26.0p", "red": "45.2p"},
        "tomorrow": {"green": "11.5p", "amber": "23.0p", "red": "39.8p"},
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"Success! Mock data saved to {FILE_NAME}")

if __name__ == "__main__":
    main()
