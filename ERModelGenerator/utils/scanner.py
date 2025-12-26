"""
ER Model Scanner 工具模組

用於掃描 Django 專案的所有 models，解析欄位類型和關聯關係，
並產生 Mermaid erDiagram 語法。
"""

import re
from django.apps import apps
from django.db import models
from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field


@dataclass
class FieldInfo:
    """欄位資訊"""
    name: str
    field_type: str
    is_pk: bool = False
    is_fk: bool = False
    is_nullable: bool = False
    max_length: Optional[int] = None
    verbose_name: str = ""


@dataclass
class RelationInfo:
    """關聯資訊"""
    from_model: str
    from_app: str
    to_model: str
    to_app: str
    relation_type: str  # 'FK', 'O2O', 'M2M'
    field_name: str
    related_name: str = ""


@dataclass
class ModelInfo:
    """Model 資訊"""
    name: str
    app_label: str
    verbose_name: str
    fields: List[FieldInfo] = field(default_factory=list)
    relations: List[RelationInfo] = field(default_factory=list)
    is_abstract: bool = False
    db_table: str = ""


# Django 欄位類型到 Mermaid 類型的對應
FIELD_TYPE_MAPPING = {
    'AutoField': 'int',
    'BigAutoField': 'bigint',
    'SmallAutoField': 'smallint',
    'IntegerField': 'int',
    'BigIntegerField': 'bigint',
    'SmallIntegerField': 'smallint',
    'PositiveIntegerField': 'int',
    'PositiveBigIntegerField': 'bigint',
    'PositiveSmallIntegerField': 'smallint',
    'FloatField': 'float',
    'DecimalField': 'decimal',
    'CharField': 'string',
    'TextField': 'text',
    'EmailField': 'string',
    'URLField': 'string',
    'SlugField': 'string',
    'UUIDField': 'uuid',
    'BooleanField': 'bool',
    'NullBooleanField': 'bool',
    'DateField': 'date',
    'DateTimeField': 'datetime',
    'TimeField': 'time',
    'DurationField': 'duration',
    'BinaryField': 'binary',
    'FileField': 'file',
    'ImageField': 'image',
    'FilePathField': 'string',
    'JSONField': 'json',
    'IPAddressField': 'string',
    'GenericIPAddressField': 'string',
    'ForeignKey': 'int',
    'OneToOneField': 'int',
    'ManyToManyField': 'int',
    # Wagtail 特有的欄位
    'RichTextField': 'text',
    'StreamField': 'json',
    # 其他
    'TreeForeignKey': 'int',
    'ParentalKey': 'int',
    'ParentalManyToManyField': 'int',
}


def sanitize_name(name: str) -> str:
    """
    清理名稱，確保符合 Mermaid 標識符規則
    - 移除或替換特殊字符
    - 確保以字母開頭
    """
    # 替換非字母數字的字符為空
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', name)
    # 確保以字母開頭
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'E' + sanitized
    return sanitized or 'Entity'


def get_mermaid_field_type(django_field_type: str) -> str:
    """將 Django 欄位類型轉換為 Mermaid 類型"""
    return FIELD_TYPE_MAPPING.get(django_field_type, 'string')


def get_all_app_labels() -> List[str]:
    """取得所有已安裝的 app labels"""
    # 排除 Django 和第三方套件的 apps
    exclude_prefixes = (
        'django.',
        'wagtail.',
        'rest_framework',
        'corsheaders',
        'taggit',
        'modelcluster',
        'drf_yasg',
        'django_filters',
        'django_ckeditor_5',
        'treebeard',
    )
    
    app_labels = []
    for app_config in apps.get_app_configs():
        module_name = app_config.module.__name__
        # 排除系統 apps
        if not any(module_name.startswith(prefix) for prefix in exclude_prefixes):
            app_labels.append(app_config.label)
    
    return sorted(app_labels)


def get_project_app_labels() -> List[str]:
    """取得專案自己的 app labels (排除所有第三方套件)"""
    # 專案 app 的特徵：通常在專案根目錄下
    project_apps = []
    
    exclude_apps = {
        'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles',
        'wagtailforms', 'wagtailredirects', 'wagtailembeds', 'wagtailsites',
        'wagtailusers', 'wagtailsnippets', 'wagtaildocs', 'wagtailimages',
        'wagtailsearch', 'wagtailadmin', 'wagtailcore', 'wagtail',
        'taggit', 'modelcluster', 'rest_framework', 'corsheaders',
        'drf_yasg', 'django_filters', 'django_ckeditor_5', 'treebeard',
        'token_blacklist', 'authtoken',
    }
    
    for app_config in apps.get_app_configs():
        if app_config.label not in exclude_apps:
            # 確保不是 django 或 wagtail 開頭的模組
            module_name = getattr(app_config.module, '__name__', '')
            if not module_name.startswith(('django.', 'wagtail.', 'rest_framework')):
                project_apps.append(app_config.label)
    
    return sorted(project_apps)


def get_models_for_app(app_label: str) -> List[ModelInfo]:
    """取得指定 app 的所有 models"""
    try:
        app_config = apps.get_app_config(app_label)
        model_list = []
        
        for model in app_config.get_models():
            model_info = parse_model(model)
            if model_info:
                model_list.append(model_info)
        
        return model_list
    except LookupError:
        return []


def parse_model(model) -> Optional[ModelInfo]:
    """解析單個 Model"""
    meta = model._meta
    
    # 跳過抽象模型
    if meta.abstract:
        return None
    
    model_info = ModelInfo(
        name=meta.object_name,
        app_label=meta.app_label,
        verbose_name=str(meta.verbose_name),
        db_table=meta.db_table,
        is_abstract=meta.abstract,
    )
    
    # 解析欄位
    for field_obj in meta.get_fields():
        field_info = parse_field(field_obj)
        if field_info:
            model_info.fields.append(field_info)
        
        # 解析關聯
        relation_info = parse_relation(field_obj, meta)
        if relation_info:
            model_info.relations.append(relation_info)
    
    return model_info


def parse_field(field_obj) -> Optional[FieldInfo]:
    """解析單個欄位"""
    # 跳過反向關聯
    if field_obj.is_relation and not field_obj.concrete:
        return None
    
    # 跳過 ManyToMany (單獨處理關聯)
    if isinstance(field_obj, ManyToManyField):
        return None
    
    field_type_name = field_obj.__class__.__name__
    mermaid_type = get_mermaid_field_type(field_type_name)
    
    # 取得欄位屬性
    is_pk = getattr(field_obj, 'primary_key', False)
    is_fk = isinstance(field_obj, (ForeignKey, OneToOneField))
    is_nullable = getattr(field_obj, 'null', False)
    max_length = getattr(field_obj, 'max_length', None)
    verbose_name = str(getattr(field_obj, 'verbose_name', ''))
    
    return FieldInfo(
        name=field_obj.name,
        field_type=mermaid_type,
        is_pk=is_pk,
        is_fk=is_fk,
        is_nullable=is_nullable,
        max_length=max_length,
        verbose_name=verbose_name,
    )


def parse_relation(field_obj, meta) -> Optional[RelationInfo]:
    """解析關聯"""
    if not field_obj.is_relation or not field_obj.concrete:
        return None
    
    if isinstance(field_obj, ForeignKey):
        relation_type = 'FK'
    elif isinstance(field_obj, OneToOneField):
        relation_type = 'O2O'
    elif isinstance(field_obj, ManyToManyField):
        relation_type = 'M2M'
    else:
        return None
    
    related_model = field_obj.related_model
    related_meta = related_model._meta
    
    return RelationInfo(
        from_model=meta.object_name,
        from_app=meta.app_label,
        to_model=related_meta.object_name,
        to_app=related_meta.app_label,
        relation_type=relation_type,
        field_name=field_obj.name,
        related_name=getattr(field_obj, 'related_query_name', lambda: '')() or '',
    )


def generate_mermaid_er(
    app_labels: Optional[List[str]] = None,
    show_fields: bool = True,
    show_field_types: bool = True,
    group_by_app: bool = True
) -> str:
    """
    產生 Mermaid erDiagram 語法
    
    Args:
        app_labels: 要包含的 app labels，None 表示全部專案 apps
        show_fields: 是否顯示欄位
        show_field_types: 是否顯示欄位類型
        group_by_app: 是否按 app 分組
    
    Returns:
        Mermaid erDiagram 語法字串
    """
    if app_labels is None:
        app_labels = get_project_app_labels()
    
    all_models: Dict[str, ModelInfo] = {}
    all_relations: List[RelationInfo] = []
    
    # 收集所有 models 和關聯
    for app_label in app_labels:
        models_list = get_models_for_app(app_label)
        for model_info in models_list:
            # 使用清理過的名稱作為 key
            key = f"{sanitize_name(model_info.app_label)}{sanitize_name(model_info.name)}"
            all_models[key] = model_info
            all_relations.extend(model_info.relations)
    
    # 開始產生 Mermaid 語法
    lines = ['erDiagram']
    
    # 產生關聯線
    processed_relations: Set[str] = set()
    for rel in all_relations:
        from_key = f"{sanitize_name(rel.from_app)}{sanitize_name(rel.from_model)}"
        to_key = f"{sanitize_name(rel.to_app)}{sanitize_name(rel.to_model)}"
        
        # 只處理在範圍內的關聯
        if from_key not in all_models:
            continue
        
        # 產生關聯識別符號
        rel_id = f"{from_key}--{to_key}--{rel.field_name}"
        if rel_id in processed_relations:
            continue
        processed_relations.add(rel_id)
        
        # 決定關聯符號 - 使用正確的 Mermaid ER 語法
        if rel.relation_type == 'O2O':
            symbol = '||--||'
        elif rel.relation_type == 'FK':
            symbol = '||--o{'  # 一對多
        else:  # M2M
            symbol = '}o--o{'
        
        # 清理標籤名稱 (只保留字母數字和連字號)
        relation_label = re.sub(r'[^a-zA-Z0-9]', '', rel.field_name)
        if not relation_label:
            relation_label = 'rel'
        
        lines.append(f'    {from_key} {symbol} {to_key} : {relation_label}')
    
    lines.append('')
    
    # 產生 Entity 定義 (按 app 分組)
    if group_by_app:
        current_app = None
        for key, model_info in sorted(all_models.items()):
            if current_app != model_info.app_label:
                current_app = model_info.app_label
                lines.append(f'    %% --- {current_app} ---')
            
            entity_name = f"{sanitize_name(model_info.app_label)}{sanitize_name(model_info.name)}"
            if show_fields and model_info.fields:
                lines.append(f'    {entity_name} {{')
                for field_info in model_info.fields:
                    field_line = _format_field_line(field_info, show_field_types)
                    if field_line:  # 只添加有效的欄位行
                        lines.append(f'        {field_line}')
                lines.append('    }')
            else:
                # 沒有欄位時仍需要定義 entity
                lines.append(f'    {entity_name} {{')
                lines.append(f'        string id')
                lines.append('    }')
    else:
        for key, model_info in sorted(all_models.items()):
            entity_name = f"{sanitize_name(model_info.app_label)}{sanitize_name(model_info.name)}"
            if show_fields and model_info.fields:
                lines.append(f'    {entity_name} {{')
                for field_info in model_info.fields:
                    field_line = _format_field_line(field_info, show_field_types)
                    if field_line:
                        lines.append(f'        {field_line}')
                lines.append('    }')
            else:
                lines.append(f'    {entity_name} {{')
                lines.append(f'        string id')
                lines.append('    }')
    
    return '\n'.join(lines)


def _format_field_line(field_info: FieldInfo, show_type: bool = True) -> str:
    """
    格式化欄位行
    Mermaid ER 圖欄位格式: type name "comment"
    """
    # 清理欄位名稱 (只保留字母數字)
    field_name = re.sub(r'[^a-zA-Z0-9]', '', field_info.name)
    if not field_name:
        return ''
    
    # 清理欄位類型
    field_type = field_info.field_type if show_type else 'string'
    field_type = re.sub(r'[^a-zA-Z0-9]', '', field_type)
    if not field_type:
        field_type = 'string'
    
    # 建立標記註解
    comment_parts = []
    if field_info.is_pk:
        comment_parts.append('PK')
    if field_info.is_fk:
        comment_parts.append('FK')
    
    if comment_parts:
        comment = ','.join(comment_parts)
        return f'{field_type} {field_name} "{comment}"'
    else:
        return f'{field_type} {field_name}'


def get_app_model_stats() -> Dict[str, int]:
    """取得每個 app 的 model 數量統計"""
    stats = {}
    for app_label in get_project_app_labels():
        models_list = get_models_for_app(app_label)
        stats[app_label] = len(models_list)
    return stats


def generate_mermaid_for_single_app(app_label: str) -> str:
    """為單一 app 產生 Mermaid ER 圖"""
    return generate_mermaid_er(
        app_labels=[app_label],
        show_fields=True,
        show_field_types=True,
        group_by_app=False
    )
