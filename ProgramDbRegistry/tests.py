"""
ProgramDbRegistry 單元測試
測試涵蓋 Models、Forms 和 Views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import IntegrityError
import json

from .models import (
    DevTeam, DevTeamMember, DatabaseServer, Program, ProgramDatabase,
    FileLocation, DatabaseDesignDoc, DesignTable, DesignField,
    PlatformApi, ProgramApiUsage, VirtualEmployee
)
from .forms import (
    DevTeamForm, DatabaseServerForm, ProgramForm, DatabaseDesignDocForm,
    DesignTableForm, DesignFieldForm, PlatformApiForm, VirtualEmployeeForm,
    VirtualEmployeeRetireForm
)


# ===== Model Tests =====

class DevTeamModelTestCase(TestCase):
    """開發團隊模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            description='這是測試團隊的說明',
            created_by=self.user
        )
    
    def test_team_creation(self):
        """測試團隊建立"""
        self.assertEqual(self.team.name, '測試團隊')
        self.assertEqual(self.team.description, '這是測試團隊的說明')
        self.assertEqual(self.team.created_by, self.user)
    
    def test_team_str_representation(self):
        """測試團隊字串表示"""
        self.assertEqual(str(self.team), '測試團隊')
    
    def test_is_creator(self):
        """測試 is_creator 方法"""
        self.assertTrue(self.team.is_creator(self.user))
        self.assertFalse(self.team.is_creator(self.other_user))
    
    def test_is_member_with_membership(self):
        """測試 is_member 方法 - 有成員資格"""
        DevTeamMember.objects.create(
            team=self.team,
            user=self.other_user,
            role='member'
        )
        self.assertTrue(self.team.is_member(self.other_user))
    
    def test_is_member_without_membership(self):
        """測試 is_member 方法 - 無成員資格"""
        self.assertFalse(self.team.is_member(self.other_user))


class DevTeamMemberModelTestCase(TestCase):
    """團隊成員模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.member = DevTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
    
    def test_member_creation(self):
        """測試成員建立"""
        self.assertEqual(self.member.team, self.team)
        self.assertEqual(self.member.user, self.user)
        self.assertEqual(self.member.role, 'creator')
    
    def test_member_str_representation(self):
        """測試成員字串表示"""
        expected = f'{self.team.name} - Test User'
        self.assertEqual(str(self.member), expected)
    
    def test_member_str_without_full_name(self):
        """測試成員字串表示 - 無全名"""
        user_no_name = User.objects.create_user(
            username='noname',
            password='testpass123'
        )
        member = DevTeamMember.objects.create(
            team=self.team,
            user=user_no_name,
            role='member'
        )
        expected = f'{self.team.name} - noname'
        self.assertEqual(str(member), expected)
    
    def test_unique_together_constraint(self):
        """測試 unique_together 約束"""
        with self.assertRaises(IntegrityError):
            DevTeamMember.objects.create(
                team=self.team,
                user=self.user,
                role='member'
            )


class DatabaseServerModelTestCase(TestCase):
    """資料庫伺服器模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.server = DatabaseServer.objects.create(
            name='SQL-PROD-01',
            description='生產環境資料庫伺服器'
        )
    
    def test_server_creation(self):
        """測試伺服器建立"""
        self.assertEqual(self.server.name, 'SQL-PROD-01')
        self.assertEqual(self.server.description, '生產環境資料庫伺服器')
    
    def test_server_str_representation(self):
        """測試伺服器字串表示"""
        self.assertEqual(str(self.server), 'SQL-PROD-01')
    
    def test_unique_name_constraint(self):
        """測試名稱唯一約束"""
        with self.assertRaises(IntegrityError):
            DatabaseServer.objects.create(
                name='SQL-PROD-01',
                description='重複的伺服器'
            )


class ProgramModelTestCase(TestCase):
    """程式模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            english_name='Test Program',
            dev_tool='Visual Studio 2022',
            git_url='https://github.com/test/repo'
        )
    
    def test_program_creation(self):
        """測試程式建立"""
        self.assertEqual(self.program.name, '測試程式')
        self.assertEqual(self.program.team, self.team)
        self.assertEqual(self.program.program_type, 'web')
    
    def test_program_str_representation(self):
        """測試程式字串表示"""
        self.assertEqual(str(self.program), '測試程式')
    
    def test_program_types(self):
        """測試不同程式類型"""
        desktop = Program.objects.create(
            team=self.team,
            name='桌面程式',
            program_type='desktop',
            dev_tool='C#',
            git_url='https://github.com/test/desktop'
        )
        plugin = Program.objects.create(
            team=self.team,
            name='外掛程式',
            program_type='plugin',
            dev_tool='Python',
            git_url='https://github.com/test/plugin'
        )
        self.assertEqual(desktop.program_type, 'desktop')
        self.assertEqual(plugin.program_type, 'plugin')


class ProgramDatabaseModelTestCase(TestCase):
    """程式使用資料庫模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test/repo'
        )
        self.server = DatabaseServer.objects.create(name='SQL-01')
        self.db = ProgramDatabase.objects.create(
            program=self.program,
            server=self.server,
            database_name='TestDB',
            table_name='Users',
            access_permission='readonly'
        )
    
    def test_database_creation(self):
        """測試資料庫建立"""
        self.assertEqual(self.db.database_name, 'TestDB')
        self.assertEqual(self.db.table_name, 'Users')
        self.assertEqual(self.db.access_permission, 'readonly')
    
    def test_database_str_representation(self):
        """測試資料庫字串表示"""
        expected = 'SQL-01/TestDB.Users'
        self.assertEqual(str(self.db), expected)


class FileLocationModelTestCase(TestCase):
    """存取檔案位置模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test/repo'
        )
        self.file_location = FileLocation.objects.create(
            program=self.program,
            path='\\\\server\\share\\data',
            description='資料檔案位置'
        )
    
    def test_file_location_creation(self):
        """測試檔案位置建立"""
        self.assertEqual(self.file_location.path, '\\\\server\\share\\data')
        self.assertEqual(self.file_location.description, '資料檔案位置')
    
    def test_file_location_str_representation(self):
        """測試檔案位置字串表示"""
        self.assertEqual(str(self.file_location), '\\\\server\\share\\data')


class DatabaseDesignDocModelTestCase(TestCase):
    """資料庫設計文件模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test/repo'
        )
        self.doc = DatabaseDesignDoc.objects.create(
            program=self.program,
            name='資料庫設計',
            doc_type='manual',
            description='測試設計文件'
        )
    
    def test_design_doc_creation(self):
        """測試設計文件建立"""
        self.assertEqual(self.doc.name, '資料庫設計')
        self.assertEqual(self.doc.doc_type, 'manual')
    
    def test_design_doc_str_representation(self):
        """測試設計文件字串表示"""
        expected = '測試程式 - 資料庫設計'
        self.assertEqual(str(self.doc), expected)
    
    def test_generate_mermaid_empty(self):
        """測試生成空 Mermaid"""
        mermaid = self.doc.generate_mermaid()
        self.assertIn('erDiagram', mermaid)
    
    def test_generate_mermaid_with_tables(self):
        """測試生成有資料表的 Mermaid"""
        table = DesignTable.objects.create(
            design_doc=self.doc,
            table_name='Users'
        )
        DesignField.objects.create(
            table=table,
            field_name='id',
            data_type='INTEGER',
            is_primary_key=True
        )
        DesignField.objects.create(
            table=table,
            field_name='name',
            data_type='VARCHAR'
        )
        
        mermaid = self.doc.generate_mermaid()
        self.assertIn('Users', mermaid)
        self.assertIn('id', mermaid)
        self.assertIn('INTEGER', mermaid)
    
    def test_parse_django_model(self):
        """測試解析 Django Model"""
        django_doc = DatabaseDesignDoc.objects.create(
            program=self.program,
            name='Django 模型',
            doc_type='django',
            django_model_code='''
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
'''
        )
        result = django_doc.parse_django_model()
        self.assertTrue(result)
        self.assertTrue(DesignTable.objects.filter(design_doc=django_doc, table_name='User').exists())


class DesignTableModelTestCase(TestCase):
    """設計資料表模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test/repo'
        )
        self.doc = DatabaseDesignDoc.objects.create(
            program=self.program,
            name='設計文件',
            doc_type='manual'
        )
        self.table = DesignTable.objects.create(
            design_doc=self.doc,
            table_name='Users',
            description='使用者資料表'
        )
    
    def test_table_creation(self):
        """測試資料表建立"""
        self.assertEqual(self.table.table_name, 'Users')
        self.assertEqual(self.table.description, '使用者資料表')
    
    def test_table_str_representation(self):
        """測試資料表字串表示"""
        expected = '設計文件 - Users'
        self.assertEqual(str(self.table), expected)
    
    def test_unique_together_constraint(self):
        """測試 unique_together 約束"""
        with self.assertRaises(IntegrityError):
            DesignTable.objects.create(
                design_doc=self.doc,
                table_name='Users'
            )


class DesignFieldModelTestCase(TestCase):
    """設計欄位模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test/repo'
        )
        self.doc = DatabaseDesignDoc.objects.create(
            program=self.program,
            name='設計文件',
            doc_type='manual'
        )
        self.table = DesignTable.objects.create(
            design_doc=self.doc,
            table_name='Users'
        )
        self.field = DesignField.objects.create(
            table=self.table,
            field_name='id',
            data_type='INTEGER',
            is_primary_key=True
        )
    
    def test_field_creation(self):
        """測試欄位建立"""
        self.assertEqual(self.field.field_name, 'id')
        self.assertEqual(self.field.data_type, 'INTEGER')
        self.assertTrue(self.field.is_primary_key)
    
    def test_field_str_representation(self):
        """測試欄位字串表示"""
        expected = 'Users.id'
        self.assertEqual(str(self.field), expected)
    
    def test_foreign_key_field(self):
        """測試外鍵欄位"""
        fk_field = DesignField.objects.create(
            table=self.table,
            field_name='role_id',
            data_type='FK',
            is_foreign_key=True,
            fk_reference_table='Roles'
        )
        self.assertTrue(fk_field.is_foreign_key)
        self.assertEqual(fk_field.fk_reference_table, 'Roles')


class PlatformApiModelTestCase(TestCase):
    """平台 API 模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.api = PlatformApi.objects.create(
            name='PMIS API',
            api_endpoint='https://api.pmis.com',
            description='專案管理系統 API',
            auth_type='token'
        )
    
    def test_api_creation(self):
        """測試 API 建立"""
        self.assertEqual(self.api.name, 'PMIS API')
        self.assertEqual(self.api.auth_type, 'token')
    
    def test_api_str_representation(self):
        """測試 API 字串表示"""
        self.assertEqual(str(self.api), 'PMIS API')
    
    def test_auth_types(self):
        """測試不同驗證方式"""
        api_key = PlatformApi.objects.create(
            name='API Key Test',
            auth_type='api_key'
        )
        oauth = PlatformApi.objects.create(
            name='OAuth Test',
            auth_type='oauth'
        )
        self.assertEqual(api_key.auth_type, 'api_key')
        self.assertEqual(oauth.auth_type, 'oauth')


class ProgramApiUsageModelTestCase(TestCase):
    """程式使用平台 API 模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test/repo'
        )
        self.api = PlatformApi.objects.create(
            name='PMIS API',
            auth_type='token'
        )
        self.usage = ProgramApiUsage.objects.create(
            program=self.program,
            platform_api=self.api,
            api_path='/api/v1/projects',
            access_type='consume'
        )
    
    def test_usage_creation(self):
        """測試使用紀錄建立"""
        self.assertEqual(self.usage.api_path, '/api/v1/projects')
        self.assertEqual(self.usage.access_type, 'consume')
    
    def test_usage_str_representation(self):
        """測試使用紀錄字串表示"""
        expected = 'PMIS API - /api/v1/projects'
        self.assertEqual(str(self.usage), expected)


class VirtualEmployeeModelTestCase(TestCase):
    """虛擬員工模型測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        self.ve = VirtualEmployee.objects.create(
            team=self.team,
            category='data_sync',
            code='VE-001',
            name='資料同步機器人',
            device='SCHEDULER-01',
            frequency='daily',
            purpose='每日同步資料',
            created_by=self.user
        )
    
    def test_virtual_employee_creation(self):
        """測試虛擬員工建立"""
        self.assertEqual(self.ve.code, 'VE-001')
        self.assertEqual(self.ve.name, '資料同步機器人')
        self.assertEqual(self.ve.category, 'data_sync')
        self.assertEqual(self.ve.status, 'active')
    
    def test_virtual_employee_str_representation(self):
        """測試虛擬員工字串表示"""
        expected = 'VE-001 - 資料同步機器人'
        self.assertEqual(str(self.ve), expected)
    
    def test_unique_together_constraint(self):
        """測試 unique_together 約束"""
        with self.assertRaises(IntegrityError):
            VirtualEmployee.objects.create(
                team=self.team,
                category='report',
                code='VE-001',  # 重複的編號
                name='另一個機器人',
                device='SCHEDULER-02',
                frequency='weekly',
                purpose='測試',
                created_by=self.user
            )


# ===== Form Tests =====

class DevTeamFormTestCase(TestCase):
    """開發團隊表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'name': '新團隊',
            'description': '團隊說明'
        }
        form = DevTeamForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_valid_form_without_description(self):
        """測試有效表單 - 無說明"""
        data = {
            'name': '新團隊',
            'description': ''
        }
        form = DevTeamForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_name(self):
        """測試無效表單 - 無名稱"""
        data = {
            'name': '',
            'description': '說明'
        }
        form = DevTeamForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class DatabaseServerFormTestCase(TestCase):
    """資料庫伺服器表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'name': 'SQL-PROD-01',
            'description': '生產環境'
        }
        form = DatabaseServerForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_name(self):
        """測試無效表單 - 無名稱"""
        data = {
            'name': '',
            'description': '說明'
        }
        form = DatabaseServerForm(data=data)
        self.assertFalse(form.is_valid())


class ProgramFormTestCase(TestCase):
    """程式表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'name': '新程式',
            'program_type': 'web',
            'dev_tool': 'Visual Studio',
            'git_url': 'https://github.com/test/repo',
            'english_name': '',
            'url': '',
            'developers': '',
            'maintainers': ''
        }
        form = ProgramForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_name(self):
        """測試無效表單 - 無名稱"""
        data = {
            'name': '',
            'program_type': 'web',
            'dev_tool': 'VS',
            'git_url': 'https://github.com/test'
        }
        form = ProgramForm(data=data)
        self.assertFalse(form.is_valid())
    
    def test_invalid_form_without_git_url(self):
        """測試無效表單 - 無 Git URL"""
        data = {
            'name': '程式',
            'program_type': 'web',
            'dev_tool': 'VS',
            'git_url': ''
        }
        form = ProgramForm(data=data)
        self.assertFalse(form.is_valid())


class DatabaseDesignDocFormTestCase(TestCase):
    """資料庫設計文件表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'name': '設計文件',
            'doc_type': 'manual',
            'description': '',
            'django_model_code': '',
            'mermaid_content': ''
        }
        form = DatabaseDesignDocForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_name(self):
        """測試無效表單 - 無名稱"""
        data = {
            'name': '',
            'doc_type': 'manual'
        }
        form = DatabaseDesignDocForm(data=data)
        self.assertFalse(form.is_valid())


class DesignTableFormTestCase(TestCase):
    """設計資料表表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'table_name': 'Users',
            'description': '使用者資料表',
            'order': 0
        }
        form = DesignTableForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_table_name(self):
        """測試無效表單 - 無表名"""
        data = {
            'table_name': '',
            'description': '',
            'order': 0
        }
        form = DesignTableForm(data=data)
        self.assertFalse(form.is_valid())


class DesignFieldFormTestCase(TestCase):
    """設計欄位表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'field_name': 'id',
            'data_type': 'INTEGER',
            'description': '',
            'is_primary_key': True,
            'is_foreign_key': False,
            'fk_reference_table': '',
            'is_nullable': False,
            'default_value': '',
            'order': 0
        }
        form = DesignFieldForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_field_name(self):
        """測試無效表單 - 無欄位名稱"""
        data = {
            'field_name': '',
            'data_type': 'VARCHAR',
            'order': 0
        }
        form = DesignFieldForm(data=data)
        self.assertFalse(form.is_valid())


class PlatformApiFormTestCase(TestCase):
    """平台 API 表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'name': 'PMIS API',
            'api_endpoint': 'https://api.pmis.com',
            'description': 'API 說明',
            'auth_type': 'token',
            'documentation_url': ''
        }
        form = PlatformApiForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_name(self):
        """測試無效表單 - 無名稱"""
        data = {
            'name': '',
            'auth_type': 'none'
        }
        form = PlatformApiForm(data=data)
        self.assertFalse(form.is_valid())


class VirtualEmployeeFormTestCase(TestCase):
    """虛擬員工表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'category': 'data_sync',
            'code': 'VE-001',
            'name': '測試機器人',
            'device': 'SCHEDULER-01',
            'frequency': 'daily',
            'frequency_note': '每天早上8點',
            'purpose': '同步資料'
        }
        form = VirtualEmployeeForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_required_fields(self):
        """測試無效表單 - 缺少必填欄位"""
        data = {
            'category': 'data_sync',
            'code': '',  # 必填
            'name': '',  # 必填
            'device': '',
            'frequency': 'daily',
            'purpose': ''
        }
        form = VirtualEmployeeForm(data=data)
        self.assertFalse(form.is_valid())


class VirtualEmployeeRetireFormTestCase(TestCase):
    """虛擬員工退休表單測試"""
    
    def test_valid_form(self):
        """測試有效表單"""
        data = {
            'retirement_reason': '功能已被新系統取代'
        }
        form = VirtualEmployeeRetireForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form_without_reason(self):
        """測試無效表單 - 無退休原因"""
        data = {
            'retirement_reason': ''
        }
        form = VirtualEmployeeRetireForm(data=data)
        self.assertFalse(form.is_valid())


# ===== View Tests =====

class TeamViewTestCase(TestCase):
    """團隊視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        # 建立者加入成員
        DevTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
    
    def test_team_list_requires_login(self):
        """測試團隊列表需要登入"""
        response = self.client.get(reverse('programdb:team_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_team_list_authenticated(self):
        """測試團隊列表 - 已登入"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('programdb:team_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試團隊')
    
    def test_team_detail_requires_login(self):
        """測試團隊詳情需要登入"""
        response = self.client.get(
            reverse('programdb:team_detail', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_team_detail_member_access(self):
        """測試團隊詳情 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:team_detail', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試團隊')
    
    def test_team_detail_non_member_denied(self):
        """測試團隊詳情 - 非成員存取受限"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:team_detail', kwargs={'pk': self.team.pk})
        )
        # 非成員會看到 access denied 頁面
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '無權限')
    
    def test_team_list_visibility_restriction(self):
        """測試團隊列表 - 只能看到自己相關的團隊"""
        # 建立另一個使用者的團隊
        other_team = DevTeam.objects.create(
            name='其他團隊',
            created_by=self.other_user
        )
        # 登入為 testuser (只屬於 self.team)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('programdb:team_list'))
        self.assertEqual(response.status_code, 200)
        
        # 應該看到自己的團隊
        self.assertContains(response, '測試團隊')
        # 不應該看到別人的團隊
        self.assertNotContains(response, '其他團隊')

    
    def test_team_create_get(self):
        """測試建立團隊頁面 - GET"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('programdb:team_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_team_create_post_valid(self):
        """測試建立團隊 - POST 有效資料"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('programdb:team_create'), {
            'name': '新建團隊',
            'description': '新團隊說明'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DevTeam.objects.filter(name='新建團隊').exists())
    
    def test_team_update_creator_only(self):
        """測試編輯團隊 - 非建立者被拒絕"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:team_update', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_team_update_by_creator(self):
        """測試編輯團隊 - 建立者存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:team_update', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_team_members_creator_only(self):
        """測試管理成員 - 非建立者被拒絕"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:team_members', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 403)


class MemberManagementViewTestCase(TestCase):
    """成員管理視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.creator = User.objects.create_user(
            username='creator',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member',
            password='testpass123'
        )
        self.new_user = User.objects.create_user(
            username='newuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.creator
        )
        DevTeamMember.objects.create(
            team=self.team,
            user=self.creator,
            role='creator'
        )
    
    def test_search_users_requires_login(self):
        """測試搜尋使用者需要登入"""
        response = self.client.get(
            reverse('programdb:search_users') + '?q=test'
        )
        self.assertEqual(response.status_code, 302)
    
    def test_search_users_short_query(self):
        """測試搜尋使用者 - 查詢太短"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('programdb:search_users') + '?q=t'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['users'], [])
    
    def test_search_users_valid_query(self):
        """測試搜尋使用者 - 有效查詢"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('programdb:search_users') + '?q=new'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['users']) >= 1)
    
    def test_add_member_requires_post(self):
        """測試新增成員需要 POST"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.get(
            reverse('programdb:add_member', kwargs={'pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 405)
    
    def test_add_member_creator_only(self):
        """測試新增成員 - 非建立者被拒絕"""
        self.client.login(username='member', password='testpass123')
        response = self.client.post(
            reverse('programdb:add_member', kwargs={'pk': self.team.pk}),
            data=json.dumps({'user_id': self.new_user.pk}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
    
    def test_add_member_success(self):
        """測試新增成員 - 成功"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('programdb:add_member', kwargs={'pk': self.team.pk}),
            data=json.dumps({'user_id': self.new_user.pk}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(
            DevTeamMember.objects.filter(
                team=self.team, user=self.new_user
            ).exists()
        )
    
    def test_add_member_duplicate(self):
        """測試新增成員 - 重複"""
        DevTeamMember.objects.create(
            team=self.team,
            user=self.new_user,
            role='member'
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('programdb:add_member', kwargs={'pk': self.team.pk}),
            data=json.dumps({'user_id': self.new_user.pk}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_remove_member_success(self):
        """測試移除成員 - 成功"""
        DevTeamMember.objects.create(
            team=self.team,
            user=self.new_user,
            role='member'
        )
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('programdb:remove_member', kwargs={
                'pk': self.team.pk,
                'user_id': self.new_user.pk
            })
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_remove_creator_denied(self):
        """測試移除建立者 - 被拒絕"""
        self.client.login(username='creator', password='testpass123')
        response = self.client.post(
            reverse('programdb:remove_member', kwargs={
                'pk': self.team.pk,
                'user_id': self.creator.pk
            })
        )
        self.assertEqual(response.status_code, 400)


class ProgramViewTestCase(TestCase):
    """程式視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        DevTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test/repo'
        )
    
    def test_program_detail_requires_login(self):
        """測試程式詳情需要登入"""
        response = self.client.get(
            reverse('programdb:program_detail', kwargs={'pk': self.program.pk})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_program_detail_member_access(self):
        """測試程式詳情 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:program_detail', kwargs={'pk': self.program.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試程式')
    
    def test_program_detail_non_member_denied(self):
        """測試程式詳情 - 非成員存取受限"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:program_detail', kwargs={'pk': self.program.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '無權限')
    
    def test_program_create_requires_member(self):
        """測試建立程式需要成員身份"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:program_create', kwargs={'team_pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_program_create_member_access(self):
        """測試建立程式 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:program_create', kwargs={'team_pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_program_update_member_access(self):
        """測試編輯程式 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:program_update', kwargs={'pk': self.program.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_program_delete_creator_only(self):
        """測試刪除程式 - 只有建立者"""
        # 新增成員
        DevTeamMember.objects.create(
            team=self.team,
            user=self.other_user,
            role='member'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('programdb:program_delete', kwargs={'pk': self.program.pk})
        )
        self.assertEqual(response.status_code, 403)


class DatabaseServerViewTestCase(TestCase):
    """資料庫伺服器視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        DevTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.server = DatabaseServer.objects.create(
            name='SQL-01',
            description='測試伺服器'
        )
    
    def test_add_db_server_requires_member(self):
        """測試新增伺服器需要成員身份"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('programdb:add_db_server', kwargs={'pk': self.team.pk}),
            {'name': 'NEW-SQL', 'description': ''}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_add_db_server_success(self):
        """測試新增伺服器 - 成功"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('programdb:add_db_server', kwargs={'pk': self.team.pk}),
            {'name': 'SQL-NEW', 'description': '新伺服器'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_delete_db_server_with_usage(self):
        """測試刪除伺服器 - 有程式使用"""
        program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test'
        )
        ProgramDatabase.objects.create(
            program=program,
            server=self.server,
            database_name='TestDB',
            table_name='Users',
            access_permission='readonly'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('programdb:delete_db_server', kwargs={
                'pk': self.team.pk,
                'server_id': self.server.pk
            })
        )
        self.assertEqual(response.status_code, 400)


class DesignDocViewTestCase(TestCase):
    """設計文件視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        DevTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test'
        )
        self.doc = DatabaseDesignDoc.objects.create(
            program=self.program,
            name='設計文件',
            doc_type='manual'
        )
    
    def test_design_doc_create_requires_member(self):
        """測試建立設計文件需要成員身份"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:design_doc_create', kwargs={'program_pk': self.program.pk})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_design_doc_detail_member_access(self):
        """測試設計文件詳情 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:design_doc_detail', kwargs={'pk': self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '設計文件')
    
    def test_design_doc_download(self):
        """測試下載設計文件"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:design_doc_download', kwargs={'pk': self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/markdown; charset=utf-8')


class VirtualEmployeeViewTestCase(TestCase):
    """虛擬員工視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        DevTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.ve = VirtualEmployee.objects.create(
            team=self.team,
            category='data_sync',
            code='VE-001',
            name='測試機器人',
            device='SCHEDULER-01',
            frequency='daily',
            purpose='測試用途',
            created_by=self.user
        )
    
    def test_virtual_employee_list_requires_member(self):
        """測試虛擬員工列表需要成員身份"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:virtual_employee_list', kwargs={'team_pk': self.team.pk})
        )
        # 非成員會看到 access denied 頁面
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '無權限')
    
    def test_virtual_employee_list_member_access(self):
        """測試虛擬員工列表 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:virtual_employee_list', kwargs={'team_pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試機器人')
    
    def test_virtual_employee_create_requires_member(self):
        """測試建立虛擬員工需要成員身份"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('programdb:virtual_employee_create', kwargs={'team_pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 403)
    
    def test_virtual_employee_create_member_access(self):
        """測試建立虛擬員工 - 成員存取"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('programdb:virtual_employee_create', kwargs={'team_pk': self.team.pk})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_virtual_employee_retire(self):
        """測試虛擬員工退休"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('programdb:virtual_employee_retire', kwargs={'pk': self.ve.pk}),
            {'retirement_reason': '功能已被取代'}
        )
        self.assertEqual(response.status_code, 302)
        self.ve.refresh_from_db()
        self.assertEqual(self.ve.status, 'retired')


class PlatformApiViewTestCase(TestCase):
    """平台 API 視圖測試"""
    
    def setUp(self):
        """建立測試資料"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.team = DevTeam.objects.create(
            name='測試團隊',
            created_by=self.user
        )
        DevTeamMember.objects.create(
            team=self.team,
            user=self.user,
            role='creator'
        )
        self.api = PlatformApi.objects.create(
            name='PMIS API',
            auth_type='token'
        )
    
    def test_add_platform_api_requires_member(self):
        """測試新增平台 API 需要成員身份"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('programdb:add_platform_api', kwargs={'pk': self.team.pk}),
            {'name': 'New API', 'auth_type': 'none'}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_add_platform_api_success(self):
        """測試新增平台 API - 成功"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('programdb:add_platform_api', kwargs={'pk': self.team.pk}),
            {
                'name': 'New API',
                'api_endpoint': 'https://api.new.com',
                'description': '',
                'auth_type': 'api_key',
                'documentation_url': ''
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_delete_platform_api_with_usage(self):
        """測試刪除平台 API - 有程式使用"""
        program = Program.objects.create(
            team=self.team,
            name='測試程式',
            program_type='web',
            dev_tool='VS',
            git_url='https://github.com/test'
        )
        ProgramApiUsage.objects.create(
            program=program,
            platform_api=self.api,
            access_type='consume'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('programdb:delete_platform_api', kwargs={
                'pk': self.team.pk,
                'api_id': self.api.pk
            })
        )
        self.assertEqual(response.status_code, 400)
