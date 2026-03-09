"""
Django Management Command: import_preset_to_hotspot
====================================================
將 PresetHotspot 的資料批次匯入到 Hotspot（未指定場景的獨立資源庫）。

規則：
    - 若 PresetHotspot 有圖片 → hotspot_type = 'image_hover'（懸浮圖片）
    - 若無圖片               → hotspot_type = 'text_hover'（懸浮文字）
    - 以 preset_source FK 記錄來源，避免重複匯入
    - pitch / yaw 預設 0（未放入場景，待使用者自行放置）

用法：
    python manage.py import_preset_to_hotspot
    python manage.py import_preset_to_hotspot --dry-run
    python manage.py import_preset_to_hotspot --clear
    python manage.py import_preset_to_hotspot --folder 職安署      # 只匯入特定資料夾
    python manage.py import_preset_to_hotspot --overwrite          # 已存在的也更新
"""

from django.core.management.base import BaseCommand
from site360.models import PresetHotspot, Hotspot


class Command(BaseCommand):
    help = "將 PresetHotspot 預設資料庫匯入到 Hotspot（未指定場景的獨立資源）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="僅預覽，不實際寫入資料庫",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="匯入前先清除所有來自 PresetHotspot 的 Hotspot（preset_source 非 null）",
        )
        parser.add_argument(
            "--folder",
            type=str,
            default="",
            help="只處理指定的資料夾名稱（如：職安署、台北勞檢、桃園勞檢），留空則全部",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="若該 PresetHotspot 已有對應 Hotspot，也強制更新",
        )

    def handle(self, *args, **options):
        dry_run   = options["dry_run"]
        clear     = options["clear"]
        folder    = options["folder"].strip()
        overwrite = options["overwrite"]

        # ---- 1. 取得要處理的 PresetHotspot ----
        qs = PresetHotspot.objects.prefetch_related('hazard_types').all()
        if folder:
            qs = qs.filter(source_folder=folder)
            self.stdout.write(f"🔍 只處理資料夾：{folder}")

        total = qs.count()
        self.stdout.write(f"\n📦 PresetHotspot 總計：{total} 筆\n")

        if total == 0:
            self.stdout.write(self.style.WARNING("⚠️  無資料，結束。"))
            return

        # ---- 2. 清除舊資料（可選）----
        if clear and not dry_run:
            del_qs = Hotspot.objects.filter(preset_source__isnull=False)
            if folder:
                del_qs = del_qs.filter(preset_source__source_folder=folder)
            count = del_qs.count()
            del_qs.delete()
            self.stdout.write(self.style.WARNING(f"🗑️  已刪除 {count} 筆舊 Hotspot（preset_source 來源）"))

        # ---- 3. 逐筆處理 ----
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for preset in qs:
            # 判斷 hotspot_type
            if preset.image:
                hotspot_type = 'image_hover'
            else:
                hotspot_type = 'text_hover'

            # 檢查是否已存在
            existing = Hotspot.objects.filter(preset_source=preset).first()

            if existing and not overwrite:
                skipped_count += 1
                continue

            defaults = {
                "hotspot_type": hotspot_type,
                "title": preset.title,
                "description": preset.description,
                "hazard_type": preset.hazard_type, # Keep legacy field
                "image": preset.image if preset.image else None,
                "pitch": 0.0,
                "yaw": 0.0,
                "scene": None,  # 不指定場景，作為獨立資源庫
            }

            # 預覽模式：只顯示不寫入
            if dry_run:
                img_mark = "🖼️ " if preset.image else "📝"
                self.stdout.write(
                    f"  {img_mark} [{preset.source_folder:<6}] {preset.serial_number:3d}. "
                    f"{preset.title[:40]} → {hotspot_type}"
                    + (" [更新]" if existing else " [新增]")
                )
                if existing:
                    updated_count += 1
                else:
                    created_count += 1
                continue

            # 實際寫入
            if existing and overwrite:
                for k, v in defaults.items():
                    setattr(existing, k, v)
                existing.save()
                existing.hazard_types.set(preset.hazard_types.all())
                updated_count += 1
            else:
                new_hotspot = Hotspot.objects.create(preset_source=preset, **defaults)
                new_hotspot.hazard_types.set(preset.hazard_types.all())
                created_count += 1

        # ---- 4. 輸出結果 ----
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  Dry-run 模式，未寫入資料庫。\n"
                f"   預計：新增 {created_count} 筆 | 更新 {updated_count} 筆 | 略過 {skipped_count} 筆"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n🎉 匯入完成！\n"
                f"   新增：{created_count} 筆\n"
                f"   更新：{updated_count} 筆\n"
                f"   略過（已存在，未加 --overwrite）：{skipped_count} 筆"
            ))
