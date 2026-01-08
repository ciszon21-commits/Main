"""
SinoFile Registry
==================
註冊可封存欄位的機制。

使用方式:
    在 app 的 apps.py 的 ready() 中註冊:
    
    from SinoFile.registry import register_archivable_field
    from .models import MyModel
    
    register_archivable_field(MyModel, 'file_field_name')
"""

from typing import List, Tuple, Type
from django.db import models


# 儲存 (model_class, field_name) 的列表
_ARCHIVABLE_FIELDS: List[Tuple[Type[models.Model], str]] = []


def register_archivable_field(model: Type[models.Model], field_name: str):
    """
    註冊一個可封存的欄位
    
    Args:
        model: Django Model 類別
        field_name: FileField 欄位名稱
    """
    # 避免重複註冊
    entry = (model, field_name)
    if entry not in _ARCHIVABLE_FIELDS:
        _ARCHIVABLE_FIELDS.append(entry)


def get_archivable_fields() -> List[Tuple[Type[models.Model], str]]:
    """
    取得所有已註冊的可封存欄位
    
    Returns:
        List of (model_class, field_name) tuples
    """
    return _ARCHIVABLE_FIELDS.copy()


def clear_registry():
    """清空註冊表（主要用於測試）"""
    _ARCHIVABLE_FIELDS.clear()
