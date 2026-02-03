
# clean_null_bytes.py
try:
    with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'rb') as f:
        content = f.read()

    if b'\x00' in content:
        print("Found null bytes. Cleaning...")
        new_content = content.replace(b'\x00', b'')
        
        # Check for BOMs and strip if needed? 
        # But null bytes usually come from UTF-16 encoding of ASCII text (0x00 0x61 etc).
        # replacing 0x00 might leave 0x61 (a) which is correct if it was basic text.
        
        with open(r'd:\10.vibecoding\CoDevStudio-07729\EngineerRPG\views.py', 'wb') as f:
            f.write(new_content)
        print("Cleaned views.py")
    else:
        print("No null bytes found.")

except Exception as e:
    print(f"Error: {e}")
