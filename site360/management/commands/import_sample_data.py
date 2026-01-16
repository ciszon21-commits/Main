import os
from django.core.management.base import BaseCommand
from django.core.files import File
from site360.models import Project, Scene

class Command(BaseCommand):
    help = 'Import sample data for Danjiang Bridge'

    def handle(self, *args, **options):
        # Using raw string for path to avoid escape issues
        source_dir = r"D:\Vibe Coding 260108\20230216 淡江大橋拍攝"
        project_name = "淡江大橋拍攝 20230216"
        
        if not os.path.exists(source_dir):
            self.stdout.write(self.style.ERROR(f'Source directory not found: {source_dir}'))
            return

        # Create Project
        project, created = Project.objects.get_or_create(
            name=project_name,
            defaults={'description': 'Sample 360 tour imported from source.'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created project "{project_name}"'))
        else:
            self.stdout.write(f'Project "{project_name}" already exists')

        # List files
        try:
            files = sorted([f for f in os.listdir(source_dir) if f.lower().endswith('.jpg')])
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading directory: {e}'))
            return

        for i, filename in enumerate(files):
            file_path = os.path.join(source_dir, filename)
            scene_title = os.path.splitext(filename)[0]
            
            # Check if scene exists
            if Scene.objects.filter(project=project, title=scene_title).exists():
                self.stdout.write(f'Scene "{scene_title}" already exists, skipping.')
                continue

            # Create Scene
            try:
                with open(file_path, 'rb') as f:
                    scene = Scene(
                        project=project,
                        title=scene_title,
                        order=i,
                    )
                    # This copies the file to MEDIA_ROOT/site360/scenes/
                    scene.image.save(filename, File(f), save=True)
                
                self.stdout.write(self.style.SUCCESS(f'Imported scene "{scene_title}"'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to import "{scene_title}": {e}'))
