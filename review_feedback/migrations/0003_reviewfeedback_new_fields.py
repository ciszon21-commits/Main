from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("review_feedback", "0002_project_admins"),
    ]

    operations = [
        migrations.AddField(
            model_name="reviewfeedback",
            name="correct_classification",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="正確分類"),
        ),
        migrations.AddField(
            model_name="reviewfeedback",
            name="additional_description",
            field=models.TextField(blank=True, default="", verbose_name="手段描述擴充"),
        ),
        migrations.AlterField(
            model_name="reviewfeedback",
            name="feedback_reason",
            field=models.TextField(blank=True, default="", verbose_name="備註說明"),
        ),
    ]
