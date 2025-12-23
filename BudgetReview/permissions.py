"""
權限檢查輔助函數
用於檢查使用者在 BudgetReview 系統中的各種權限
"""
from django.utils import timezone


def has_project_admin_permission(user, project):
    """
    檢查是否為標案管理員或建立者
    
    Args:
        user: 使用者物件
        project: 標案物件
        
    Returns:
        bool: 是否有管理權限
    """
    if user.is_superuser:
        return True
    if user == project.created_by:
        return True
    if user in project.admins.all():
        return True
    return False


def has_discipline_admin_permission(user, discipline):
    """
    檢查是否為專業管理員
    
    Args:
        user: 使用者物件
        discipline: 專業分組物件
        
    Returns:
        bool: 是否有專業管理權限
    """
    if user.is_superuser:
        return True
    if user == discipline.responsible_user:
        return True
    return False


def has_discipline_member_permission(user, discipline):
    """
    檢查是否為專業管理員或成員
    
    Args:
        user: 使用者物件
        discipline: 專業分組物件
        
    Returns:
        bool: 是否有專業操作權限
    """
    if has_discipline_admin_permission(user, discipline):
        return True
    if user in discipline.members.all():
        return True
    return False


def has_budget_permission(user, project):
    """
    檢查是否為預算管理員或成員
    
    Args:
        user: 使用者物件
        project: 標案物件
        
    Returns:
        bool: 是否有預算操作權限
    """
    if user.is_superuser:
        return True
    
    # 檢查是否為任何專業的預算管理員或成員
    for discipline in project.disciplines.all():
        if user == discipline.budget_manager:
            return True
        if user in discipline.budget_members.all():
            return True
    
    return False


def can_submit_file(user, file_obj, check_deadline=True):
    """
    檢查是否可提送檔案
    
    Args:
        user: 使用者物件
        file_obj: 檔案物件
        check_deadline: 是否檢查截止時間
        
    Returns:
        tuple: (bool, str) 是否可提送, 錯誤訊息
    """
    # 超級管理員可以提送任何檔案
    if user.is_superuser:
        return True, ""
    
    # 檢查是否已提送
    if file_obj.is_submitted:
        return False, "檔案已提送，無法重複提送"
    
    # 檢查截止時間（整合專業除外）
    if check_deadline and file_obj.stage and file_obj.stage.deadline:
        if file_obj.discipline and not file_obj.discipline.is_overall:
            if timezone.now() > file_obj.stage.deadline:
                return False, "已超過檔案提送截止時間"
    
    # 根據檔案類型檢查權限
    file_type = type(file_obj).__name__
    
    if file_type == 'QuantityFile' or file_type == 'PriceInquiryFile':
        # 數量計算書與訪價資料：需為專業管理員或成員
        if file_obj.discipline:
            if has_discipline_member_permission(user, file_obj.discipline):
                return True, ""
        return False, "您沒有權限提送此專業的檔案"
    
    elif file_type == 'BudgetFile':
        # 預算書：需為預算管理員或成員
        if has_budget_permission(user, file_obj.project):
            return True, ""
        return False, "您沒有權限提送預算書"
    
    elif file_type == 'FinalBudgetFile':
        # 整合預算書：需為預算管理員
        if has_budget_permission(user, file_obj.project):
            return True, ""
        return False, "您沒有權限提送整合預算書"
    
    return False, "未知的檔案類型"


def can_delete_project(user, project):
    """
    檢查是否可刪除標案（軟刪除）
    
    Args:
        user: 使用者物件
        project: 標案物件
        
    Returns:
        bool: 是否可刪除
    """
    if user.is_superuser:
        return True
    if has_project_admin_permission(user, project):
        return True
    return False


def can_access_hidden_projects(user):
    """
    檢查是否可檢視隱藏標案列表
    
    Args:
        user: 使用者物件
        
    Returns:
        bool: 是否可檢視
    """
    return user.is_superuser


def can_restore_project(user):
    """
    檢查是否可復原標案
    
    Args:
        user: 使用者物件
        
    Returns:
        bool: 是否可復原
    """
    return user.is_superuser


def can_permanent_delete_project(user):
    """
    檢查是否可永久刪除標案
    
    Args:
        user: 使用者物件
        
    Returns:
        bool: 是否可永久刪除
    """
    return user.is_superuser
