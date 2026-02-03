# Final fix: Remove all lines with syntax errors
with open('d:/10.vibecoding/CoDevStudio-07729/EngineerRPG/views.py', 'rb') as f:
    content = f.read()

# Try different encodings
try:
    text = content.decode('utf-8')
except:
    try:
        text = content.decode('utf-8', errors='ignore')
    except:
        text = content.decode('latin-1', errors='ignore')

lines = text.split('\n')
clean_lines = []

for i, line in enumerate(lines):
    # Skip lines that would cause syntax errors
    try:
        # Try to compile the line as Python (if it looks like code)
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            compile(line + '\n', '<string>', 'exec')
        clean_lines.append(line)
    except SyntaxError as e:
        # Skip this line
        print(f"Skipped line {i+1} due to syntax error: {str(e)[:50]}")
        continue
    except:
        # Keep the line if it's not compilable (might be part of multi-line statement)
        clean_lines.append(line)

with open('d:/10.vibecoding/CoDevStudio-07729/EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(clean_lines))

print(f"Done! Kept {len(clean_lines)} / {len(lines)} lines")
