# Simple script to remove all non-ASCII docstrings
with open('d:/10.vibecoding/CoDevStudio-07729/EngineerRPG/views.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

lines = content.split('\n')
output = []

for i, line in enumerate(lines):
    # Check for non-ASCII in docstrings
    if '"""' in line or "'''" in line:
        try:
            line.encode('ascii')
            output.append(line)
        except:
            # Skip this line
            print(f"Skipped line {i+1}")
            continue
    else:
        output.append(line)

with open('d:/10.vibecoding/CoDevStudio-07729/EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Done! Total lines: {len(output)}")
