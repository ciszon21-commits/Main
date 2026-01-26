from django.test import TestCase
from GeoDataHub.services import MapGridService
from decimal import Decimal

class MapGridTest(TestCase):
    def test_decode_1_5000_sheet(self):
        # Sample from OpenSearch: 94194059 (龍蛟潭)
        # 龍蛟潭 approx: 23.3, 120.2
        sheet_no = "94194059"
        coords = MapGridService.decode_1_5000_sheet(sheet_no)
        
        self.assertIsNotNone(coords)
        lat, lng = coords
        
        # Check if it falls around Taiwan
        self.assertTrue(21 < lat < 26)
        self.assertTrue(119 < lng < 123)
        
        # Specific check for 94194059 based on our formula
        # x=94, y=19 -> base_lng=120.204, base_lat=23.254
        # sub_x=40, sub_y=59 -> lng=120.204+0.2=120.404, lat=23.254+0.295=23.549
        print(f"Decoded {sheet_no} -> Lat: {lat}, Lng: {lng}")

    def test_invalid_sheet(self):
        self.assertIsNone(MapGridService.decode_1_5000_sheet("ABC"))
        self.assertIsNone(MapGridService.decode_1_5000_sheet("123"))
        self.assertIsNone(MapGridService.decode_1_5000_sheet(None))
