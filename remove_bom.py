path = 'EngineerRPG/views.py'
with open(path, 'rb') as f:
    content = f.read()

# Check for BOM
if content.startswith(b'\xef\xbb\xbf'):
    print("BOM found. Removing...")
    content = content[3:]
    with open(path, 'wb') as f:
        f.write(content)
else:
    print("No BOM found.")
