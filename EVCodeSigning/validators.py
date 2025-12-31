"""
EVCodeSigning 檔案驗證器
"""
import os
from django.core.exceptions import ValidationError


# 允許的檔案副檔名
ALLOWED_EXTENSIONS = {
    '.exe',   # Windows 執行檔
    '.msi',   # Windows 安裝程式
    '.dll',   # 動態連結程式庫
    '.cab',   # Windows Cabinet 壓縮檔
    '.ocx',   # ActiveX 控制項
    '.xpi',   # Firefox 擴充套件
    '.axp',   # ActiveX 套件
    '.jar',   # Java Archive
    '.air',   # Adobe AIR 應用程式
    '.airi',  # Adobe AIR 中繼檔
}


def validate_signing_file(file):
    """
    驗證上傳檔案的副檔名是否在允許清單中
    
    Args:
        file: 上傳的檔案物件
        
    Raises:
        ValidationError: 當檔案副檔名不在允許清單中時
    """
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ', '.join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationError(
            f'不支援的檔案格式 "{ext}"。'
            f'允許的格式：{allowed_list}'
        )


def get_allowed_extensions_display():
    """取得允許的副檔名清單（用於顯示）"""
    return ', '.join(sorted(ALLOWED_EXTENSIONS))
