import re

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend

from StudioBase.services import get_user_json





class SinoRemoteUserBackend(RemoteUserBackend):
    def clean_username(self, username):
        return re.sub('[\\\\/:\*\?"<>\|]', '_', username)

    def configure_user(self, request, user):
        return user

    def authenticate(self, request, remote_user):
        if not remote_user:
            return
        UserModel = get_user_model()
        username = self.clean_username(remote_user).upper()
        user = UserModel.objects.filter(username=username).first()
        if user:
            return user
        emp_no = self.username_emp_no(username)
        if not emp_no:
            # 不是有效的 中興人員 格式
            return
        user_detail = get_user_json(username)
        if not user_detail:
            # 沒有找到這個 中興人員 相關的資料
            return
        user = UserModel(
            username=username,
            email=user_detail['emp_email'],
            first_name=user_detail['emp_name'][:1],
            last_name=user_detail['emp_name'][1:],
        )
        user.set_unusable_password()
        user.save()
        user = self.configure_user(request, user)
        return user



    def username_emp_no(self, username:'str') -> 'str|None':
        pattern = r'^(?P<domain>.+)_(?P<emp_no>\d+)$'
        match = re.match(pattern, username)
        if not match:
            return None
        return match.group('emp_no')

