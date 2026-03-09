from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("review_feedback", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="admins",
            field=models.ManyToManyField(
                blank=True,
                related_name="admin_projects",
                to=settings.AUTH_USER_MODEL,
                verbose_name="專案管理員",
            ),
        ),
    ]
