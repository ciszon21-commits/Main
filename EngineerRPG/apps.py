from django.apps import AppConfig


class EngineerrpgConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'EngineerRPG'
    
    def ready(self):
        """應用程式準備就緒時的初始化動作"""
        # 載入 signals 以處理 User 創建時的自動權限設置
        import EngineerRPG.signals
