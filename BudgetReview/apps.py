from django.apps import AppConfig


class BudgetreviewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BudgetReview'
    
    def ready(self):
        import BudgetReview.signals  # 載入signals
        
        from SinoFile.registry import register_archivable_field
        from .models import QuantityFile, PriceInquiryFile, BudgetFile, FinalBudgetFile
        
        register_archivable_field(QuantityFile, 'file')
        register_archivable_field(PriceInquiryFile, 'file')
        register_archivable_field(BudgetFile, 'file')
        register_archivable_field(FinalBudgetFile, 'file')
