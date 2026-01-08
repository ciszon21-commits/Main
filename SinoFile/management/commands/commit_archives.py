"""
commit_archives Management Command
====================================
Phase 3 of Two-Phase Commit: 確認並提交封存

前置條件:
    - Phase 1 (pack_archives) 已執行，ArchiveFolder 狀態為 CLOSED
    - Phase 2 (手動) 管理員已將資料夾從 /mnt/tmp_data/ 移動到 /mnt/cold_storage/

功能:
1. 掃描狀態為 CLOSED 的 ArchiveFolder
2. 驗證資料夾和檔案是否存在於冷儲存區
3. 更新業務模型的 FileField 為 archived://{FolderName}/{UUID}.{ext}
4. 刪除原始熱檔案
5. 更新 ArchiveFolder 狀態為 ARCHIVED

使用方式:
    python manage.py commit_archives
    python manage.py commit_archives --folder=VOL_20260108
    python manage.py commit_archives --dry-run
"""

import os
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from SinoFile.models import ArchiveFolder
from SinoFile.utils import (
    build_archive_path,
    get_cold_path,
    verify_cold_file,
    verify_cold_folder,
)


class Command(BaseCommand):
    help = '驗證冷儲存並提交封存變更 (Phase 3 of Two-Phase Commit)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            default=None,
            help='指定要處理的資料夾名稱（預設處理所有 CLOSED 狀態的資料夾）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬執行，不實際更新資料庫或刪除檔案',
        )
        parser.add_argument(
            '--skip-delete',
            action='store_true',
            help='跳過刪除原始熱檔案（用於測試）',
        )
    
    def handle(self, *args, **options):
        folder_name = options['folder']
        dry_run = options['dry_run']
        skip_delete = options['skip_delete']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE ==='))
        
        # 取得待處理的資料夾
        if folder_name:
            folders = ArchiveFolder.objects.filter(
                folder_name=folder_name,
                status=ArchiveFolder.Status.CLOSED
            )
            if not folders.exists():
                self.stdout.write(self.style.ERROR(
                    f'找不到狀態為 CLOSED 的資料夾: {folder_name}'
                ))
                return
        else:
            folders = ArchiveFolder.objects.filter(
                status=ArchiveFolder.Status.CLOSED
            )
        
        if not folders.exists():
            self.stdout.write(self.style.NOTICE('沒有待處理的 CLOSED 資料夾'))
            return
        
        for archive_folder in folders:
            self._process_folder(archive_folder, dry_run, skip_delete)
    
    def _process_folder(self, archive_folder: ArchiveFolder, dry_run: bool, skip_delete: bool):
        """處理單一封存資料夾"""
        folder_name = archive_folder.folder_name
        self.stdout.write(f'\n處理資料夾: {folder_name}')
        self.stdout.write('=' * 50)
        
        # Step 1: 驗證資料夾存在於冷儲存區
        if not verify_cold_folder(folder_name):
            self.stdout.write(self.style.ERROR(
                f'驗證失敗: 資料夾 {folder_name} 不存在於冷儲存區\n'
                f'請確認已將 {folder_name} 從暫存區移動到冷儲存區'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✓ 資料夾存在於冷儲存區'))
        
        # Step 2: 驗證所有檔案
        files = archive_folder.manifest_data.get('files', [])
        missing_files = []
        
        for file_info in files:
            uuid_filename = file_info.get('uuid_filename')
            if not verify_cold_file(folder_name, uuid_filename):
                missing_files.append(uuid_filename)
        
        if missing_files:
            self.stdout.write(self.style.ERROR(
                f'驗證失敗: 以下檔案不存在於冷儲存區:'
            ))
            for f in missing_files[:10]:
                self.stdout.write(f'  - {f}')
            if len(missing_files) > 10:
                self.stdout.write(f'  ... 還有 {len(missing_files) - 10} 個檔案')
            return
        
        self.stdout.write(self.style.SUCCESS(f'✓ 所有 {len(files)} 個檔案已驗證'))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE(
                f'[DRY RUN] 將會更新 {len(files)} 筆資料庫記錄'
            ))
            for file_info in files[:5]:
                archive_path = build_archive_path(folder_name, file_info['uuid_filename'])
                self.stdout.write(f'  {file_info["original_path"]} -> {archive_path}')
            if len(files) > 5:
                self.stdout.write(f'  ... 還有 {len(files) - 5} 筆')
            return
        
        # Step 3: 更新資料庫記錄並刪除熱檔案
        success_count = 0
        error_count = 0
        
        for file_info in files:
            try:
                with transaction.atomic():
                    result = self._update_file_record(
                        file_info, folder_name, skip_delete
                    )
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'處理失敗: {file_info.get("original_path")} - {e}'
                ))
                error_count += 1
        
        # Step 4: 更新資料夾狀態
        if error_count == 0:
            archive_folder.archive()
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ 資料夾 {folder_name} 已標記為 ARCHIVED'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ 有 {error_count} 個檔案處理失敗，資料夾狀態維持 CLOSED'
            ))
        
        # 輸出統計
        self.stdout.write(f'\n處理完成:')
        self.stdout.write(f'  成功: {success_count}')
        self.stdout.write(f'  失敗: {error_count}')
    
    def _update_file_record(self, file_info: dict, folder_name: str, skip_delete: bool) -> bool:
        """
        更新單一檔案記錄
        
        Two-Phase Commit Phase 3:
        1. 更新業務模型的 FileField 為 archived:// 路徑
        2. 刪除原始熱檔案
        """
        model_label = file_info.get('model_label')
        field_name = file_info.get('field_name')
        instance_pk = file_info.get('instance_pk')
        original_path = file_info.get('original_path')
        uuid_filename = file_info.get('uuid_filename')
        
        # 取得模型類別
        try:
            model_class = apps.get_model(model_label)
        except LookupError:
            self.stdout.write(self.style.ERROR(f'找不到模型: {model_label}'))
            return False
        
        # 取得實例
        try:
            instance = model_class.objects.get(pk=instance_pk)
        except model_class.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'跳過: {model_label} pk={instance_pk} 已不存在'
            ))
            return True  # 視為成功（不需處理）
        
        # 檢查目前的檔案路徑是否仍為原始路徑
        current_path = getattr(instance, field_name).name
        if current_path != original_path:
            self.stdout.write(self.style.WARNING(
                f'跳過: {model_label} pk={instance_pk} 的 {field_name} 已變更\n'
                f'  期望: {original_path}\n'
                f'  目前: {current_path}'
            ))
            return True  # 視為成功（已被其他流程處理）
        
        # 建構新的 archived:// 路徑
        archive_path = build_archive_path(folder_name, uuid_filename)
        
        # 更新資料庫記錄
        setattr(instance, field_name, archive_path)
        instance.save(update_fields=[field_name])
        
        self.stdout.write(f'  更新: {model_label} pk={instance_pk}')
        
        # 刪除原始熱檔案
        if not skip_delete:
            try:
                hot_file_path = Path(settings.MEDIA_ROOT) / original_path
                if hot_file_path.exists():
                    hot_file_path.unlink()
                    self.stdout.write(f'  刪除: {original_path}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'  警告: 無法刪除熱檔案 {original_path}: {e}'
                ))
        
        return True
