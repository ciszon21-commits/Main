import re

with open('EngineerRPG/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix common patterns
replacements = {
    # Error messages
    "f'?剖???嚗?蝝?? {profile.level}嚗?)": "f'升級了！目前等級 {profile.level}')",
    "'??蝣潔?甇?Ⅱ'": "'原密碼錯誤'",
    "'撌脫????)": "'已登出')",
    "f'甇∟??????芾???典歇? {user.rpg_profile.character_class.name}'": "f'歡迎冒險者！你的職業是 {user.rpg_profile.character_class.name}'",
    "f'甇∟???嚗user.username}嚗?)": "f'歡迎，{user.username}！')",
    "'??啣ㄚ'": "'土木戰士'",
    "'撠移?撌亦??璆?'": "'專精土木工程的職業'",
}

fixed_lines = []
for line in lines:
    # Check for unterminated strings
    fixed_line = line
    
    # Replace known patterns
    for old, new in replacements.items():
        if old in fixed_line:
            fixed_line = fixed_line.replace(old, new)
    
    # Fix unterminated f-strings that contain garbled characters
    # Pattern: f'...(garbled)...) without closing quote
    matches = re.findall(r"f'[^']*$", fixed_line.rstrip())
    for match in matches:
        if match and not match.endswith("'"):
            # This is an unterminated f-string
            fixed_line = fixed_line.replace(match, "f'訊息')")
    
    # Same for regular strings
    matches = re.findall(r"'[^']+$", fixed_line.rstrip())
    for match in matches:
        stripped = fixed_line.rstrip()
        if stripped.endswith(match) and not stripped.endswith("'") and not stripped.endswith("'''"):
            # Check if this is inside a function call
            fixed_line = fixed_line.replace(match, "'訊息')")
    
    fixed_lines.append(fixed_line)

with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print(f'Processed {len(fixed_lines)} lines')
