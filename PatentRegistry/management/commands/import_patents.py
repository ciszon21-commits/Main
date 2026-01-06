"""
Django management command to import patent data from CSV file.
Usage: python manage.py import_patents [--file FILE_PATH] [--dry-run]
"""
import csv
import re
from datetime import datetime, date
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PatentRegistry.models import PatentApplication, GrantedPatent, PatentAnnuity


class Command(BaseCommand):
    help = '從 CSV 檔案匯入專利資料到資料庫'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='ref/patent.csv',
            help='CSV 檔案路徑 (預設: ref/patent.csv)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模擬匯入，不實際寫入資料庫'
        )
        parser.add_argument(
            '--encoding',
            type=str,
            default='big5',
            help='CSV 檔案編碼 (預設: big5)'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='若資料已存在則更新 (否則跳過)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        encoding = options['encoding']
        update_existing = options['update']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== 模擬匯入模式 (不會寫入資料庫) ==='))

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row
                
                self.stdout.write(f'開始處理 CSV 檔案: {file_path}')
                self.stdout.write(f'欄位: {header}')
                
                created_count = 0
                updated_count = 0
                skipped_count = 0
                error_count = 0
                
                rows = list(reader)
                total_rows = len(rows)
                
                with transaction.atomic():
                    for row_num, row in enumerate(rows, start=2):
                        try:
                            result = self.process_row(row, row_num, update_existing, dry_run)
                            if result == 'created':
                                created_count += 1
                            elif result == 'updated':
                                updated_count += 1
                            elif result == 'skipped':
                                skipped_count += 1
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'第 {row_num} 列處理錯誤: {str(e)}')
                            )
                    
                    if dry_run:
                        # Rollback transaction in dry run mode
                        transaction.set_rollback(True)
                
                # Summary
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=== 匯入結果 ==='))
                self.stdout.write(f'總列數: {total_rows}')
                self.stdout.write(self.style.SUCCESS(f'新增: {created_count}'))
                self.stdout.write(self.style.WARNING(f'更新: {updated_count}'))
                self.stdout.write(f'跳過: {skipped_count}')
                self.stdout.write(self.style.ERROR(f'錯誤: {error_count}'))
                
        except FileNotFoundError:
            raise CommandError(f'找不到檔案: {file_path}')
        except UnicodeDecodeError as e:
            raise CommandError(f'檔案編碼錯誤，請嘗試使用 --encoding 參數指定正確編碼: {str(e)}')

    def process_row(self, row, row_num, update_existing, dry_run):
        """
        處理 CSV 中的一列資料
        
        CSV 欄位對應:
        0: 計畫編號 -> plan_number
        1: 委外編號 -> outsource_number
        2: 項次 -> item_number
        3: 案件內容 -> name (申請專利項目名稱)
        4: 申請專利類別 -> category
        5: 狀態 -> status
        6: 答辯紀錄 (備註使用)
        7: 長江案號 -> firm_case_number (事務所案號)
        8: 專利編號 -> patent_number (GrantedPatent)
        9: 專利名稱 -> patent_name (GrantedPatent)
        10: 專利期間 -> patent_period (GrantedPatent)
        11: 年費繳交期限 (用於計算專利結束日期)
        12: 答辯費 (備註使用)
        13: 取得年度 (GrantedPatent)
        14: 領證+第1年年費 (PatentAnnuity)
        15: 第2年 (PatentAnnuity)
        16: 第3年 (PatentAnnuity)
        """
        # Ensure row has enough columns
        while len(row) < 17:
            row.append('')
        
        plan_number = row[0].strip()
        outsource_number = row[1].strip()
        item_number_str = row[2].strip()
        name = row[3].strip()
        category_str = row[4].strip()
        status_str = row[5].strip()
        rebuttal_notes = row[6].strip()
        firm_case_number = row[7].strip()
        patent_number = row[8].strip()
        patent_name = row[9].strip()
        patent_period = row[10].strip()
        annuity_deadline = row[11].strip()
        rebuttal_fee = row[12].strip()
        granted_year_str = row[13].strip()
        fee_year_1 = row[14].strip()
        fee_year_2 = row[15].strip()
        fee_year_3 = row[16].strip()
        
        # Skip empty rows
        if not plan_number:
            return 'skipped'
        
        # Parse item number
        item_number = self.parse_item_number(item_number_str)
        
        # Map category
        category = self.map_category(category_str)
        
        # Map status
        status = self.map_status(status_str)
        
        # Check if application already exists
        app_exists = PatentApplication.objects.filter(
            plan_number=plan_number,
            outsource_number=outsource_number,
            item_number=item_number
        ).first()
        
        if app_exists and not update_existing:
            self.stdout.write(
                f'第 {row_num} 列: 專利申請已存在，跳過 ({plan_number}/{outsource_number}/{item_number})'
            )
            return 'skipped'
        
        if dry_run:
            action = '更新' if app_exists else '新增'
            self.stdout.write(
                f'[模擬] 第 {row_num} 列: {action} 專利申請 - {plan_number} {name}'
            )
            if patent_number:
                self.stdout.write(f'  -> 已取得專利: {patent_number} {patent_name}')
            return 'updated' if app_exists else 'created'
        
        # Create or update PatentApplication
        if app_exists:
            application = app_exists
            application.name = name
            application.category = category
            application.status = status
            application.firm_case_number = firm_case_number
            application.patent_firm = '長江專利事務所'  # Default firm name based on CSV header
            application.save()
            result = 'updated'
        else:
            application = PatentApplication.objects.create(
                plan_number=plan_number,
                outsource_number=outsource_number,
                item_number=item_number,
                name=name,
                category=category,
                status=status,
                firm_case_number=firm_case_number,
                patent_firm='長江專利事務所'  # Default firm name based on CSV header
            )
            result = 'created'
        
        # Create GrantedPatent if status is APPROVED and patent_number exists
        if status == 'APPROVED' and patent_number:
            start_date, end_date = self.parse_patent_period(patent_period)
            
            granted, created = GrantedPatent.objects.update_or_create(
                application=application,
                defaults={
                    'patent_number': patent_number,
                    'patent_name': patent_name,
                    'patent_period': patent_period,
                    'start_date': start_date,
                    'end_date': end_date,
                }
            )
            
            # Create annuity records for years 1-3 if data exists
            self.create_annuity_records(granted, fee_year_1, fee_year_2, fee_year_3)
        
        self.stdout.write(
            self.style.SUCCESS(f'第 {row_num} 列: {"更新" if result == "updated" else "新增"} - {plan_number} {name}')
        )
        
        return result

    def parse_item_number(self, item_str):
        """解析項次編號，如 #1-1, 01, 1 等"""
        if not item_str:
            return 1
        # Remove # and split by - or other delimiters
        clean = re.sub(r'[#\-]', '', item_str)
        # Extract first number
        match = re.search(r'\d+', clean)
        if match:
            return int(match.group())
        return 1

    def map_category(self, category_str):
        """將 CSV 中的類別對應到 Model 的類別"""
        category_str = category_str.strip()
        if '發明' in category_str:
            return 'INVENTION'
        elif '新型' in category_str:
            return 'UTILITY_MODEL'
        elif '設計' in category_str:
            return 'DESIGN'
        # Default mappings based on common abbreviations
        elif category_str in ['發', '發明']:
            return 'INVENTION'
        elif category_str in ['新', '新型']:
            return 'UTILITY_MODEL'
        elif category_str in ['設', '設計']:
            return 'DESIGN'
        else:
            # Default to INVENTION if unclear
            return 'INVENTION'

    def map_status(self, status_str):
        """將 CSV 中的狀態對應到 Model 的狀態"""
        status_str = status_str.strip().upper()
        if '申請' in status_str or 'PENDING' in status_str:
            return 'PENDING'
        elif '通過' in status_str or '核准' in status_str or 'APPROVED' in status_str:
            return 'APPROVED'
        elif '不通過' in status_str or '駁回' in status_str or 'REJECTED' in status_str:
            return 'REJECTED'
        # Check for specific number patterns like "2+3" which indicates approved stages
        elif re.match(r'\d+\+\d+', status_str):
            return 'APPROVED'
        else:
            # Default to PENDING if unclear
            return 'PENDING'

    def parse_patent_period(self, period_str):
        """
        解析專利期間，如 "2023.12.11~2041.06.22"
        返回 (start_date, end_date)
        """
        if not period_str:
            return date.today(), date(date.today().year + 20, 1, 1)
        
        # Clean up the string
        period_str = period_str.replace('\n', '').replace(' ', '')
        
        # Try to match pattern like "2023.12.11~2041.06.22"
        match = re.search(r'(\d{4}[./]\d{1,2}[./]\d{1,2})\s*[~-]\s*(\d{4}[./]\d{1,2}[./]\d{1,2})', period_str)
        if match:
            start_str = match.group(1)
            end_str = match.group(2)
            start_date = self.parse_date(start_str)
            end_date = self.parse_date(end_str)
            return start_date, end_date
        
        # Fallback to defaults
        return date.today(), date(date.today().year + 20, 1, 1)

    def parse_date(self, date_str):
        """解析日期字串"""
        date_str = date_str.strip()
        # Replace various separators with -
        date_str = re.sub(r'[./]', '-', date_str)
        
        for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return date.today()

    def create_annuity_records(self, granted_patent, fee_year_1, fee_year_2, fee_year_3):
        """創建年費核銷記錄"""
        base_year = granted_patent.start_date.year if granted_patent.start_date else date.today().year
        
        fees = [
            (1, fee_year_1),
            (2, fee_year_2),
            (3, fee_year_3),
        ]
        
        for year_offset, fee_data in fees:
            if not fee_data or not fee_data.strip():
                continue
            
            # Parse fee data - may contain plan number and date
            # Format examples: "5041Z(2022結案)", "(2023.03.25)1005Z"
            plan_match = re.search(r'(\d+[A-Z]+)', fee_data)
            write_off_plan = plan_match.group(1) if plan_match else granted_patent.application.plan_number
            
            # Try to extract year from the data
            year_match = re.search(r'(\d{4})', fee_data)
            write_off_year = int(year_match.group(1)) if year_match else base_year + year_offset - 1
            
            PatentAnnuity.objects.update_or_create(
                granted_patent=granted_patent,
                year=write_off_year,
                defaults={
                    'write_off_plan_number': write_off_plan,
                    'write_off_date': date(write_off_year, 1, 1),
                    'notes': fee_data
                }
            )
