import urllib.request

try:
    # Try accessing the payment upload page without any authentication cookies
    print('Testing access to http://127.0.0.1:8000/lunch/payment/upload/ ...')
    req = urllib.request.Request('http://127.0.0.1:8000/lunch/payment/upload/')
    # This should now return 200 directly, not a redirect
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        print(f'STATUS: {response.status}')
        print(f'URL: {response.geturl()}')
        
        # Check for identifying content of the page
        if '繳費辨識' in html and 'type="file"' in html:
             print('SUCCESS: Page content loaded correctly (public access confirmed).')
        else:
             print('FAILURE: Page content seems incorrect or missing expected elements.')
             print('Title check:', '繳費辨識' in html)
             print('File input check:', 'type="file"' in html)

except urllib.error.HTTPError as e:
    print(f'HTTP Error: {e.code} - {e.reason}')
except Exception as e:
    print(f'Error: {e}')
