import re

with open('EngineerRPG/views.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Remove any non-printable characters (except newlines, tabs, etc.)
cleaned_content = ''
for char in content:
    code = ord(char)
    # Keep regular ASCII printable, newline, carriage return, tab
    # Keep standard CJK characters (Chinese)
    if code == 0x0A or code == 0x0D or code == 0x09:  # newline, CR, tab
        cleaned_content += char
    elif 0x20 <= code <= 0x7E:  # ASCII printable
        cleaned_content += char
    elif 0x4E00 <= code <= 0x9FFF:  # CJK Unified Ideographs
        cleaned_content += char
    elif 0x3400 <= code <= 0x4DBF:  # CJK Extension A
        cleaned_content += char
    elif 0xFF00 <= code <= 0xFFEF:  # Halfwidth and Fullwidth Forms
        cleaned_content += char
    elif 0x3000 <= code <= 0x303F:  # CJK Symbols
        cleaned_content += char
    # Skip Private Use Area and other garbled characters
    elif 0xE000 <= code <= 0xF8FF:
        continue
    elif code > 0x10000:  # Skip other high Unicode
        continue
    else:
        cleaned_content += char

with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.write(cleaned_content)

print('Views.py cleaned successfully')
