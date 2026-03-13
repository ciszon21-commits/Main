from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("DesignConsistency", "0003_comparisonrun_report_file"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComparisonIssue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "issue_type",
                    models.CharField(
                        choices=[
                            ("unmatched_budget", "Budget only"),
                            ("unmatched_quantity", "Quantity only"),
                            ("unit_mismatch", "Unit mismatch"),
                            ("qty_mismatch", "Quantity mismatch"),
                            ("low_confidence", "Low confidence match"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed mismatch"),
                            ("false_positive", "False positive"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("summary", models.CharField(max_length=255)),
                ("payload", models.JSONField(blank=True, null=True)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="issues",
                        to="DesignConsistency.comparisonrun",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
