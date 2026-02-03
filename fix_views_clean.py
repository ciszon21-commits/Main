# 修復並使用 views_clean.py

import re

# 讀取檔案，忽略錯誤字符
with open('EngineerRPG/views_clean.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 移除或替換問題字符
# 查找所有包含替換字符 � 的字符串
content = re.sub(r'"""[^"]*�[^"]*"""', '"""修復的文檔字符串"""', content)
content = re.sub(r'"[^"]*�[^"]*"', '"修復的字符串"', content)
content = re.sub(r"'[^']*�[^']*'", "'修復的字符串'", content)

# 寫入新檔案
with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 已修復並複製 views_clean.py 到 views.py")

# 驗證
import py_compile
try:
    py_compile.compile('EngineerRPG/views.py', doraise=True)
    print("✓ views.py 編譯成功！")
except Exception as e:
    print(f"✗ 編譯失敗: {e}")
