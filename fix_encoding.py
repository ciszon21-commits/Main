# 修復編碼並重建 views.py

import codecs

# 嘗試不同的編碼讀取檔案
encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'gbk']

source_files = [
    'EngineerRPG/views_additional.py',
    'EngineerRPG/views_clean.py',
    'EngineerRPG/views_final.py',
]

for source_file in source_files:
    print(f"\n嘗試讀取: {source_file}")
    for encoding in encodings:
        try:
            with open(source_file, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            
            # 檢查是否能編譯
            compile(content, source_file, 'exec')
            
            # 成功！複製到 views.py
            with open('EngineerRPG/views.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ 成功使用 {encoding} 編碼讀取並複製到 views.py")
            
            # 驗證
            import py_compile
            py_compile.compile('EngineerRPG/views.py', doraise=True)
            print("✓ views.py 編譯成功！")
            exit(0)
            
        except Exception as e:
            print(f"  {encoding}: {str(e)[:100]}")
            continue

print("\n所有嘗試都失敗了")
