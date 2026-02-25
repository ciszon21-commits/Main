import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.soilmove.tw/soilmove/dumpsiteGisQueryList"
print("--- FETCHING ---")
try:
    response = requests.get(url, verify=False)
    data = response.json()
    items = data if isinstance(data, list) else data.get('data', [])
    if items:
        print(f"KEYS: {list(items[0].keys())}")
        print(f"X: {items[0].get('x')}")
        print(f"Y: {items[0].get('y')}")
        print(f"TWD97X: {items[0].get('TWD97X')}")
        print(f"TWD97Y: {items[0].get('TWD97Y')}")
    else:
        print("NO DATA")
except Exception as e:
    print(e)
print("--- DONE ---")
