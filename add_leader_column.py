# 新增 leader_id 欄位到資料庫

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        # 新增 leader_id 欄位
        cursor.execute('''
            ALTER TABLE TeamKnowledgeHub_knowledgeteam 
            ADD COLUMN leader_id INTEGER NULL 
            REFERENCES auth_user(id)
        ''')
    print("✓ 成功新增 leader_id 欄位")
except Exception as e:
    if 'duplicate column name' in str(e).lower():
        print("✓ leader_id 欄位已存在")
    else:
        print(f"✗ 錯誤: {e}")
