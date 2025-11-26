#!/usr/bin/env python3
"""
Cross-platform path compatibility test for SinoArchive app.
Tests the fixed path handling to ensure compatibility between Windows and Ubuntu.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSinoArchiveCrossPlatformPaths(TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_windows_unc_paths = [
            '\\\\192.168.1.100\\filed\\documents\\test.pdf',
            '\\\\server\\share\\folder\\file.dwg',
            '\\\\10.0.0.1\\backup\\archives\\data.zip',
        ]
        
        self.test_regular_paths = [
            'media/photos/test/file.jpg',
            'media\\photos\\test\\file.jpg',
            '/media/photos/test/file.jpg',
            '\\media\\photos\\test\\file.jpg',
        ]
        
    def test_win_path_to_unix_conversion(self):
        """Test Windows UNC path to Unix mount path conversion."""
        from SinoArchive.model_managers import win_path_to_unix
        
        # Test with UBUNTU setting enabled
        with patch.object(settings, 'UBUNTU', True):
            # Test normal UNC path conversion
            win_path = '\\\\192.168.1.100\\filed\\documents\\test.pdf'
            expected = '/mnt/filed/documents/test.pdf'
            result = win_path_to_unix(win_path)
            self.assertEqual(os.path.normpath(result), os.path.normpath(expected),
                           f"UNC path conversion failed. Expected: {expected}, Got: {result}")
            
            # Test share root path
            win_path = '\\\\server\\share'
            expected = '/mnt/share'
            result = win_path_to_unix(win_path)
            self.assertEqual(os.path.normpath(result), os.path.normpath(expected),
                           f"Share root conversion failed. Expected: {expected}, Got: {result}")
            
            # Test with custom mount point
            result = win_path_to_unix('\\\\server\\data\\file.txt', base_mount='/custom')
            expected = '/custom/data/file.txt'
            self.assertEqual(os.path.normpath(result), os.path.normpath(expected))
        
        # Test with UBUNTU setting disabled (should return original path)
        with patch.object(settings, 'UBUNTU', False):
            win_path = '\\\\192.168.1.100\\filed\\documents\\test.pdf'
            result = win_path_to_unix(win_path)
            self.assertEqual(result, win_path,
                           "Path should be unchanged when UBUNTU=False")
    
    def test_win_path_to_unix_error_handling(self):
        """Test error handling for invalid UNC paths."""
        from SinoArchive.model_managers import win_path_to_unix
        
        with patch.object(settings, 'UBUNTU', True):
            # Test invalid path (too short)
            with self.assertRaises(ValueError) as context:
                win_path_to_unix('\\\\server')
            
            self.assertIn('路徑格式錯誤', str(context.exception))
            
            # Test empty path
            with self.assertRaises(ValueError):
                win_path_to_unix('')

    def test_archive_file_path_methods(self):
        """Test ArchiveFile model path methods."""
        # Mock the ArchiveFile model
        with patch('SinoArchive.models.ArchiveFile') as MockArchiveFile:
            # Create a mock instance
            mock_instance = MagicMock()
            mock_instance.folder = 'BIM00001'
            mock_instance.UUID = '12345678-1234-1234-1234-123456789abc'
            mock_instance.ext = '.pdf'
            
            # Import the model methods after setting up mocks
            from SinoArchive.models import ArchiveFile
            
            # Test get_full_path method (should use os.path.join)
            result = ArchiveFile.get_full_path(mock_instance)
            expected_parts = [mock_instance.folder, f"{mock_instance.UUID}{mock_instance.ext}"]
            
            # Verify that the result contains the expected components
            self.assertIn(str(mock_instance.UUID), result)
            self.assertIn(mock_instance.ext, result)
            self.assertIn(str(mock_instance.folder), result)

    def test_archive_file_full_path_property(self):
        """Test ArchiveFile full_path property uses os.path.join."""
        from SinoArchive.model_methods import ArchiveFile
        
        # Mock settings
        with patch('SinoArchive.model_methods.settings') as mock_settings:
            mock_settings.MEDIA_DIR = '/var/media' if os.name != 'nt' else 'C:\\media'
            
            # Create a mock instance
            mock_instance = MagicMock()
            mock_instance.file = 'photos/test/file.jpg'
            
            # Test the full_path method
            result = ArchiveFile.full_path(mock_instance)
            
            # Verify that the result is properly joined
            expected = os.path.join(mock_settings.MEDIA_DIR, mock_instance.file)
            self.assertEqual(result, expected,
                           f"full_path should use os.path.join. Expected: {expected}, Got: {result}")

    def test_template_tag_media_path(self):
        """Test archive_path template tag cross-platform compatibility."""
        from SinoArchive.templatetags.archive_path import setMediaPath
        
        # Test various path formats
        test_cases = [
            ('media/photos/test.jpg', '/media/photos/test.jpg'),
            ('media\\photos\\test.jpg', '/media/photos/test.jpg'),
            ('/media/photos/test.jpg', '/media/photos/test.jpg'),
            ('\\media\\photos\\test.jpg', '/media/photos/test.jpg'),
            ('photos/test.jpg', '/media/photos/test.jpg'),
            ('photos\\test.jpg', '/media/photos/test.jpg'),
        ]
        
        for input_path, expected_output in test_cases:
            result = setMediaPath(input_path)
            self.assertEqual(result, expected_output,
                           f"setMediaPath failed for {input_path}. Expected: {expected_output}, Got: {result}")

    def test_archive_manager_path_normalization(self):
        """Test ArchiveFile manager path normalization."""
        from SinoArchive.model_managers import ArchiveFile as ArchiveFileManager
        
        # Mock the dependencies
        with patch('SinoArchive.model_managers.File') as mock_file, \
             patch('SinoArchive.model_managers.models') as mock_models, \
             patch('SinoArchive.model_managers.PmisModels') as mock_pmis:
            
            # Setup mocks
            mock_file.setFileLocalPath.return_value = 'photos/test/file.jpg'
            mock_models.ArchiveFile.objects.filter.return_value.first.return_value = None
            
            manager = ArchiveFileManager()
            
            # Test get_archive_path with various path formats
            test_paths = [
                'media/photos/test/file.jpg',
                'media\\photos\\test\\file.jpg',
                '/media/photos/test/file.jpg',
            ]
            
            for path in test_paths:
                # This should not raise an exception
                result = manager.get_archive_path(path)
                # Since our mock returns None, result should be empty string
                self.assertEqual(result, '')
                
                # Verify that setFileLocalPath was called
                mock_file.setFileLocalPath.assert_called()

def run_tests():
    """Run the SinoArchive cross-platform compatibility tests."""
    # Note: This would normally be run with Django's test runner
    # python manage.py test SinoArchive.tests.test_cross_platform_paths
    pass

if __name__ == '__main__':
    print("SinoArchive Cross-platform Path Compatibility Tests")
    print(f"Operating System: {os.name}")
    print(f"Platform: {sys.platform}")
    print(f"Path separator: '{os.sep}'")
    print("-" * 50)
    print("Note: Run with Django test runner:")
    print("python manage.py test SinoArchive.tests.test_cross_platform_paths")