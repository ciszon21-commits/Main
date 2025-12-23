from django.apps import AppConfig


class BudgetreviewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BudgetReview'
    
    def ready(self):
        import BudgetReview.signals  # 載入signals
