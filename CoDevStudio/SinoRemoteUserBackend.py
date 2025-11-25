from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend
from Extension.SinoUser import get_user_json


class SinoRemoteUserBackend(RemoteUserBackend):
    def clean_username(self, username):
        return username.replace('\\', '_')

    def configure_user(self, request, user):
        return user

    def authenticate(self, request, remote_user):
        if not remote_user:
            return
        user_model = get_user_model()
        username = self.clean_username(remote_user).upper()
        
        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            user = user_model(username=username)
            sino_name = get_user_json(username)['emp_name']
            if len(sino_name)>1:
                user.first_name = sino_name[0:1]
                user.last_name = sino_name[1:]

            user.set_unusable_password()
            user.save()
            user = self.configure_user(request, user)
        return user