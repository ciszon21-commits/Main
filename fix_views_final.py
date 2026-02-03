# 最終修復 - 移除所有損壞的文檔字符串

# 讀取檔案
with open('EngineerRPG/views_clean.py', 'rb') as f:
    content = f.read()

# 解碼
content_str = content.decode('utf-8', errors='replace')

# 移除所有包含 � 的多行文檔字符串
import re

# 匹配 """...""" 或 '''...''' 格式的文檔字符串
def replace_docstring(match):
    docstring = match.group(0)
    if '�' in docstring:
        # 返回簡單的替代文檔字符串
        return '"""Docstring"""'
    return docstring

# 替換所有文檔字符串
content_str = re.sub(r'""".*?"""', replace_docstring, content_str, flags=re.DOTALL)
content_str = re.sub(r"'''.*?'''", replace_docstring, content_str, flags=re.DOTALL)

# 寫入
with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
    f.write(content_str)

print("✓ 已修復並複製到 views.py")

# 驗證
import py_compile
try:
    py_compile.compile('EngineerRPG/views.py', doraise=True)
    print("✓ views.py 編譯成功！")
except Exception as e:
    print(f"✗ 編譯失敗: {str(e)[:200]}")
