
import os

file_path = r'EngineerRPG/views.py'
backup_path = r'EngineerRPG/views.py.bak'

# Logic to append
append_code = """
@login_required
def delete_question(request, question_id):
    \"\"\"Delete a question\"\"\"
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:question_management')
        
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, '題目已刪除')
        
    return redirect('engineer_rpg:question_management')
"""

def fix_file():
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"Backed up to {backup_path}")

    with open(file_path, 'rb') as f:
        content = f.read()

    # Find the corruption. PowerShell UTF-16 LE usually adds 0x00 bytes.
    # We scan from the end. We expect standard ASCII/UTF-8 Python code.
    # If we find 0x00, we cut.
    
    # Locate the last known good end? 
    # Or simply search for the first 0x00 and cut there?
    # Python source shouldn't have null bytes.
    
    null_byte_index = content.find(b'\x00')
    
    if null_byte_index != -1:
        print(f"Found null byte at offset {null_byte_index}. Truncating...")
        # Check if the preceding bytes are the appended content's start?
        # Actually, simpler: finding the first 0x00 is safe if the original file was clean.
        
        # We might have appended "garbage". 
        # Let's find the end of the previous valid content.
        # It ended with lines like `return render(request, 'EngineerRPG/management/question_list.html', context)`?
        # A safe bet is to look for the last newline before the null byte block?
        
        clean_content = content[:null_byte_index]
        
        # Verify it ends cleanly
        if not clean_content.endswith(b'\n'):
             clean_content += b'\n'
             
        # Write back clean content + new code
        with open(file_path, 'wb') as f:
            f.write(clean_content)
            f.write(append_code.encode('utf-8'))
            
        print("File repaired and code appended.")
    else:
        print("No null bytes found. File might be clean or corrupted differently.")
        # If no null bytes but bad chars?
        # The error said "null bytes". So this should catch it.

if __name__ == "__main__":
    fix_file()
