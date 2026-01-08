"""
SinoFile Utilities
===================
封存系統的輔助函式。
"""

import os
from pathlib import Path
from django.conf import settings

from .fields import ARCHIVE_PROTOCOL


def get_archive_root():
    """取得冷儲存掛載點路徑"""
    return getattr(settings, 'ARCHIVE_ROOT', '/mnt/cold_storage')


def get_tmp_root():
    """取得暫存區路徑"""
    return getattr(settings, 'TMP_ROOT', '/mnt/tmp_data')


def get_archive_url():
    """取得封存檔案 URL 前綴"""
    return getattr(settings, 'ARCHIVE_URL', '/archive/')


def get_max_folder_size():
    """取得資料夾大小上限（bytes）"""
    return getattr(settings, 'ARCHIVE_MAX_FOLDER_SIZE', 4 * 1024 * 1024 * 1024)


def is_archived(file_path: str) -> bool:
    """
    檢查路徑是否使用 archived:// 協議
    
    Args:
        file_path: 檔案路徑字串
        
    Returns:
        bool: True 表示已封存
    """
    return bool(file_path and file_path.startswith(ARCHIVE_PROTOCOL))


def parse_archive_path(path: str) -> dict:
    """
    解析 archived:// 路徑
    
    Args:
        path: archived://{FolderName}/{UUID}.{ext} 格式的路徑
        
    Returns:
        dict: {'folder_name': str, 'uuid_filename': str} 或 None
    """
    if not is_archived(path):
        return None
    
    archive_part = path[len(ARCHIVE_PROTOCOL):]
    parts = archive_part.split('/', 1)
    
    if len(parts) == 2:
        return {
            'folder_name': parts[0],
            'uuid_filename': parts[1],
        }
    return None


def build_archive_path(folder_name: str, uuid_filename: str) -> str:
    """
    建構 archived:// 路徑
    
    Args:
        folder_name: 資料夾名稱 (如 VOL_20260108)
        uuid_filename: UUID 檔名 (如 abc123.pdf)
        
    Returns:
        str: archived://{FolderName}/{UUID}.{ext}
    """
    return f'{ARCHIVE_PROTOCOL}{folder_name}/{uuid_filename}'


def verify_cold_folder(folder_name: str) -> bool:
    """
    驗證資料夾是否存在於冷儲存區
    
    Args:
        folder_name: 資料夾名稱
        
    Returns:
        bool: True 表示資料夾存在
    """
    cold_path = Path(get_archive_root()) / folder_name
    return cold_path.exists() and cold_path.is_dir()


def verify_cold_file(folder_name: str, filename: str) -> bool:
    """
    驗證檔案是否存在於冷儲存區
    
    Args:
        folder_name: 資料夾名稱
        filename: 檔案名稱
        
    Returns:
        bool: True 表示檔案存在
    """
    cold_file_path = Path(get_archive_root()) / folder_name / filename
    return cold_file_path.exists() and cold_file_path.is_file()


def get_staging_path(folder_name: str) -> Path:
    """
    取得暫存區資料夾路徑
    
    Args:
        folder_name: 資料夾名稱
        
    Returns:
        Path: 暫存區資料夾的完整路徑
    """
    return Path(get_tmp_root()) / folder_name


def get_cold_path(folder_name: str) -> Path:
    """
    取得冷儲存區資料夾路徑
    
    Args:
        folder_name: 資料夾名稱
        
    Returns:
        Path: 冷儲存區資料夾的完整路徑
    """
    return Path(get_archive_root()) / folder_name


def get_file_extension(filename: str) -> str:
    """
    取得檔案副檔名
    
    Args:
        filename: 檔案名稱
        
    Returns:
        str: 副檔名（包含點號），如 '.pdf'
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()
