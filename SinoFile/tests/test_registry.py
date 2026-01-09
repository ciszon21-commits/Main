from django.test import TestCase
from django.db import models
from SinoFile.registry import register_archivable_field, get_archivable_fields, clear_registry

# Define MockModel at module level to avoid re-registration warning during tests
class MockModel(models.Model):
    class Meta:
        managed = False  # No database table needed for registry tests
        app_label = 'SinoFile'

class RegistryTest(TestCase):
    
    def setUp(self):
        clear_registry()

    def tearDown(self):
        clear_registry()

    def test_register_field(self):
        """測試註冊欄位"""
        register_archivable_field(MockModel, 'file')
        fields = get_archivable_fields()
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0], (MockModel, 'file'))

    def test_avoid_duplicates(self):
        """測試避免重複註冊"""
        register_archivable_field(MockModel, 'file')
        register_archivable_field(MockModel, 'file')  # Duplicate
        
        fields = get_archivable_fields()
        self.assertEqual(len(fields), 1)

    def test_clear_registry(self):
        """測試清空註冊表"""
        register_archivable_field(MockModel, 'file')
        self.assertEqual(len(get_archivable_fields()), 1)
        
        clear_registry()
        self.assertEqual(len(get_archivable_fields()), 0)
