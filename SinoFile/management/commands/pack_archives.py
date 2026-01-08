"""
pack_archives Management Command
=================================
Phase 1 of Two-Phase Commit: 打包待封存檔案

邏輯:
1. 掃描所有已註冊的 SmartArchiveField
2. 計算所有待封存檔案的總大小
3. 若總大小 >= 4GB，則開始封存
4. 每個封存資料夾不超過 4GB
5. **不更新**業務模型的 DB 記錄（網站仍提供原始檔案）

使用方式:
    python manage.py pack_archives
    python manage.py pack_archives --dry-run
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from SinoFile.models import ArchiveFolder
from SinoFile.registry import get_archivable_fields
from SinoFile.utils import (
    get_file_extension,
    get_max_folder_size,
    get_staging_path,
    is_archived,
)


class Command(BaseCommand):
    help = '掃描並打包待封存的熱檔案 (Phase 1 of Two-Phase Commit)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬執行，不實際複製檔案',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制執行，即使總大小不足 4GB',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        max_folder_size = get_max_folder_size()
        
        self.stdout.write(self.style.NOTICE(
            f'掃描待封存檔案... (觸發門檻: {self._human_size(max_folder_size)})'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE ==='))
        
        # Step 1: 收集所有待封存檔案資訊
        archivable_fields = get_archivable_fields()
        
        if not archivable_fields:
            self.stdout.write(self.style.WARNING(
                '未找到已註冊的可封存欄位。\n'
                '請在各 App 的 apps.py ready() 中使用 register_archivable_field() 註冊。'
            ))
            return
        
        # 取得已在 manifest 中的檔案（冪等性檢查）
        existing_files = self._get_existing_manifest_files()
        
        # 掃描所有可封存檔案
        candidate_files = []
        total_candidate_size = 0
        
        for model_class, field_name in archivable_fields:
            model_label = f'{model_class._meta.app_label}.{model_class._meta.model_name}'
            self.stdout.write(f'\n掃描 {model_label}.{field_name}...')
            
            queryset = model_class.objects.all()
            
            for instance in queryset:
                file_field = getattr(instance, field_name)
                
                # 跳過空檔案
                if not file_field or not file_field.name:
                    continue
                
                file_path = file_field.name
                
                # 跳過已封存的檔案
                if is_archived(file_path):
                    continue
                
                # 冪等性檢查：跳過已在 manifest 中的檔案
                if file_path in existing_files:
                    continue
                
                # 取得檔案大小
                try:
                    full_path = Path(settings.MEDIA_ROOT) / file_path
                    if not full_path.exists():
                        self.stdout.write(self.style.WARNING(
                            f'  檔案不存在: {file_path}'
                        ))
                        continue
                    
                    file_size = full_path.stat().st_size
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'  無法讀取檔案: {file_path} ({e})'
                    ))
                    continue
                
                candidate_files.append({
                    'file_path': file_path,
                    'full_path': full_path,
                    'file_size': file_size,
                    'model_label': model_label,
                    'field_name': field_name,
                    'instance_pk': instance.pk,
                })
                total_candidate_size += file_size
        
        # Step 2: 檢查是否達到封存門檻 (4GB)
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'待封存檔案: {len(candidate_files)} 個')
        self.stdout.write(f'待封存總大小: {self._human_size(total_candidate_size)}')
        self.stdout.write(f'封存門檻: {self._human_size(max_folder_size)}')
        
        if total_candidate_size < max_folder_size and not force:
            self.stdout.write(self.style.NOTICE(
                f'\n待封存總大小 ({self._human_size(total_candidate_size)}) '
                f'未達門檻 ({self._human_size(max_folder_size)})，跳過封存。\n'
                f'使用 --force 參數可強制執行。'
            ))
            return
        
        if force and total_candidate_size < max_folder_size:
            self.stdout.write(self.style.WARNING('使用 --force 強制執行封存'))
        
        # Step 3: 開始封存
        self.stdout.write(self.style.SUCCESS('\n開始封存程序...'))
        
        if dry_run:
            self._dry_run_pack(candidate_files, max_folder_size)
            return
        
        # 取得或建立 ArchiveFolder
        archive_folder = self._get_or_create_folder()
        if not archive_folder:
            self.stdout.write(self.style.ERROR('無法取得或建立封存資料夾'))
            return
        
        processed_files = 0
        
        for file_info in candidate_files:
            file_path = file_info['file_path']
            full_path = file_info['full_path']
            file_size = file_info['file_size']
            
            # 檢查資料夾是否還有空間
            if not archive_folder.can_add_file(file_size):
                # 封閉目前資料夾，建立新的
                archive_folder.save()
                archive_folder.close()
                self._write_manifest_file(archive_folder)
                self._write_index_file(archive_folder)
                self.stdout.write(self.style.SUCCESS(
                    f'\n資料夾 {archive_folder.folder_name} 已達上限 '
                    f'({archive_folder.get_human_size()})，狀態設為 CLOSED'
                ))
                archive_folder = self._get_or_create_folder()
            
            # 產生 UUID 檔名
            ext = get_file_extension(file_path)
            uuid_filename = f'{uuid.uuid4().hex}{ext}'
            
            # 複製檔案到暫存區
            success = self._copy_file(
                full_path,
                archive_folder.folder_name,
                uuid_filename
            )
            
            if success:
                # 更新 manifest
                archive_folder.add_to_manifest(
                    original_path=file_path,
                    uuid_filename=uuid_filename,
                    file_size=file_size,
                    model_label=file_info['model_label'],
                    field_name=file_info['field_name'],
                    instance_pk=file_info['instance_pk'],
                )
                processed_files += 1
                self.stdout.write(f'  複製: {file_path} -> {uuid_filename}')
        
        # 儲存 manifest 和 index
        archive_folder.save()
        self._write_manifest_file(archive_folder)
        self._write_index_file(archive_folder)
        
        # 如果資料夾已滿，封閉它
        if archive_folder.get_remaining_space() < 1024 * 1024:  # 小於 1MB
            archive_folder.close()
            self.stdout.write(self.style.SUCCESS(
                f'資料夾 {archive_folder.folder_name} 已滿，狀態設為 CLOSED'
            ))
        
        # 輸出統計
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'封存完成!'))
        self.stdout.write(f'  已處理檔案: {processed_files}')
        self.stdout.write(f'  目前資料夾: {archive_folder.folder_name}')
        self.stdout.write(f'  資料夾狀態: {archive_folder.get_status_display()}')
        self.stdout.write(f'  資料夾大小: {archive_folder.get_human_size()}')
    
    def _get_existing_manifest_files(self) -> set:
        """取得所有 STAGING 狀態資料夾中已有的檔案"""
        existing = set()
        for folder in ArchiveFolder.objects.filter(status=ArchiveFolder.Status.STAGING):
            for f in folder.manifest_data.get('files', []):
                existing.add(f.get('original_path'))
        return existing
    
    def _dry_run_pack(self, candidate_files: list, max_folder_size: int):
        """模擬封存過程"""
        folder_count = 1
        current_folder_size = 0
        
        self.stdout.write(f'\n[DRY RUN] 模擬封存結果:')
        
        for file_info in candidate_files:
            file_size = file_info['file_size']
            
            # 檢查是否需要新資料夾
            if current_folder_size + file_size > max_folder_size:
                self.stdout.write(f'  [資料夾 {folder_count}] 大小: {self._human_size(current_folder_size)}')
                folder_count += 1
                current_folder_size = 0
            
            current_folder_size += file_size
        
        if current_folder_size > 0:
            self.stdout.write(f'  [資料夾 {folder_count}] 大小: {self._human_size(current_folder_size)}')
        
        self.stdout.write(f'\n預計建立 {folder_count} 個封存資料夾')
    
    def _get_or_create_folder(self):
        """
        取得或建立封存資料夾
        
        資料夾命名規則: CODEV + 5位數字 (ID)
        例如: CODEV00001, CODEV00042
        """
        # 取得現有的 STAGING 資料夾
        folder = ArchiveFolder.objects.filter(
            status=ArchiveFolder.Status.STAGING
        ).first()
        
        if folder:
            return folder
        
        # 建立新資料夾（先用暫時名稱）
        folder = ArchiveFolder.objects.create(
            folder_name='_TEMP_',  # 暫時名稱
            max_size=get_max_folder_size(),
        )
        
        # 使用 ID 產生正式名稱: CODEV + 5位數字
        new_name = f'CODEV{folder.pk:05d}'
        folder.folder_name = new_name
        folder.save(update_fields=['folder_name'])
        
        self.stdout.write(self.style.SUCCESS(f'建立新封存資料夾: {new_name}'))
        return folder
    
    def _copy_file(self, source_path: Path, folder_name: str, uuid_filename: str) -> bool:
        """複製檔案到暫存區"""
        try:
            staging_dir = get_staging_path(folder_name)
            staging_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = staging_dir / uuid_filename
            shutil.copy2(source_path, dest_path)
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'複製失敗: {e}'))
            return False
    
    def _write_manifest_file(self, archive_folder: ArchiveFolder):
        """將 manifest 寫入 JSON 檔案"""
        staging_dir = get_staging_path(archive_folder.folder_name)
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = staging_dir / 'manifest.json'
        manifest_data = {
            'folder_name': archive_folder.folder_name,
            'status': archive_folder.status,
            'total_size': archive_folder.total_size,
            'created_at': archive_folder.created_at.isoformat(),
            'files': archive_folder.manifest_data.get('files', []),
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(f'已更新 manifest: {manifest_path}')
    
    def _human_size(self, size: int) -> str:
        """返回人類可讀的檔案大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'
    
    def _write_index_file(self, archive_folder: ArchiveFolder):
        """
        寫入人類可讀的索引檔案
        
        檔案名稱: _{folder_name}.txt
        格式: UUID檔名\t日期\t容量\t原始路徑
        """
        staging_dir = get_staging_path(archive_folder.folder_name)
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        index_filename = f'_{archive_folder.folder_name}.txt'
        index_path = staging_dir / index_filename
        
        files = archive_folder.manifest_data.get('files', [])
        
        with open(index_path, 'w', encoding='utf-8') as f:
            for file_info in files:
                uuid_filename = file_info.get('uuid_filename', '')
                original_path = file_info.get('original_path', '')
                file_size = file_info.get('file_size', 0)
                
                # 取得檔案日期 (從暫存區的檔案)
                try:
                    copied_file_path = staging_dir / uuid_filename
                    if copied_file_path.exists():
                        mtime = copied_file_path.stat().st_mtime
                        file_date = datetime.fromtimestamp(mtime).strftime('%Y/%m/%d %H:%M:%S')
                    else:
                        file_date = '-'
                except Exception:
                    file_date = '-'
                
                # 格式化檔案大小
                size_str = self._human_size(file_size)
                
                # 寫入: UUID檔名  日期  容量  原始路徑
                f.write(f'{uuid_filename}\t{file_date}\t{size_str}\t{original_path}\n')
        
        self.stdout.write(f'已建立索引檔: {index_path}')
