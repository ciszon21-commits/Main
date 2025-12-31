import os
from django.core.exceptions import ValidationError

# 定義檔案類型可接受的副檔名
ALLOWED_EXTENSIONS = {
    'quantity': ['.xls', '.xlsx', '.pdf'],
    'price_inquiry': ['.pdf', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'],
    'budget': ['.xml'],
    'blank_tender': ['.xml'],
    'integrated_budget': ['.xml'],
    'price_data': ['.pdf', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.xml'], # Added
}

# 格式化的提示文字
FORMAT_LABELS = {
    'quantity': 'Excel (.xls, .xlsx), PDF (.pdf)',
    'price_inquiry': 'PDF (.pdf), Excel (.xls, .xlsx), 圖片 (.jpg, .jpeg, .png)',
    'budget': 'XML (.xml)',
    'blank_tender': 'XML (.xml)',
    'price_data': 'PDF, Excel, 圖片, XML', # Added
}

def validate_file_extension(uploaded_file, file_type):
    """
    驗證檔案副檔名是否符合規定
    """
    if file_type not in ALLOWED_EXTENSIONS:
        return True, "" # 未定義限制的類型預設允許

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    allowed = ALLOWED_EXTENSIONS[file_type]
    
    if ext not in allowed:
        label = FORMAT_LABELS.get(file_type, ", ".join(allowed))
        return False, f"此類型僅接受 {label} 格式檔案，請重新選擇。"
    
    return True, ""
