import requests
import json
import os

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.soilmove.tw/soilmove/dumpsiteGisQueryList"
print(f"Fetching {url}...")
try:
    response = requests.get(url, verify=False)
    data = response.json()
    
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if 'data' in data: items = data['data']
        elif 'items' in data: items = data['items']
        
    print(f"Found {len(items)} items.")
    if len(items) > 0:
        print("First item keys:", items[0].keys())
        print("First item sample:", json.dumps(items[0], ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
