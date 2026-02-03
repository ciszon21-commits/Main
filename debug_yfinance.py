import yfinance as yf
import ssl
import os
import urllib3

# Disable SSL warnings (mimicking app logic)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

symbols = ['2330.TW', 'AAPL']

print("Starting yfinance debug...")
for symbol in symbols:
    print(f"\n--- Testing {symbol} ---")
    try:
        ticker = yf.Ticker(symbol)
        
        print("Attempting .fast_info...")
        try:
            info = ticker.fast_info
            price = info.last_price
            print(f"Success! fast_info.last_price: {price}")
        except Exception as e:
            print(f"fast_info FAILED: {e}")

        print("Attempting .history(period='1d')...")
        try:
            hist = ticker.history(period="1d")
            if not hist.empty:
                print(f"Success! history last close: {hist['Close'].iloc[-1]}")
            else:
                print("history returned empty DataFrame")
        except Exception as e:
            print(f"history FAILED: {e}")

    except Exception as e:
        print(f"Ticker creation or other error: {e}")
