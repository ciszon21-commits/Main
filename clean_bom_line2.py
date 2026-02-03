path = 'EngineerRPG/views.py'
with open(path, 'rb') as f:
    lines = f.readlines()

# Check line 2 for BOM (index 1)
if len(lines) > 1 and lines[1].startswith(b'\xef\xbb\xbf'):
    print("Found BOM on line 2. Cleaning...")
    lines[1] = lines[1][3:]
    with open(path, 'wb') as f:
        f.writelines(lines)
    print("Cleaned.")
else:
    print("No BOM found on line 2.")
