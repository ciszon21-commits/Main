from django.test import TestCase
from django.utils import timezone
from SinoFile.models import ArchiveFolder

class ArchiveFolderModelTest(TestCase):

    def setUp(self):
        self.folder = ArchiveFolder.objects.create(
            folder_name='TEST_VOL_001',
            max_size=1024 * 1024 * 100  # 100 MB
        )

    def test_initial_status(self):
        """測試初始狀態應為 STAGING"""
        self.assertEqual(self.folder.status, ArchiveFolder.Status.STAGING)
        self.assertEqual(self.folder.total_size, 0)
        self.assertIsNone(self.folder.closed_at)
        self.assertIsNone(self.folder.archived_at)

    def test_string_representation(self):
        """測試 __str__ 方法"""
        expected_str = f'TEST_VOL_001 (暫存中)'
        self.assertEqual(str(self.folder), expected_str)

    def test_get_remaining_space(self):
        """測試剩餘空間計算"""
        initial_space = self.folder.get_remaining_space()
        self.assertEqual(initial_space, 100 * 1024 * 1024)

        # 模擬加入檔案佔用空間
        self.folder.total_size = 50 * 1024 * 1024
        self.folder.save()
        
        remaining = self.folder.get_remaining_space()
        self.assertEqual(remaining, 50 * 1024 * 1024)

        # 模擬爆滿
        self.folder.total_size = 110 * 1024 * 1024
        self.folder.save()
        self.assertEqual(self.folder.get_remaining_space(), 0)

    def test_can_add_file(self):
        """測試是否可加入檔案"""
        # 剛好可以放入 100MB
        self.assertTrue(self.folder.can_add_file(100 * 1024 * 1024))
        # 超過就不行
        self.assertFalse(self.folder.can_add_file(100 * 1024 * 1024 + 1))

        # 狀態改變後應無法加入
        self.folder.status = ArchiveFolder.Status.CLOSED
        self.folder.save()
        self.assertFalse(self.folder.can_add_file(1024))

    def test_add_to_manifest(self):
        """測試加入清單"""
        self.folder.add_to_manifest(
            original_path='uploads/test.pdf',
            uuid_filename='abc-123.pdf',
            file_size=1024,
            model_label='myapp.MyModel',
            field_name='file',
            instance_pk=1
        )
        
        self.assertEqual(self.folder.total_size, 1024)
        self.assertEqual(len(self.folder.manifest_data['files']), 1)
        
        file_entry = self.folder.manifest_data['files'][0]
        self.assertEqual(file_entry['original_path'], 'uploads/test.pdf')
        self.assertEqual(file_entry['uuid_filename'], 'abc-123.pdf')

    def test_close_folder(self):
        """測試封閉資料夾"""
        self.folder.close()
        self.assertEqual(self.folder.status, ArchiveFolder.Status.CLOSED)
        self.assertIsNotNone(self.folder.closed_at)

    def test_archive_folder(self):
        """測試標記為已封存"""
        self.folder.archive()
        self.assertEqual(self.folder.status, ArchiveFolder.Status.ARCHIVED)
        self.assertIsNotNone(self.folder.archived_at)

    def test_get_file_count(self):
        """測試取得檔案數量"""
        self.assertEqual(self.folder.get_file_count(), 0)
        
        self.folder.add_to_manifest('a', 'b', 100, 'm', 'f', 1)
        self.assertEqual(self.folder.get_file_count(), 1)

    def test_get_human_size(self):
        """測試人類可讀大小"""
        self.folder.total_size = 500
        self.assertEqual(self.folder.get_human_size(), '500.0 B')
        
        self.folder.total_size = 1024
        self.assertEqual(self.folder.get_human_size(), '1.0 KB')
        
        self.folder.total_size = 1024 * 1024 * 1.5
        self.assertEqual(self.folder.get_human_size(), '1.5 MB')
