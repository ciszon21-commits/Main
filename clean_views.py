import sys

# 讀取損壞的檔案
try:
    with open('EngineerRPG/views.py', 'rb') as f:
        content = f.read()
    
    # 移除所有 null bytes
    clean_content = content.replace(b'\x00', b'')
    
    # 寫回檔案
    with open('EngineerRPG/views.py', 'wb') as f:
        f.write(clean_content)
    
    print(f"Cleaned file. Original size: {len(content)}, New size: {len(clean_content)}")
    print(f"Removed {len(content) - len(clean_content)} null bytes")
    
    # 嘗試編譯以驗證
    import py_compile
    py_compile.compile('EngineerRPG/views.py', doraise=True)
    print("File compiled successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
