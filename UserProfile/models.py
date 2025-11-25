from django.contrib.auth.models import User
from django.db import models

from .func_models import methods
from Extension.SinoUser import get_user_projects




class UserProfile(models.Model, methods.UserProfileMethod):
    user = models.OneToOneField(User, related_name='profile',on_delete=models.CASCADE)
    is_superuser = models.BooleanField(verbose_name='小超級使用者', default=False, blank=True, null=True)
    emp_name = models.CharField(max_length=20,verbose_name='姓名', blank=True, null=True)
    emp_email = models.CharField(max_length=100,verbose_name='電子郵件', blank=True, null=True)
    emp_dept = models.CharField(max_length=20,verbose_name='部門', blank=True, null=True)
    emp_company = models.CharField(max_length=20,verbose_name='公司', blank=True, null=True)
    def __str__(self): return self.user.username
    def get_emp_no(self):
        return self.user.username.split('_')[1]
    def get_user_projects(self):
        return get_user_projects(self.get_emp_no())['projects']
    @property
    def duty(self):
        return get_user_projects(self.get_emp_no())['duty']


# 使用 Django 的信號來在 User 創建時自動創建 Profile



User.add_to_class('profile', property(methods.UserMethod.get_profile))
User.add_to_class('sino_name', property(methods.UserMethod.get_full_name))
User.add_to_class('create_user_profile', methods.UserMethod.create_user_profile)


