from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("DesignConsistency", "0002_comparisonrun"),
    ]

    operations = [
        migrations.AddField(
            model_name="comparisonrun",
            name="report_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="design_consistency/reports/%Y/%m/%d/",
            ),
        ),
    ]
