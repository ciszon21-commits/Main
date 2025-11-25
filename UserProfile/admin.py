from django.contrib import admin

from . import models


# admin.site.register(models.UserProfile)
@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_superuser',]
    def username(self, obj): return obj.user.username
    username.short_description = '使用者名稱'
    def email(self, obj): return obj.user.email
    email.short_description = '信箱'
