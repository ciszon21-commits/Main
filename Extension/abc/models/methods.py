import re
from typing import overload
from typing import (
    Any,
    Callable,
    Type,
    TypedDict,
    TypeVar,
)
from uuid import UUID

from datetime import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import connection
from django.db import models

from Extension.abc import MyTime



_T = TypeVar('_T', bound=models.Model)

SqlFormat = TypedDict('SqlFormat', {
    'select': 'str',
    'from': 'str',
    'where': 'str'
})






def model_meta(model:'_T|Type[_T]') -> 'None':
    if hasattr(model, '_meta'): return model._meta
    return model.__class__._meta

def model_fields(model:'_T|Type[_T]', primaryKey:'bool'=False) -> 'list[models.Field]':
    meta = model_meta(model)
    if primaryKey: return [f for f in meta.fields]
    return [f for f in meta.fields if not f.primary_key]
def model_field(model:'_T|Type[_T]', fieldName:'str') -> 'models.Field':
    fields = model_fields(model, primaryKey=True)
    return next(filter(lambda f: f.name==fieldName, fields), None)




def model_update(model:'_T', primaryKey:'bool'=False, save:'bool'=True, **kwargs) -> '_T':
    """ 可以用不嚴謹資料更新 model 的方法
    * model: 要更新的 model 本人
    * primaryKey: 是否要套用更新 pk
    * save: 更新後是否直接儲存
    * kwargs: 要更新的欄位資料
    """
    fields = model_fields(model, primaryKey=primaryKey)
    for k, v in kwargs.items():
        f = next(filter(lambda f: check_key_is_field(k, v, f), fields), None)
        if not f: continue
        k, v = format_key_value(k, v, f)
        if not k: continue
        setattr(model, k, v)
    if save: model.save()
    return model



def model_serializer(model:'models.Model', toJson:'bool'=True) -> 'dict':
    """ 不透過 rest api 的 serializer
    """
    fields = model_fields(model, primaryKey=True)
    return {f.name: format_field_value(model, f, toJson) for f in fields}




# sqlPathChain(ReportSection, **kwargs)
@overload
def sql_path_chain(
        modelType:'Type[_T]',
        chainField:'str',
        delimiter:'str'='-',
        parentField:'str'='parent_id',
        **kwargs
    ) -> 'list[_T]': ...
def sql_path_chain(modelType:'Type[_T]', **kwargs) -> 'list[_T]':
    """ 用遞迴的方式查詢資料
    """
    with connection.cursor() as cursor:
        sqlStr = model_path_chain_sql_str(**kwargs)
        cursor.execute(sqlStr)
        rows = cursor.fetchall()
        rowModels = format_list_2_models(modelType, rows)
    return rowModels



def format_list_2_models(modelType:'Type[_T]', datas:'list[list]') -> 'list[_T]':
    """ 把多個資料庫 connection.cursor.fetch 的 list 轉成 model 的方法
    """
    d2mLam:'Callable[[list],_T]' = lambda d: format_list_2_model(modelType, d)
    return list(map(d2mLam, datas))
def format_list_2_model(modelType:'Type[_T]', data:'list') -> '_T':
    """ 把資料庫 connection.cursor.fetch 的 list 轉成 model 的方法
    """
    fields = modelType._meta.fields
    if len(fields) != len(data): return None
    context = dict(zip(fields, data))
    return modelType(**context)






def check_key_is_field(key:'str', value:'Any', field:'models.Field') -> 'bool':
    if isinstance(field, models.ForeignKey):
        return check_key_is_foreign_key(key, value, field)
    return check_key_is_normal_field(key, value, field)
def check_key_is_normal_field(key:'str', value:'Any', field:'models.Field') -> 'bool':
    return key == field.name
def check_key_is_foreign_key(key:'str', value:'Any', field:'models.Field') -> 'bool':
    if key == field.name: return True
    if key == f'{field.name}_id': return True
    return False

def format_key_value(key:'str', value:'Any', field:'models.Field',) -> 'tuple[str,Any]':
    # TODO 有空的時候了解一下要怎麼解
    # if isinstance(field, models.FileField):
    #     return formatKeyValueFileField(key, value, field)
    if isinstance(field, models.ForeignKey):
        return format_key_value_foreign_key(key, value, field)
    if isinstance(field, models.DateTimeField):
        return format_key_value_date_time(key, value, field)
    return format_key_value_normal(key, value, field)
def format_key_value_normal(key:'str', value:'Any', field:'models.Field') -> 'tuple[str,Any]':
    return (key, value)
def format_key_value_date_time(key:'str', value:'Any', field:'models.DateTimeField') -> 'tuple[str,datetime]':
    if not value: return (None, None)
    val = MyTime.format_datetime(value)
    return (key, val)
def format_key_value_foreign_key(key:'str', value:'Any', field:'models.Field') -> 'tuple[str,Any]':
    keyIsId = key.endswith('_id')
    valIsModel = isinstance(value, models.Model)
    if valIsModel and keyIsId: return (key, value.pk)
    if valIsModel and not keyIsId: return (key, value)
    if not valIsModel and keyIsId: return (key, value)
    if not valIsModel and not keyIsId: return (f'{key}_id', value)
    return (None, None)
# def formatKeyValueFileField(key:'str', value:'InMemoryUploadedFile', field:'models.Field') -> 'tuple[str,InMemoryUploadedFile]':
#     return (key, value)



def format_field_value(model:'models.Model', field:'models.Field', toJson:'bool'=True):
    attr = getattr(model, field.name)
    if not toJson: return attr
    if not attr: return attr
    if isinstance(field, models.ForeignKey):
        attr = attr.pk
    elif isinstance(field, datetime):
        attr = attr.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(attr, UUID):
        attr = str(attr)
    return attr







def model_path_chain_sql_str(
        modelType:'Type[_T]',
        chainField:'str',
        delimiter:'str'='-',
        parentField:'str'='parent_id',
        **kwargs
    ) -> 'str':
    """ 用遞迴的方式進行查詢的 SQL 語法
    * modelType: model class 本人
    * chainField: 要進行串連的那個欄位 (ex: name)
    * delimiter: 各個欄位中間的字 (ex: 2019-20 的 '-')
    * parentField: 紀錄上一層的那個欄位 (要使用 sql 內的欄位，FK 要加 _id)
    * kwargs: 本來要 filter 的 dict
    """
    tName = 't'
    rName = 'r'
    cTempField = 'chain_path',
    pkField = modelType._meta.pk.name
    sqlDict = qs_sql_format(modelType, **kwargs)
    csSelect = sqlDict['select']
    cusSelect = qs_sql_select(sqlDict['select'], tName=tName)
    csCast = qs_chain_sql_cast(chainField, cTempField)
    cusCast = qs_chain_union_sql_cast(chainField, cTempField, delimiter, tName, rName)
    whereStr = 'WHERE %s' %(sqlDict['where']) if sqlDict['where'] else ''
    sqlStr = """
        ;WITH PathChain AS (
            SELECT {6}, {8}
            FROM {0}
            WHERE [{3}] IS NULL

            UNION ALL

            SELECT {7}, {9}
            FROM {0} AS {2}
            INNER JOIN PathChain AS {3}
                ON {2}.[{4}] = {3}.[{5}]
        )
        SELECT * FROM PathChain {1};
    """.format(
        sqlDict['from'],    # 0
        whereStr,           # 1
        tName,              # 2
        rName,              # 3
        parentField,        # 4
        pkField,            # 5
        csSelect,           # 6
        cusSelect,          # 7
        csCast,             # 8
        cusCast,            # 9
    )
    return re.sub(r'[\s\r\n\t]+', ' ', sqlStr)

def qs_sql_format(modelType:'Type[_T]', **kwargs) -> 'SqlFormat':
    qs = modelType.objects.filter(**kwargs)
    pattern = r'SELECT (?P<select>.+)\s*FROM (?P<from>.+)(\s*WHERE (?P<where>.+))?'
    match = re.search(pattern, str(qs.query), flags=re.IGNORECASE)
    if not match: return {}
    return match.groupdict()

def qs_sql_select(select:'str', tName:'str'=None) -> 'str':
    if tName is None: return select
    ctfLam = lambda s: '%s.%s' %(tName, s)
    sList = re.split(r'[,\s]+', select)
    return list(map(ctfLam, sList))
def qs_chain_sql_cast(chainField:'str', cTempField:'str'='chain_path') -> 'str':
    return 'CAST([{0}] AS VARCHAR(MAX)) AS {1}'.format(chainField, cTempField)
def qs_chain_union_sql_cast(chainField:'str', cTempField:'str'='chain_path', delimiter:'str'='-', tName:'str'='t', rName:'str'='r') -> 'str':
    return 'CAST({1}.[{3}] + \'{4}\' + {0}.[{2}] AS VARCHAR(MAX)) AS {3}'.format(tName, rName, chainField, cTempField, delimiter)

# def qsChainSqlSelect(select:'str', chainField:'str', cTempField:'str'='chain_path') -> 'str':
#     chainStr = 'CAST([{0}] AS VARCHAR(MAX)) AS {1}'.format(chainField, cTempField)
#     sList = re.split(r'[,\s]+', select)
#     sList.append(chainStr)
#     return ', '.join(sList)
# def qsChainUnionSqlSelect(select:'str', chainField:'str', cTempField:'str'='chain_path', delimiter:'str'='-', tName:'str'='t', rName:'str'='r') -> 'str':
#     ctfLam = lambda s: '%s.%s' %(tName, s)
#     chainStr = 'CAST({1}.[{3}] + \'{4}\' + {0}.[{2}] AS VARCHAR(MAX)) AS {3}'.format(tName, rName, chainField, cTempField, delimiter)
#     sList = re.split(r'[,\s]+', select)
#     sList = list(map(ctfLam, sList))
#     sList.append(chainStr)
#     return ', '.join(sList)


