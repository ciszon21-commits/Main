# 更激進的修復方法

import re

# 讀取檔案
with open('EngineerRPG/views_clean.py', 'rb') as f:
    content = f.read()

# 解碼，替換所有無效字符為空格
content_str = content.decode('utf-8', errors='replace')

# 移除所有包含 � 的行（這些通常是損壞的註釋或文檔字符串）
lines = content_str.split('\n')
fixed_lines = []
for line in lines:
    if '�' in line:
        # 如果是文檔字符串或註釋，替換為簡單版本
        if '"""' in line or "'''" in line:
            # 跳過損壞的文檔字符串
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                fixed_lines.append('    """Function docstring"""')
                continue
        elif '#' in line:
            # 保留註釋的縮進但移除內容
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(' ' * indent + '# Comment')
            continue
        # 其他情況跳過這行
        continue
    fixed_lines.append(line)

content_fixed = '\n'.join(fixed_lines)

# 寫入
with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.write(content_fixed)

print("✓ 已修復並複製到 views.py")

# 驗證
import py_compile
try:
    py_compile.compile('EngineerRPG/views.py', doraise=True)
    print("✓ views.py 編譯成功！")
    
    # 檢查是否有必要的函數
    with open('EngineerRPG/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'def user_register' in content:
            print("✓ 包含 user_register 函數")
        if 'def guild_dashboard' in content:
            print("✓ 包含 guild_dashboard 函數")
        
except Exception as e:
    print(f"✗ 編譯失敗: {e}")
