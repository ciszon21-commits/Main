from django.core.management.base import BaseCommand
from BudgetReview.models import Project, Discipline

class Command(BaseCommand):
    help = '為所有現有標案補充整合專業（代碼00）'

    def handle(self, *args, **options):
        projects = Project.objects.all()
        created_count = 0
        skipped_count =0
        
        for project in projects:
            # 檢查是否已有整合專業
            if not project.disciplines.filter(is_overall=True).exists():
                # 創建整合專業
                first_admin = project.admins.first()
                Discipline.objects.create(
                    project=project,
                    code='00',
                    name='整合',
                    is_overall=True,
                    responsible_user=first_admin
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 為標案「{project.name}」創建整合專業')
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(f'○ 標案「{project.name}」已有整合專業，跳過')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n完成！共創建 {created_count} 個整合專業，跳過 {skipped_count} 個')
        )
