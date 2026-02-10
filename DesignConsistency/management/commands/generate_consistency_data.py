import random
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from DesignConsistency.models import Project, ProjectFile, ComparisonRun

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate test data for DesignConsistency app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of projects to create'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Target username to own the test data'
        )

    def handle(self, *args, **options):
        count = options['count']
        username = options.get('username')
        
        # 1. Get or create a target user
        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'Using specified user: {user.username}')
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User "{username}" not found. Falling back to consistency_tester.'))
                username = None

        if not username:
            user, created = User.objects.get_or_create(
                username='consistency_tester',
                defaults={
                    'email': 'tester@example.com',
                    'first_name': 'Consistency',
                    'last_name': 'Tester'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created test user: {user.username}'))
            else:
                self.stdout.write(f'Using existing test user: {user.username}')

        # 2. Generate Projects
        project_names = [
            "台北大巨蛋興建工程", "高雄衛武營藝術中心", "台中綠美圖", 
            "桃園國際機場第三航廈", "台南美術館", "新北美術館"
        ]
        
        for i in range(count):
            p_name = random.choice(project_names) + f" (Test {random.randint(100, 999)})"
            project = Project.objects.create(
                name=p_name,
                code=f"PRJ-{random.randint(1000, 9999)}",
                description=f"這是一個關於 {p_name} 的自動產生測試專案。",
                owner=user
            )
            self.stdout.write(f"Created project: {project.name}")

            # 3. Create Files for each project
            file_types = [
                (ProjectFile.FILE_TYPE_BUDGET, "budget_sample.xml", b"<budget>dummy</budget>"),
                (ProjectFile.FILE_TYPE_QUANTITY, "quantity_sample.xlsx", b"dummy xlsx content"),
                (ProjectFile.FILE_TYPE_SPEC_PDF, "specification.pdf", b"%PDF-1.4 dummy"),
            ]
            
            created_files = []
            for ft, fname, content in file_types:
                pf = ProjectFile(
                    project=project,
                    file_type=ft,
                    original_name=fname,
                    uploaded_by=user
                )
                pf.file.save(fname, ContentFile(content), save=True)
                created_files.append(pf)
                self.stdout.write(f"  - Created file: {fname} ({ft})")

            # 4. Create Comparison Runs
            budget_file = next((f for f in created_files if f.file_type == ProjectFile.FILE_TYPE_BUDGET), None)
            quantity_file = next((f for f in created_files if f.file_type == ProjectFile.FILE_TYPE_QUANTITY), None)

            if budget_file and quantity_file:
                mock_result = {
                    "summary": {
                        "total_items": 150,
                        "matched": 135,
                        "mismatched": 15,
                        "consistency_rate": 90.0
                    },
                    "mismatches": [
                        {"item_code": "A1-001", "budget_qty": 100, "quantity_qty": 95, "diff": 5},
                        {"item_code": "B2-012", "budget_qty": 50, "quantity_qty": 52, "diff": -2}
                    ]
                }
                
                run = ComparisonRun.objects.create(
                    project=project,
                    budget_file=budget_file,
                    quantity_file=quantity_file,
                    status=ComparisonRun.STATUS_DONE,
                    result=mock_result,
                    notes="自動產生的測試比對結果。"
                )
                self.stdout.write(f"  - Created comparison run: {run}")

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {count} test projects and related data.'))
