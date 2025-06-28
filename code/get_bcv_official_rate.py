import requests
from bs4 import BeautifulSoup
import os
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_bcv_all_rates():
    """
    Scrape all official BCV rates from their website using div ids
    """
    url = "https://www.bcv.org.ve/tasas-informativas-sistema-bancario"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        currency_map = {
            "euro":  {"code": "EUR", "symbol": "€"},
            "yuan":  {"code": "CNY", "symbol": "¥"},
            "lira":  {"code": "TRY", "symbol": "₺"},
            "rublo": {"code": "RUB", "symbol": "₽"},
            "dolar": {"code": "USD", "symbol": "$"},
        }

        rates = []
        for div_id, info in currency_map.items():
            div = soup.find("div", id=div_id)
            if div:
                strong = div.find("strong")
                if strong:
                    text = strong.get_text(strip=True)
                    try:
                        value = float(text.replace(",", ""))
                        rates.append({
                            "id": div_id,
                            "code": info["code"],
                            "symbol": info["symbol"],
                            "value": value,
                            "raw": text
                        })
                    except Exception as e:
                        print(f"Could not parse value for {div_id}: {text} ({e})")

        # Get the value date (e.g., "Fecha Valor: Lunes, 30 Junio 2025")
        value_date = None
        for tag in soup.find_all(string=True):
            if 'Fecha Valor' in tag:
                value_date = tag.strip()
                break

        # Save all rates and the value date
        output = {
            'fecha_valor': value_date,
            'rates': rates
        }
        output_path = "../data/cleaned/bcv_official_rates.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Saved all BCV rates: {rates}")
        return output
    except Exception as e:
        print(f"Error fetching BCV rates: {e}")
        return None

if __name__ == "__main__":
    get_bcv_all_rates() 