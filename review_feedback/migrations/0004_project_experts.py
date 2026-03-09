from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("review_feedback", "0003_reviewfeedback_new_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="experts",
            field=models.ManyToManyField(
                blank=True,
                related_name="expert_projects",
                to=settings.AUTH_USER_MODEL,
                verbose_name="專家審查員",
            ),
        ),
    ]
