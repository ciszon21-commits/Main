# EngineerRPG/cron.py
"""
定時任務（Cron Jobs）
"""
from .utils import refresh_daily_tasks


def refresh_daily_tasks_job():
    """
    每日刷新任務的 Cron Job
    
    這個函式會在每天凌晨 12 點執行
    """
    refresh_daily_tasks()
