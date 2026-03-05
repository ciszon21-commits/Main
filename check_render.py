import urllib.request

try:
    resp = urllib.request.urlopen('http://127.0.0.1:8000/volume-calc/')
    html = resp.read().decode('utf-8')
    lines = html.split('\n')
    for i, line in enumerate(lines):
        if "function volumeCalculator" in line:
            for j in range(i, min(i+15, len(lines))):
                print(f"{j}: {repr(lines[j])}")
except Exception as e:
    print("Error:", e)
