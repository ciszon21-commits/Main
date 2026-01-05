from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, Mock

from ERModelGenerator.views import er_diagram_view, admin_required

class ViewPermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='normal_user', password='password')
        self.admin = User.objects.create_superuser(username='admin_user', password='password')

    def test_admin_required_decorator(self):
        """測試管理員權限裝飾器"""
        # 未登入
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        @admin_required
        def test_view(req):
            return "OK"
            
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # 導向登入

        # 普通用戶
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 403)  # 禁止訪問

        # 管理員
        request.user = self.admin
        response = test_view(request)
        self.assertEqual(response, "OK")


class ERModelViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='password')
        self.client.force_login(self.admin)
        
        self.url_index = reverse('er_model:diagram')
        self.url_api_mermaid = reverse('er_model:api_mermaid')
        self.url_api_apps = reverse('er_model:api_apps')
        self.url_download = reverse('er_model:download')

    @patch('ERModelGenerator.views.get_project_app_labels')
    @patch('ERModelGenerator.views.generate_mermaid_er')
    @patch('ERModelGenerator.views.get_app_model_stats')
    def test_er_diagram_view(self, mock_stats, mock_gen, mock_apps):
        """測試主頁面視圖"""
        mock_apps.return_value = ['app1', 'app2']
        mock_stats.return_value = {'app1': 5, 'app2': 3}
        mock_gen.return_value = "erDiagram\n    app1Model"

        # 默認 GET
        response = self.client.get(self.url_index)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ERModelGenerator/er_diagram.html')
        self.assertEqual(response.context['all_apps'], ['app1', 'app2'])
        self.assertEqual(response.context['current_app'], 'app1') # 預設選第一個

        # 測試參數：single mode with specific app
        response = self.client.get(self.url_index, {'view_mode': 'single', 'current_app': 'app2'})
        self.assertEqual(response.context['current_app'], 'app2')
        self.assertEqual(response.context['displayed_apps'], ['app2'])

        # 測試參數：multi mode
        response = self.client.get(self.url_index, {'view_mode': 'multi', 'apps': 'app1,app2'})
        self.assertEqual(response.context['displayed_apps'], ['app1', 'app2'])
        
        # 測試參數：relations mode
        response = self.client.get(self.url_index, {'view_mode': 'relations'})
        self.assertEqual(response.context['view_mode'], 'relations')

    @patch('ERModelGenerator.views.generate_mermaid_er')
    @patch('ERModelGenerator.views.get_project_app_labels')
    def test_api_mermaid_code(self, mock_apps, mock_gen):
        """測試 Mermaid API"""
        mock_apps.return_value = ['app1']
        mock_gen.return_value = "graph TD;"
        
        response = self.client.get(self.url_api_mermaid, {'apps': 'app1'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['mermaid_code'], "graph TD;")

    @patch('ERModelGenerator.views.get_project_app_labels')
    @patch('ERModelGenerator.views.get_app_model_stats')
    def test_api_app_list(self, mock_stats, mock_apps):
        """測試 App 列表 API"""
        mock_apps.return_value = ['app1']
        mock_stats.return_value = {'app1': 10}
        
        response = self.client.get(self.url_api_apps)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['apps']), 1)
        self.assertEqual(data['apps'][0]['label'], 'app1')
        self.assertEqual(data['apps'][0]['model_count'], 10)

    @patch('ERModelGenerator.views.get_models_for_app')
    def test_api_app_models(self, mock_get_models):
        """測試 App Models API"""
        # Mock ModelInfo
        mock_model = Mock()
        mock_model.name = 'TestModel'
        mock_model.verbose_name = 'Test Verbose'
        mock_model.db_table = 'test_table'
        
        # Mock Field
        mock_field = Mock()
        mock_field.name = 'id'
        mock_field.field_type = 'int'
        mock_field.is_pk = True
        mock_field.is_fk = False
        mock_field.verbose_name = 'ID'
        mock_model.fields = [mock_field]
        mock_model.relations = []
        
        mock_get_models.return_value = [mock_model]
        
        url = reverse('er_model:api_app_models', args=['test_app'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['models'][0]['name'], 'TestModel')
        self.assertEqual(data['models'][0]['fields'][0]['name'], 'id')

        # 測試無此 App
        mock_get_models.return_value = []
        response = self.client.get(url)
        self.assertFalse(response.json()['success'])

    @patch('ERModelGenerator.views.generate_mermaid_er')
    @patch('ERModelGenerator.views.get_project_app_labels')
    def test_download_mermaid(self, mock_apps, mock_gen):
        """測試下載功能"""
        mock_apps.return_value = ['app1']
        mock_gen.return_value = "content"
        
        response = self.client.get(self.url_download, {'apps': 'app1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn('attachment; filename="er_diagram_app1.mmd"', response['Content-Disposition'])
        self.assertEqual(response.content.decode(), "content")
