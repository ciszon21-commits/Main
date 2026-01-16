"""
SinoFile Fields
================
SinoFileField: 自訂 FileField，自動處理 archived:// 協議的 URL 產生。

使用方式:
    1. 在業務模型中將 models.FileField 替換為 SinoFileField
    2. 前端模板無需任何改動，file.url 會自動產生正確的 URL

Path Encoding Strategy:
    - Hot files: 標準 MEDIA_URL 路徑 (如 media/uploads/file.pdf)
    - Cold files: archived://{FolderName}/{UUID}.{ext} (如 archived://CODEV00001/abc123.pdf)

當 file.url 被呼叫時:
    - 偵測到 archived:// 前綴 -> 產生 ARCHIVE_URL/{FolderName}/{UUID}.{ext}
    - 否則 -> 產生標準 MEDIA_URL 路徑
"""

import os
from django.conf import settings
from django.db.models.fields.files import FieldFile, FileField


# archived:// 協議前綴
ARCHIVE_PROTOCOL = 'archived://'


class SinoFileFieldFile(FieldFile):
    """
    自訂 FieldFile，覆寫 url 屬性以支援 archived:// 協議。
    
    前端透明性: 模板中使用 {{ file.url }} 無需任何改動，
    此類會自動判斷並產生正確的 URL。
    """
    
    @property
    def url(self):
        """
        產生檔案的公開 URL。
        
        Returns:
            str: 
                - 若為 archived:// 路徑 -> ARCHIVE_URL/{FolderName}/{UUID}.{ext}
                - 否則 -> 標準 MEDIA_URL 路徑
        """
        self._require_file()
        
        # 取得儲存的路徑值
        file_path = self.name
        
        # 檢查是否為 archived:// 協議
        if file_path and file_path.startswith(ARCHIVE_PROTOCOL):
            # 解析 archived://{FolderName}/{UUID}.{ext}
            archive_path = file_path[len(ARCHIVE_PROTOCOL):]
            archive_url = getattr(settings, 'ARCHIVE_URL', '/archive/')
            
            # 確保 URL 格式正確
            if not archive_url.endswith('/'):
                archive_url += '/'
            
            return f'{archive_url}{archive_path}'
        
        # 標準 Hot 檔案 URL
        return self.storage.url(self.name)
    
    @property
    def is_archived(self):
        """檢查此檔案是否已封存至冷儲存"""
        return bool(self.name and self.name.startswith(ARCHIVE_PROTOCOL))
    
    def get_archive_info(self):
        """
        取得封存資訊（僅適用於已封存的檔案）
        
        Returns:
            dict: {'folder_name': str, 'uuid_filename': str} 或 None
        """
        if not self.is_archived:
            return None
        
        archive_path = self.name[len(ARCHIVE_PROTOCOL):]
        parts = archive_path.split('/', 1)
        
        if len(parts) == 2:
            return {
                'folder_name': parts[0],
                'uuid_filename': parts[1],
            }
        return None


class SinoFileField(FileField):
    """
    中興檔案欄位
    
    繼承自 Django FileField，使用 SinoFileFieldFile 處理 URL 產生邏輯。
    
    使用範例:
        class MyModel(models.Model):
            file = SinoFileField(upload_to='uploads/')
    
    特點:
        1. 完全向後相容 Django FileField
        2. 自動處理 archived:// 協議
        3. 前端模板無需修改
        4. 可與 pack_archives/commit_archives 管理命令搭配使用
    """
    
    attr_class = SinoFileFieldFile
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def deconstruct(self):
        """用於 migrations"""
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
