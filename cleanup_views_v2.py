import re
import shutil

# Backup first
shutil.copy('EngineerRPG/views.py', 'EngineerRPG/views.py.bak_clean')

with open('EngineerRPG/views.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # 1. Fix redirections
    if "redirect('engineer_rpg:setup_profile')" in line:
        line = line.replace("redirect('engineer_rpg:setup_profile')", "redirect('engineer_rpg:profile_edit')")
    
    # 2. Clean up docstrings if they look garbled
    # Pattern: quotes followed by potential garbled text
    # We'll just replace all garbled-looking docstrings with generic ones
    if '"""' in line and any(ord(c) > 0xE000 for c in line):
        line = '    """Function docstring"""\n'
    
    # 3. Clean up messages and string literals
    # This is conservative: if we see Private Use Area chars, we replace the string content
    
    # Regex to find string literals containing PUA characters
    # This is hard to do perfectly with regex on a line-by-line basis, 
    # so we'll do a simpler character filtering for the whole line if it contains PUA
    
    has_pua = any(0xE000 <= ord(c) <= 0xF8FF for c in line)
    if has_pua:
        # If it's a message or print, try to preserve the structure
        if "messages." in line or "print(" in line:
            # Replace content inside quotes with generic message
            line = re.sub(r"f?['\"].*?['\"]", "'Operation processed'", line)
            # Fix any broken syntax from the sub
            if not line.endswith('\n'): line += '\n'
        elif "description=" in line or "name=" in line:
             line = re.sub(r"=['\"].*?['\"]", "='Unknown'", line)
        else:
            # If it's a comment, just strip the garbled part
            if line.strip().startswith('#'):
                line = '# Comment\n'
            else:
                # Code line with garbled text? Potentially dangerous to keep.
                # Try to filter out just the bad chars
                clean_chars = []
                for c in line:
                    if not (0xE000 <= ord(c) <= 0xF8FF):
                        clean_chars.append(c)
                line = "".join(clean_chars)
    
    # 4. Fix specific broken strings identified previously
    if "f'?剖???嚗?蝝??" in line:
        line = "            messages.success(request, f'Level Up! Level {profile.level}')\n"
    
    new_lines.append(line)

with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Cleanup complete.")
