

@admin.register(AdminWhitelist)
class AdminWhitelistAdmin(admin.ModelAdmin):
    """管理者白名單管理"""
    list_display = ['user', 'role', 'granted_by', 'granted_at']
    list_filter = ['role', 'granted_at']
    search_fields = ['user__username', 'granted_by__username', 'notes']
    readonly_fields = ['granted_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('user', 'role')
        }),
        ('授權資訊', {
            'fields': ('granted_by', 'granted_at', 'notes')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """保存時自動設置授權者"""
        if not change:  # 新建時
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)
