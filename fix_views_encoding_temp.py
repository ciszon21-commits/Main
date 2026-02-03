import re

# Read the file
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 393 - broken f-string
content = re.sub(
    r"messages\.success\(request, f'[^']*user\.username\}[^']*\)",
    "messages.success(request, f'Welcome, {user.username}!')",
    content
)

# Write back
with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed line 393")
