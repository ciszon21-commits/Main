import requests
import json
import re
from django.core.management.base import BaseCommand
from ...models import SoilMove

class Command(BaseCommand):
    help = 'Fetches soil temporary storage data from soilmove.tw and updates the database.'

    def handle(self, *args, **options):
        url = "https://www.soilmove.tw/soilmove/dumpsiteGisQueryList"
        self.stdout.write(f"Fetching data from {url}...")

        try:
            response = requests.get(url, verify=False) # Skip verify if SSL issues persist in environment
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict):
                 if 'data' in data and isinstance(data['data'], list):
                     data = data['data']
                 elif 'items' in data and isinstance(data['items'], list):
                     data = data['items']

            if not isinstance(data, list):
                self.stderr.write(self.style.ERROR(f"Unexpected data format: {type(data)}. Expected list."))
                return

            self.stdout.write(f"Found {len(data)} records. Starting sync...")
            
            created_count = 0
            updated_count = 0

            for item in data:
                site_id = item.get('id')
                if not site_id:
                    continue

                defaults = {
                    'name': item.get('dumpname'),
                    'city': item.get('city'),
                    'remain_capacity': item.get('remain'),
                    'coord_status': item.get('coord_status'),
                    'site_type': item.get('typename'),
                    'control_id': item.get('controlId'),
                    'longitude': item.get('y'), 
                    'latitude': item.get('x'),  
                    'area': item.get('area'),
                    'max_capacity': item.get('maxbury'),
                    'apply_date': item.get('applydate'),
                }
                
                # Clean up numeric fields
                for field in ['remain_capacity', 'longitude', 'latitude', 'area', 'max_capacity']:
                    val = defaults[field]
                    if val == '':
                         defaults[field] = None
                    elif isinstance(val, str):
                        try:
                            defaults[field] = float(val)
                        except ValueError:
                            defaults[field] = None
                
                # Calculate status based on name
                name = defaults.get('name', '')
                if re.search(r'暫停|停止|停場|註銷|屆滿|封場|廢止|撤銷|終止', name):
                    defaults['status'] = '停止'
                else:
                    defaults['status'] = '正常'

                obj, created = SoilMove.objects.update_or_create(
                    site_id=site_id,
                    defaults=defaults
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(self.style.SUCCESS(f"Sync complete. Created: {created_count}, Updated: {updated_count}"))

        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Network error: {e}"))
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"JSON decode error: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
