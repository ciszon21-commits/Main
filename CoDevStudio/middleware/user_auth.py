import re
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin

from SinoExtension.tools import is_app_ready

if TYPE_CHECKING:
    from BimAuth.models import BIMToken



DATABASES:'dict[str,dict]' = getattr(settings, 'DATABASES', {})

FROM_SAFE_APP = [
    'Single_Redirect',
]

SINO_USERNAME_STR = 'SINO-TOKEN_%s'


class UserAuthMiddleware(MiddlewareMixin):
    def process_request(self, request:'HttpRequest'):
        if not self._need_bim_auth_login(request): return
        token = self._catch_bim_token(request)
        if not token or not token.can_use(): return
        user = self._catch_token_user(request, token)
        if not user: return
        self._login_user(request, user, token)

    def _need_bim_auth_login(self, request:'HttpRequest') -> 'bool':
        if request.user.is_authenticated:  # 使用者已經登入了
            return False
        if 'bimauth' not in DATABASES:  # 沒有 bimauth 資料庫
            return False
        return True
    def _catch_bim_token(self, request:'HttpRequest') -> 'BIMToken|None':
        if not is_app_ready('BimAuth'): return None
        token_str = self._get_token_str(request)
        if not token_str: return None
        from BimAuth.models import BIMToken
        return BIMToken.objects.filter(token=token_str).first()
    def _catch_token_user(self, request, token:'BIMToken') -> 'User|None':
        user_s = self._catch_token_user_strong(token)
        if user_s: return user_s
        user_w = self._catch_token_user_weak(token)
        if user_w: return user_w
        user_srt = self._create_safe_app_token_user(token)
        if user_srt: return user_srt
        return None
    def _login_user(self, request:'HttpRequest', user:'User', token:'BIMToken'):
        auth_user = (
            authenticate(request, remote_user=user.username)
            or user
        )
        login(request, auth_user, backend='django.contrib.auth.backends.ModelBackend')
        token.use(used_app='%s.%s' %('KMW', self.__class__.__name__))


    def _get_token_str(self, request:'HttpRequest') -> 'str|None':
        req_data = {}
        req_data.update(request.GET.dict())
        req_data.update(request.POST.dict())
        if 'token' in req_data:
            return req_data['token']
        if 'next' in req_data:
            token_pattern = r'(?:\?|%3F).*?token(?:\=|%3D)(?P<token>\w{8}-?\w{4}-?\w{4}-?\w{4}-?\w{12})(?:\&|%26)?'
            search = re.search(token_pattern, req_data['next'], flags=re.IGNORECASE)
            if search:
                return search.group('token')
        return None

    def _catch_token_user_strong(self, token:'BIMToken') -> 'User|None':
        fQ = (
            Q(username__endswith=token.emp_no_5)
            & Q(email=token.email)
            & Q(is_active=True)
        )
        return User.objects.filter(fQ).first()
    def _catch_token_user_weak(self, token:'BIMToken') -> 'User|None':
        fQ = (
            Q(username__endswith=token.emp_no_4)
            & Q(is_active=True)
        )
        users = User.objects.filter(fQ)
        if users.count() == 1:
            return users.first()
        return None
    def _create_safe_app_token_user(self, token:'BIMToken') -> 'User|None':
        if token.created_app not in FROM_SAFE_APP:
            return None
        username = SINO_USERNAME_STR %(str(token.emp_no_5))
        user = User()
        user.username = username
        user.set_unusable_password()
        user.save()
        return user


