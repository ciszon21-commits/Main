
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from GeoCoding.models import County, Township
from GeoCoding.services import get_geocoding_service
from GeoDataHub.models import GeoDataSource
from GeoDataHub.services import GeocodingService, OpenSearchMappingService


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
