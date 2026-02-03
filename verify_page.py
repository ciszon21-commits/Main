
import urllib.request
import urllib.error

url = "http://127.0.0.1:8000/rpg/equipment/"

try:
    with urllib.request.urlopen(url) as response:
        code = response.getcode()
        content = response.read().decode('utf-8')
        
        print(f"Status Code: {code}")
        
        if "TemplateSyntaxError" in content:
            print("FAIL: TemplateSyntaxError found in content!")
        elif code == 200:
            print("PASS: Page loaded successfully.")
            # Check for dashed border style in CSS (we can't easily check computed style, but we can check if the class is applied)
            if "border: 2px dashed" in content:
                 print("WARNING: Inline dashed border style found (might be old code).")
            else:
                 print("PASS: No inline dashed border style found (good).")
        else:
            print(f"FAIL: Unexpected status code {code}")

except urllib.error.HTTPError as e:
    print(f"FAIL: HTTP Error {e.code}")
    print(e.read().decode('utf-8')[:500]) # Print first 500 chars of error
except Exception as e:
    print(f"FAIL: Error {e}")
