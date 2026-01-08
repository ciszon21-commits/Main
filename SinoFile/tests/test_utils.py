import os
from django.test import TestCase, override_settings
from SinoFile import utils

class UtilsTest(TestCase):

    @override_settings(ARCHIVE_ROOT='/tmp/archive', TMP_ROOT='/tmp/staging')
    def test_get_roots(self):
        """測試取得路徑設定"""
        self.assertEqual(utils.get_archive_root(), '/tmp/archive')
        self.assertEqual(utils.get_tmp_root(), '/tmp/staging')

    def test_is_archived(self):
        """測試是否為封存路徑"""
        self.assertTrue(utils.is_archived('archived://vol/file'))
        self.assertFalse(utils.is_archived('uploads/file'))
        self.assertFalse(utils.is_archived(None))

    def test_parse_archive_path(self):
        """測試解析封存路徑"""
        path = 'archived://VOL01/abc.pdf'
        result = utils.parse_archive_path(path)
        self.assertEqual(result['folder_name'], 'VOL01')
        self.assertEqual(result['uuid_filename'], 'abc.pdf')

        self.assertIsNone(utils.parse_archive_path('invalid'))
        self.assertIsNone(utils.parse_archive_path('archived://incomplete'))

    def test_build_archive_path(self):
        """測試建構封存路徑"""
        path = utils.build_archive_path('VOL01', 'abc.pdf')
        self.assertEqual(path, 'archived://VOL01/abc.pdf')

    def test_get_file_extension(self):
        """測試取得副檔名"""
        self.assertEqual(utils.get_file_extension('test.PDF'), '.pdf')
        self.assertEqual(utils.get_file_extension('/path/to/test.txt'), '.txt')
        self.assertEqual(utils.get_file_extension('noext'), '')
