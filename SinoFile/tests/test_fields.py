from django.test import TestCase, override_settings
from django.db.models.fields.files import FieldFile
from django.core.files.storage import default_storage
from unittest.mock import MagicMock
from SinoFile.fields import SinoFileField, SinoFileFieldFile, ARCHIVE_PROTOCOL

class SinoFileFieldTest(TestCase):

    def setUp(self):
        # 建立一個模擬的 FieldFile 實例
        self.field = SinoFileField()
        self.mock_instance = MagicMock()
        self.mock_field = MagicMock()
        self.mock_field.storage = default_storage
        self.mock_field.storage.url = MagicMock(return_value='/media/uploads/test.txt')
    
    def create_field_file(self, name):
        return SinoFileFieldFile(self.mock_instance, self.mock_field, name)

    @override_settings(ARCHIVE_URL='/custom-archive/')
    def test_url_archived_file(self):
        """測試已封存檔案的 URL 生成"""
        name = f'{ARCHIVE_PROTOCOL}VOL001/abc-123.pdf'
        field_file = self.create_field_file(name)
        
        # 應忽略模擬的 storage.url，直接回傳 archive url
        self.assertEqual(field_file.url, '/custom-archive/VOL001/abc-123.pdf')

    def test_url_normal_file(self):
        """測試一般檔案的 URL 生成"""
        name = 'uploads/test.txt'
        field_file = self.create_field_file(name)
        
        # 應呼叫 storage.url
        url = field_file.url
        self.mock_field.storage.url.assert_called_with(name)
        self.assertEqual(url, '/media/uploads/test.txt')

    def test_is_archived(self):
        """測試 is_archived 屬性"""
        archived_file = self.create_field_file(f'{ARCHIVE_PROTOCOL}VOL/file')
        self.assertTrue(archived_file.is_archived)

        normal_file = self.create_field_file('uploads/file')
        self.assertFalse(normal_file.is_archived)
        
        empty_file = self.create_field_file(None)
        self.assertFalse(empty_file.is_archived)

    def test_get_archive_info(self):
        """測試 get_archive_info 方法"""
        # 正常封存路徑
        name = f'{ARCHIVE_PROTOCOL}VOL_2024/uuid-file.ext'
        field_file = self.create_field_file(name)
        info = field_file.get_archive_info()
        self.assertEqual(info['folder_name'], 'VOL_2024')
        self.assertEqual(info['uuid_filename'], 'uuid-file.ext')

        # 非封存檔案
        normal_file = self.create_field_file('uploads/file.ext')
        self.assertIsNone(normal_file.get_archive_info())
        
        # 格式錯誤的封存路徑 (少一部分)
        broken_name = f'{ARCHIVE_PROTOCOL}VOL_ONLY'
        broken_file = self.create_field_file(broken_name)
        self.assertIsNone(broken_file.get_archive_info())
