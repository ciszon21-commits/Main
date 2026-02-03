#!/usr/bin/env python
"""
檢查 Django Admin 註冊狀態
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from django.contrib import admin
from django.contrib.auth.models import User

print("=== Django Admin 註冊檢查 ===\n")

# 檢查 User 模型是否已註冊
if User in admin.site._registry:
    print("✅ User 模型已註冊到 Admin")
    user_admin = admin.site._registry[User]
    print(f"   Admin 類別: {user_admin.__class__.__name__}")
    print(f"   模組: {user_admin.__class__.__module__}")
else:
    print("❌ User 模型未註冊到 Admin")

print("\n所有已註冊的模型：")
for model, model_admin in admin.site._registry.items():
    print(f"  - {model.__name__} ({model._meta.app_label})")

print("\n=== 檢查完成 ===")
