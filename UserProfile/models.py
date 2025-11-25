from django.contrib.auth.models import User
from django.db import models

from StudioBase.constants import (
    SINO_COMPANY_DB,
    SINO_DEPT_DB,
)




class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile',on_delete=models.CASCADE)
    is_superuser = models.BooleanField(verbose_name='小超級使用者', default=False, blank=True, null=True)
    emp_name = models.CharField(max_length=20,verbose_name='姓名', blank=True, null=True)
    emp_email = models.CharField(max_length=100,verbose_name='電子郵件', blank=True, null=True)
    emp_dept = models.CharField(max_length=20,verbose_name='部門', blank=True, null=True)
    emp_company = models.CharField(max_length=20,verbose_name='公司', blank=True, null=True)

    def __str__(self): return self.user.username

    @property
    def company_display(self) -> 'str':
        return SINO_COMPANY_DB.get(self.emp_company, '公司')
    @property
    def dept_display(self) -> 'str':
        return SINO_DEPT_DB.get(self.emp_dept, '部門')



