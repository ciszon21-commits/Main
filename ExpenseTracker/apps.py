from django.apps import AppConfig


class ExpenseTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ExpenseTracker'
    verbose_name = '記帳系統'
