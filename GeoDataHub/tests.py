
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from GeoCoding.models import County, Township
from GeoCoding.services import get_geocoding_service
from GeoDataHub.models import GeoDataSource, GeoCategory
from GeoDataHub.services import GeocodingService, OpenSearchMappingService
from django.contrib.auth import get_user_model

User = get_user_model()


class GeoCodingIntegrationTest(TestCase):
    def setUp(self):
        self.county = County.objects.create(
            name='臺北市',
            latitude=25.0375,
            longitude=121.5637,
        )
        self.township = Township.objects.create(
            county=self.county,
            name='中山區',
            latitude=25.06315,
            longitude=121.5331,
        )
        # 確保 GeoCoding 快取重新載入測試資料
        self.local_geocoder = get_geocoding_service()
        self.local_geocoder.refresh_cache()

    def _create_opensearch_source(self, title: str = '臺北市中山區'):
        return GeoDataSource.objects.create(
            title=title,
            description='',
            source_type=GeoDataSource.SourceType.OPENSEARCH,
            opensearch_index='sino_map',
            metadata={'title': title}
        )

    def test_geocode_address_prefers_local_dataset(self):
        service = GeocodingService()
        self.assertIsNotNone(service.internal_geocoder)

        result = service.geocode_address('臺北市中山區')

        self.assertIsNotNone(result)
        self.assertEqual(result['source'], 'GeoCoding')
        self.assertAlmostEqual(result['latitude'], self.township.latitude, places=5)
        self.assertAlmostEqual(result['longitude'], self.township.longitude, places=5)
        self.assertEqual(result['address'].get('county'), '臺北市')
        self.assertEqual(result['address'].get('township'), '中山區')

    def test_resolve_location_uses_local_match(self):
        mapping_service = OpenSearchMappingService()
        self.assertIsNotNone(mapping_service.geocoder.internal_geocoder)
        mapping_service.geocoder.internal_geocoder.refresh_cache()

        location = mapping_service._resolve_location({'title': '中山區'})

        self.assertIsNotNone(location)
        self.assertAlmostEqual(float(location.latitude), self.township.latitude, places=5)
        self.assertAlmostEqual(float(location.longitude), self.township.longitude, places=5)
        self.assertEqual(location.city, '臺北市')
        self.assertEqual(location.district, '中山區')

    def test_location_stage_updates_data_sources(self):
        source = self._create_opensearch_source()
        mapping_service = OpenSearchMappingService()
        mapping_service.geocoder.internal_geocoder.refresh_cache()

        result = mapping_service.sync_sino_maps_two_stage(mode='location')

        self.assertIn('location_stage', result)
        self.assertEqual(result['location_stage']['status'], 'success')
        self.assertEqual(result['location_stage']['updated'], 1)

        source.refresh_from_db()
        self.assertIsNotNone(source.location)
        self.assertAlmostEqual(float(source.location.latitude), self.township.latitude, places=5)
        self.assertAlmostEqual(float(source.location.longitude), self.township.longitude, places=5)
        self.assertEqual(source.location.city, '臺北市')
        self.assertEqual(source.location.district, '中山區')

    def test_sync_geodata_command_updates_locations(self):
        source = self._create_opensearch_source(title='臺北市中山區第二筆')
        out = StringIO()

        call_command('sync_geodata', mode='location', batch_size=1, stdout=out)

        self.assertIn('同步任務執行完畢', out.getvalue())
        source.refresh_from_db()
        self.assertIsNotNone(source.location)
        self.assertAlmostEqual(float(source.location.latitude), self.township.latitude, places=5)
        self.assertEqual(source.location.city, '臺北市')
        self.assertEqual(source.location.district, '中山區')


class GeoClickLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = GeoCategory.objects.create(name='Test Category')
        self.source = GeoDataSource.objects.create(
            title='Test Source',
            source_type=GeoDataSource.SourceType.UPLOAD,
            category=self.category,
            created_by=self.user
        )

    def test_api_log_click(self):
        from django.urls import reverse
        from GeoDataHub.models import GeoClickLog
        import json
        
        url = reverse('geodatahub:api_log_click')
        data = {
            'source_id': self.source.id,
            'category_id': self.category.id,
            'click_type': 'view_detail'
        }
        
        # Login
        self.client.login(username='testuser', password='password')
        
        response = self.client.post(url, data, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        self.assertEqual(GeoClickLog.objects.count(), 1)
        log = GeoClickLog.objects.first()
        self.assertEqual(log.source.id, self.source.id)
        self.assertEqual(log.user.id, self.user.id)
        self.assertEqual(log.category.id, self.category.id)

    def test_detail_view_logs_click(self):
        from django.urls import reverse
        from GeoDataHub.models import GeoClickLog
        
        url = reverse('geodatahub:source_detail', kwargs={'pk': self.source.id})
        
        # Initial count
        self.assertEqual(GeoClickLog.objects.count(), 0)
        
        # Visit detail page
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check if log was created
        self.assertEqual(GeoClickLog.objects.count(), 1)
        log = GeoClickLog.objects.first()
        self.assertEqual(log.source.id, self.source.id)
        self.assertEqual(log.click_type, GeoClickLog.ClickType.VIEW_DETAIL)


class DashboardTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.superuser = User.objects.create_superuser(username='admin', password='password', email='admin@example.com')

    def test_dashboard_access(self):
        from django.urls import reverse
        url = reverse('geodatahub:dashboard')
        
        # Public access
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '使用量儀表板')
        self.assertNotContains(response, 'superuser-logs')  # Public shouldn't see logs table
        
        # Superuser access
        self.client.force_login(self.superuser, backend='django.contrib.auth.backends.ModelBackend')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'superuser-logs')  # Superuser should see logs table
        self.assertIn('recent_logs', response.context)
        self.assertTrue(len(response.context['recent_logs']) >= 0)

