from functools import cached_property
import re
from typing import (
    Type,
    TYPE_CHECKING,
)

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend

from SinoExtension.tools import is_app_ready
from StudioBase.services import get_user_json

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from UserProfile.models import UserProfile




class SinoRemoteUserBackend(RemoteUserBackend):
    _username:'str' = None
    def clean_username(self, username):
        return re.sub(r'[\\\\/:\*\?"<>\|]', '_', username)


    def authenticate(self, request, remote_user):
        """ 認證使用者
        查詢 或 新增 sino 使用者
        """
        if not remote_user:
            return
        UserModel = get_user_model()
        self._username = self.clean_username(remote_user).upper()
        user = self.catch_user()
        if user:
            self.configure_user(request, user)
            return user
        domain, emp_no = self.parsed_un
        if not emp_no:
            # 不是有效的 中興人員 格式
            return
        if not self.user_detail:
            # 沒有找到這個 中興人員 相關的資料
            return
        user = UserModel(
            username=self._username,
            email=self.user_detail['emp_email'],
            first_name=self.user_detail['emp_name'][:1],
            last_name=self.user_detail['emp_name'][1:],
        )
        if not user.is_superuser:
            user.set_unusable_password()
        user.save()
        self.configure_user(request, user)
        return super().authenticate(request, remote_user)

    def configure_user(self, request, user:'User'):
        """ 設定使用者資料
        """
        UserProfile = self.user_profile_cls
        if not UserProfile:
            # 沒有 UserProfile 模組
            return
        if not self.user_detail:
            # 沒有找到這個 中興人員 相關的資料
            return
        user.email = self.user_detail['emp_email']
        user.last_name = self.user_detail['emp_name'][1:]
        user.first_name = self.user_detail['emp_name'][:1]
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.emp_name = self.user_detail['emp_name']
        profile.emp_email = self.user_detail['emp_email']
        profile.emp_dept = self.user_detail['emp_dept']
        profile.emp_company = self.user_detail['emp_company']
        profile.save()
        return super().configure_user(request, user)



    @property
    def user_profile_cls(self) -> 'Type[UserProfile]|None':
        if not is_app_ready('UserProfile'):
            return None
        from UserProfile.models import UserProfile
        return UserProfile


    @cached_property
    def user_detail(self):
        if not self._username:
            return None
        _, emp_no = self.parsed_un
        return get_user_json(emp_no=emp_no)
    @cached_property
    def parsed_un(self) -> 'tuple[str,str]':
        if not self._username:
            return ('', '')
        domain, emp_no = self.parse_username(self._username)
        return (
            domain,
            emp_no.rjust(5, '0'),
        )


    def parse_username(self, username:'str') -> 'tuple[str,str]':
        """ 解析使用者名稱，提取 domain 和 emp_no
        """
        # 純數字 -> ('', emp_no)
        if username.isdigit():
            return ('', username)
        # 有底線且最後一個底線後是數字 -> (domain, emp_no)
        match = re.match(r'^(.+)_(\d+)$', username)
        if match:
            return match.groups()
        # 其他情況 -> (domain, '')
        return (username, '')

    def catch_user(self):
        UserModel = get_user_model()
        domain, emp_no = self.parsed_un
        if emp_no:
            return UserModel.objects.filter(username__endswith=emp_no).first()
        return UserModel.objects.filter(username=domain).first()



