from django.db import models
from django.contrib.auth.models import User


class DevTeam(models.Model):
    """開發團隊模型"""
    name = models.CharField(max_length=200, verbose_name="團隊名稱")
    description = models.TextField(blank=True, verbose_name="團隊說明")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_dev_teams',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "開發團隊"
        verbose_name_plural = "開發團隊"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_member(self, user):
        """檢查使用者是否為團隊成員"""
        return self.members.filter(user=user).exists()

    def is_creator(self, user):
        """檢查使用者是否為團隊建立者"""
        return self.created_by == user


class DevTeamMember(models.Model):
    """團隊成員模型"""
    ROLE_CHOICES = [
        ('creator', '建立者'),
        ('member', '成員'),
    ]

    team = models.ForeignKey(
        DevTeam,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="團隊"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dev_team_memberships',
        verbose_name="使用者"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name="角色"
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="加入時間")

    class Meta:
        verbose_name = "團隊成員"
        verbose_name_plural = "團隊成員"
        unique_together = ['team', 'user']
        ordering = ['role', 'joined_at']

    def __str__(self):
        return f"{self.team.name} - {self.user.get_full_name() or self.user.username}"


class DatabaseServer(models.Model):
    """資料庫伺服器模型"""
    name = models.CharField(max_length=200, unique=True, verbose_name="伺服器名稱")
    description = models.TextField(blank=True, verbose_name="說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "資料庫伺服器"
        verbose_name_plural = "資料庫伺服器"
        ordering = ['name']

    def __str__(self):
        return self.name


class Program(models.Model):
    """程式模型"""
    PROGRAM_TYPE_CHOICES = [
        ('web', '網頁'),
        ('desktop', '單機程式'),
        ('plugin', '外掛程式'),
    ]

    team = models.ForeignKey(
        DevTeam,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name="所屬團隊"
    )
    name = models.CharField(max_length=200, verbose_name="程式名稱")
    program_type = models.CharField(
        max_length=20,
        choices=PROGRAM_TYPE_CHOICES,
        verbose_name="程式類型"
    )
    english_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="英文名稱"
    )
    url = models.URLField(blank=True, verbose_name="網址")
    dev_tool = models.CharField(max_length=200, verbose_name="開發工具")
    git_url = models.URLField(verbose_name="Git 網址")
    developers = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="開發者",
        help_text="多位請用逗號分隔"
    )
    maintainers = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="維運者",
        help_text="多位請用逗號分隔"
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name="最後變更時間")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "程式"
        verbose_name_plural = "程式"
        ordering = ['-last_modified', '-created_at']

    def __str__(self):
        return self.name


class ProgramDatabase(models.Model):
    """程式使用資料庫模型"""
    ACCESS_PERMISSION_CHOICES = [
        ('readonly', '唯讀'),
        ('readwrite', '可寫入'),
    ]

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='databases',
        verbose_name="程式"
    )
    server = models.ForeignKey(
        DatabaseServer,
        on_delete=models.PROTECT,
        related_name='databases',
        verbose_name="資料庫伺服器"
    )
    database_name = models.CharField(max_length=200, verbose_name="資料庫名稱")
    table_name = models.CharField(max_length=200, verbose_name="資料表")
    access_permission = models.CharField(
        max_length=20,
        choices=ACCESS_PERMISSION_CHOICES,
        verbose_name="存取權限"
    )

    class Meta:
        verbose_name = "使用資料庫"
        verbose_name_plural = "使用資料庫"
        ordering = ['server__name', 'database_name', 'table_name']

    def __str__(self):
        return f"{self.server.name}/{self.database_name}.{self.table_name}"


# Developer and Maintainer models removed - now using CharField on Program


class FileLocation(models.Model):
    """存取檔案位置模型"""
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='file_locations',
        verbose_name="程式"
    )
    path = models.CharField(max_length=500, verbose_name="檔案路徑")
    description = models.CharField(max_length=200, blank=True, verbose_name="說明")

    class Meta:
        verbose_name = "存取檔案位置"
        verbose_name_plural = "存取檔案位置"
        ordering = ['path']

    def __str__(self):
        return self.path


class DatabaseDesignDoc(models.Model):
    """資料庫設計文件模型"""
    DOC_TYPE_CHOICES = [
        ('manual', '手動建立'),
        ('django', 'Django Model'),
        ('mermaid', 'Mermaid 圖表'),
    ]

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='design_docs',
        verbose_name="程式"
    )
    name = models.CharField(max_length=200, verbose_name="文件名稱")
    doc_type = models.CharField(
        max_length=20,
        choices=DOC_TYPE_CHOICES,
        verbose_name="文件類型"
    )
    django_model_code = models.TextField(
        blank=True,
        verbose_name="Django Model 程式碼",
        help_text="貼上 Django Model 程式碼，系統將自動解析"
    )
    mermaid_content = models.TextField(
        blank=True,
        verbose_name="Mermaid 內容",
        help_text="自動生成的 Mermaid ER Diagram 內容"
    )
    description = models.TextField(blank=True, verbose_name="說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "資料庫設計文件"
        verbose_name_plural = "資料庫設計文件"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.program.name} - {self.name}"

    def generate_mermaid(self):
        """生成 Mermaid ER Diagram"""
        lines = ["erDiagram"]
        tables = self.tables.prefetch_related('fields').all()
        
        for table in tables:
            # 添加表格及其欄位
            lines.append(f"    {table.table_name} {{")
            for field in table.fields.all():
                pk_marker = "PK" if field.is_primary_key else ""
                fk_marker = "FK" if field.is_foreign_key else ""
                marker = f" {pk_marker}{fk_marker}".rstrip()
                lines.append(f"        {field.data_type} {field.field_name}{marker}")
            lines.append("    }")
        
        # 添加關聯
        for table in tables:
            for field in table.fields.filter(is_foreign_key=True):
                if field.fk_reference_table:
                    lines.append(f"    {field.fk_reference_table} ||--o{{ {table.table_name} : has")
        
        return "\n".join(lines)

    def parse_django_model(self):
        """解析 Django Model 程式碼並建立資料表結構"""
        import re
        
        if not self.django_model_code:
            return False
        
        code = self.django_model_code
        
        # 找出所有 class 定義
        class_pattern = r'class\s+(\w+)\s*\([^)]*models\.Model[^)]*\):'
        classes = re.findall(class_pattern, code)
        
        # Django field 類型對應
        django_type_map = {
            'CharField': 'VARCHAR',
            'TextField': 'TEXT',
            'IntegerField': 'INTEGER',
            'BigIntegerField': 'BIGINT',
            'SmallIntegerField': 'SMALLINT',
            'PositiveIntegerField': 'INTEGER',
            'FloatField': 'FLOAT',
            'DecimalField': 'DECIMAL',
            'BooleanField': 'BOOLEAN',
            'DateField': 'DATE',
            'DateTimeField': 'DATETIME',
            'TimeField': 'TIME',
            'EmailField': 'VARCHAR',
            'URLField': 'VARCHAR',
            'UUIDField': 'UUID',
            'FileField': 'VARCHAR',
            'ImageField': 'VARCHAR',
            'ForeignKey': 'FK',
            'OneToOneField': 'FK',
            'ManyToManyField': 'M2M',
            'AutoField': 'INTEGER',
            'BigAutoField': 'BIGINT',
        }
        
        for class_name in classes:
            # 建立資料表
            table, created = DesignTable.objects.get_or_create(
                design_doc=self,
                table_name=class_name,
                defaults={'description': f'從 Django Model 解析'}
            )
            
            # 找出該 class 的欄位定義
            class_block_pattern = rf'class\s+{class_name}\s*\([^)]*\):(.*?)(?=class\s+\w+|$)'
            class_match = re.search(class_block_pattern, code, re.DOTALL)
            
            if class_match:
                class_body = class_match.group(1)
                
                # 找出欄位定義
                field_pattern = r'(\w+)\s*=\s*models\.(\w+)\s*\('
                fields = re.findall(field_pattern, class_body)
                
                order = 0
                for field_name, field_type in fields:
                    if field_name in ['Meta', 'objects']:
                        continue
                    
                    data_type = django_type_map.get(field_type, field_type.upper())
                    is_fk = field_type in ['ForeignKey', 'OneToOneField']
                    is_pk = field_name == 'id' or 'AutoField' in field_type
                    
                    # 找出 FK 的參考表
                    fk_ref = ''
                    if is_fk:
                        fk_pattern = rf'{field_name}\s*=\s*models\.{field_type}\s*\(\s*[\'"]?(\w+)[\'"]?'
                        fk_match = re.search(fk_pattern, class_body)
                        if fk_match:
                            fk_ref = fk_match.group(1)
                    
                    DesignField.objects.update_or_create(
                        table=table,
                        field_name=field_name,
                        defaults={
                            'data_type': data_type,
                            'is_primary_key': is_pk,
                            'is_foreign_key': is_fk,
                            'fk_reference_table': fk_ref or '',
                            'order': order
                        }
                    )
                    order += 1
        
        # 更新 Mermaid 內容
        self.mermaid_content = self.generate_mermaid()
        self.save(update_fields=['mermaid_content'])
        
        return True


class DesignTable(models.Model):
    """設計文件中的資料表"""
    design_doc = models.ForeignKey(
        DatabaseDesignDoc,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name="設計文件"
    )
    table_name = models.CharField(max_length=200, verbose_name="資料表名稱")
    description = models.TextField(blank=True, verbose_name="說明")
    order = models.IntegerField(default=0, verbose_name="排序")

    class Meta:
        verbose_name = "設計資料表"
        verbose_name_plural = "設計資料表"
        ordering = ['order', 'table_name']
        unique_together = ['design_doc', 'table_name']

    def __str__(self):
        return f"{self.design_doc.name} - {self.table_name}"


class DesignField(models.Model):
    """設計文件中的欄位"""
    DATA_TYPE_CHOICES = [
        ('INTEGER', 'INTEGER'),
        ('BIGINT', 'BIGINT'),
        ('SMALLINT', 'SMALLINT'),
        ('VARCHAR', 'VARCHAR'),
        ('TEXT', 'TEXT'),
        ('BOOLEAN', 'BOOLEAN'),
        ('DATE', 'DATE'),
        ('DATETIME', 'DATETIME'),
        ('TIME', 'TIME'),
        ('FLOAT', 'FLOAT'),
        ('DECIMAL', 'DECIMAL'),
        ('UUID', 'UUID'),
        ('BLOB', 'BLOB'),
        ('JSON', 'JSON'),
        ('FK', 'FOREIGN KEY'),
        ('M2M', 'MANY TO MANY'),
    ]

    table = models.ForeignKey(
        DesignTable,
        on_delete=models.CASCADE,
        related_name='fields',
        verbose_name="資料表"
    )
    field_name = models.CharField(max_length=200, verbose_name="欄位名稱")
    data_type = models.CharField(
        max_length=50,
        choices=DATA_TYPE_CHOICES,
        verbose_name="資料類型"
    )
    description = models.TextField(blank=True, verbose_name="說明")
    is_primary_key = models.BooleanField(default=False, verbose_name="是否為主鍵")
    is_foreign_key = models.BooleanField(default=False, verbose_name="是否為外鍵")
    fk_reference_table = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="外鍵參考表",
        help_text="如果是外鍵，填入參考的資料表名稱"
    )
    is_nullable = models.BooleanField(default=True, verbose_name="可否為空")
    default_value = models.CharField(max_length=200, blank=True, verbose_name="預設值")
    order = models.IntegerField(default=0, verbose_name="排序")

    class Meta:
        verbose_name = "設計欄位"
        verbose_name_plural = "設計欄位"
        ordering = ['order', 'field_name']

    def __str__(self):
        return f"{self.table.table_name}.{self.field_name}"


class PlatformApi(models.Model):
    """平台 API 模型 - 類似資料庫伺服器，作為可介接的資料來源"""
    AUTH_TYPE_CHOICES = [
        ('none', '無需驗證'),
        ('api_key', 'API Key'),
        ('oauth', 'OAuth'),
        ('token', 'Token'),
        ('basic', 'Basic Auth'),
    ]

    name = models.CharField(max_length=200, verbose_name="平台名稱")
    api_endpoint = models.URLField(verbose_name="API 端點", blank=True)
    description = models.TextField(blank=True, verbose_name="說明")
    auth_type = models.CharField(
        max_length=20,
        choices=AUTH_TYPE_CHOICES,
        default='none',
        verbose_name="驗證方式"
    )
    documentation_url = models.URLField(blank=True, verbose_name="文件連結")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "平台 API"
        verbose_name_plural = "平台 API"
        ordering = ['name']

    def __str__(self):
        return self.name


class ProgramApiUsage(models.Model):
    """程式使用平台 API 模型 - 類似 ProgramDatabase"""
    ACCESS_TYPE_CHOICES = [
        ('consume', '呼叫使用'),
        ('provide', '提供服務'),
    ]

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='api_usages',
        verbose_name="程式"
    )
    platform_api = models.ForeignKey(
        PlatformApi,
        on_delete=models.PROTECT,
        related_name='usages',
        verbose_name="平台 API"
    )
    api_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="API 路徑",
        help_text="例如：/api/v1/users"
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default='consume',
        verbose_name="存取類型"
    )
    description = models.CharField(max_length=500, blank=True, verbose_name="說明")

    class Meta:
        verbose_name = "使用平台 API"
        verbose_name_plural = "使用平台 API"
        ordering = ['platform_api__name', 'api_path']

    def __str__(self):
        return f"{self.platform_api.name} - {self.api_path or '(全部)'}"


class VirtualEmployee(models.Model):
    """虛擬員工模型 - 排程機器人"""
    CATEGORY_CHOICES = [
        ('data_sync', '資料同步'),
        ('report', '報表產生'),
        ('notification', '通知發送'),
        ('backup', '備份作業'),
        ('cleanup', '清理作業'),
        ('monitoring', '監控檢查'),
        ('other', '其他'),
    ]

    FREQUENCY_CHOICES = [
        ('hourly', '每小時'),
        ('daily', '每日'),
        ('weekly', '每週'),
        ('monthly', '每月'),
        ('custom', '自訂'),
    ]

    STATUS_CHOICES = [
        ('active', '運作中'),
        ('retired', '已退休'),
    ]

    team = models.ForeignKey(
        DevTeam,
        on_delete=models.CASCADE,
        related_name='virtual_employees',
        verbose_name="所屬團隊"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="分類"
    )
    code = models.CharField(max_length=50, verbose_name="編號")
    name = models.CharField(max_length=200, verbose_name="名稱")
    device = models.CharField(max_length=200, verbose_name="排程設備")
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name="頻率"
    )
    frequency_note = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="頻率備註",
        help_text="例如：每天晚上3點"
    )
    purpose = models.TextField(verbose_name="作用")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="狀態"
    )
    retirement_reason = models.TextField(
        blank=True,
        verbose_name="退休原因"
    )
    retired_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="退休時間"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_virtual_employees',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "虛擬員工"
        verbose_name_plural = "虛擬員工"
        ordering = ['status', 'category', 'code']
        unique_together = ['team', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"
