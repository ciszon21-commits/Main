import json
import logging
import re
import ssl
import time
import urllib.request
from collections import defaultdict
from datetime import datetime
from html import unescape

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .plant_coordinates import get_plant_name, PLANT_COORDINATES


TAIPOWER_API_URL = 'https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.json'
TAIPOWER_CACHE_KEY = 'energymap:taipower:fresh'
TAIPOWER_STALE_CACHE_KEY = 'energymap:taipower:stale'
TAIPOWER_REFRESH_LOCK_KEY = 'energymap:taipower:refresh_lock'
TAIPOWER_CACHE_TTL_SECONDS = 300
TAIPOWER_STALE_TTL_SECONDS = 3600
TAIPOWER_REFRESH_LOCK_TIMEOUT_SECONDS = 30
TAIPOWER_REFRESH_WAIT_TIMEOUT_SECONDS = 20
TAIPOWER_REFRESH_WAIT_INTERVAL_SECONDS = 0.25
ENERGYMAP_LOAD_ERROR_MESSAGE = 'Unable to load energy data right now.'

logger = logging.getLogger(__name__)

# 能源類型對照（HTML anchor name → 中文/英文標籤）
ENERGY_TYPE_MAP = {
    'lng': {'zh': '燃氣', 'en': 'LNG', 'color': '#3b82f6'},
    'ipplng': {'zh': '民營燃氣', 'en': 'IPP-LNG', 'color': '#60a5fa'},
    'coal': {'zh': '燃煤', 'en': 'Coal', 'color': '#6b7280'},
    'ippcoal': {'zh': '民營燃煤', 'en': 'IPP-Coal', 'color': '#9ca3af'},
    'cogen': {'zh': '汽電共生', 'en': 'Co-Gen', 'color': '#f59e0b'},
    'fueloil': {'zh': '燃油', 'en': 'Fuel Oil', 'color': '#ef4444'},
    'solar': {'zh': '太陽能', 'en': 'Solar', 'color': '#eab308'},
    'wind': {'zh': '風力', 'en': 'Wind', 'color': '#22c55e'},
    'hydro': {'zh': '水力', 'en': 'Hydro', 'color': '#06b6d4'},
    'EnergyStorageSystem': {'zh': '儲能', 'en': 'Energy Storage', 'color': '#a855f7'},
    'OtherRenewableEnergy': {'zh': '其它再生能源', 'en': 'Other Renewable', 'color': '#14b8a6'},
    'EnergyStorageSystemLoad': {'zh': '儲能負載', 'en': 'Storage Load', 'color': '#7c3aed'},
}

TYPE_ORDER = [
    'lng',
    'ipplng',
    'coal',
    'ippcoal',
    'cogen',
    'fueloil',
    'solar',
    'wind',
    'hydro',
    'EnergyStorageSystem',
    'OtherRenewableEnergy',
]

PANEL_ONLY_TYPE_KEYS = {
    'OtherRenewableEnergy',
    'cogen',
}

PANEL_ONLY_NAMES_BY_TYPE = {
    'solar': {'其它台電自有', '其它購電太陽能'},
    'wind': {'其它台電自有', '其它購電風力'},
    'EnergyStorageSystem': {'電池'},
    'fueloil': {'離島其它'},
}

MERGED_SOURCE_NAMES = {
    '龍A風': '海龍二',
    '龍B風': '海龍二',
    '允湖': '雲林離岸風場',
    '允西': '雲林離岸風場',
}

SPLIT_MAP_LOCATIONS = {
    '嘉南西口、烏山頭和八田': [
        {'name': '嘉南西口'},
        {'name': '烏山頭'},
        {'name': '八田'},
    ],
    '烏來&桂山&粗坑': [
        {'name': '烏來'},
        {'name': '桂山'},
        {'name': '粗坑'},
    ],
    '觀威觀音&桃威新屋': [
        {'name': '觀威觀音'},
        {'name': '桃威新屋'},
    ],
    '芳一風': [
        {'name': '芳一風(彰芳)'},
        {'name': '芳一風(西島)'},
    ],
    '雲林離岸風場': [
        {'name': '允湖', 'label': '雲林離岸風場 - 允湖'},
        {'name': '允西', 'label': '雲林離岸風場 - 允西'},
    ],
}


def _fetch_taipower_data():
    """從台電 API 擷取即時發電資料"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        TAIPOWER_API_URL,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        raw = resp.read().decode('utf-8')
    return json.loads(raw)


def _build_cache_payload(raw_data):
    source_update_time = _extract_source_update_time(raw_data)
    return {
        'raw_data': raw_data,
        'fetched_at': timezone.now().isoformat(),
        'source_update_time': source_update_time,
    }


def _cache_meta(cache_state, payload):
    return {
        'cache_state': cache_state,
        'fetched_at': payload.get('fetched_at'),
        'source_update_time': payload.get('source_update_time'),
    }


def _extract_source_update_time(raw_data):
    candidates = [
        raw_data.get('update_time'),
        raw_data.get('UpdateTime'),
        raw_data.get('updatetime'),
        raw_data.get(''),
    ]

    for candidate in candidates:
        if candidate:
            return str(candidate).strip()

    return ''


def _parse_cached_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _payload_is_fresh(payload, now=None):
    if not payload:
        return False

    fetched_at = _parse_cached_datetime(payload.get('fetched_at'))
    if fetched_at is None:
        return False

    reference_time = now or timezone.now()
    return (reference_time - fetched_at).total_seconds() < TAIPOWER_CACHE_TTL_SECONDS


def _wait_for_fresh_cache(previous_fetched_at=None):
    deadline = time.monotonic() + TAIPOWER_REFRESH_WAIT_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        cached_payload = cache.get(TAIPOWER_CACHE_KEY)
        if _payload_is_fresh(cached_payload):
            if previous_fetched_at is None or cached_payload.get('fetched_at') != previous_fetched_at:
                return cached_payload
            return cached_payload
        if previous_fetched_at and cached_payload and cached_payload.get('fetched_at') != previous_fetched_at:
            return cached_payload
        time.sleep(TAIPOWER_REFRESH_WAIT_INTERVAL_SECONDS)

    return None


def _get_taipower_data(force_refresh=False):
    now = timezone.now()
    cached_payload = cache.get(TAIPOWER_CACHE_KEY)
    if not force_refresh and _payload_is_fresh(cached_payload, now):
        return cached_payload['raw_data'], _cache_meta('fresh_cache', cached_payload)

    stale_payload = cache.get(TAIPOWER_STALE_CACHE_KEY) or cached_payload

    acquired_lock = cache.add(
        TAIPOWER_REFRESH_LOCK_KEY,
        '1',
        TAIPOWER_REFRESH_LOCK_TIMEOUT_SECONDS,
    )

    if not acquired_lock:
        waited_payload = _wait_for_fresh_cache(cached_payload.get('fetched_at') if cached_payload else None)
        if waited_payload:
            return waited_payload['raw_data'], _cache_meta('fresh_cache_wait', waited_payload)

        if stale_payload:
            return stale_payload['raw_data'], _cache_meta('stale_while_revalidate', stale_payload)

        raise RuntimeError('Taipower refresh is already in progress.')

    try:
        raw_data = _fetch_taipower_data()
    except Exception:
        cache.delete(TAIPOWER_REFRESH_LOCK_KEY)
        if stale_payload:
            logger.warning('Serving stale Taipower data after upstream fetch failure.', exc_info=True)
            return stale_payload['raw_data'], _cache_meta('stale_cache', stale_payload)
        raise

    cache_payload = _build_cache_payload(raw_data)
    try:
        cache.set(TAIPOWER_CACHE_KEY, cache_payload, TAIPOWER_CACHE_TTL_SECONDS)
        cache.set(TAIPOWER_STALE_CACHE_KEY, cache_payload, TAIPOWER_STALE_TTL_SECONDS)
    finally:
        cache.delete(TAIPOWER_REFRESH_LOCK_KEY)

    return raw_data, _cache_meta('live', cache_payload)


def _parse_energy_type(html_str):
    """
    從 HTML 標籤解析能源類型 key。
    例如：<A NAME='lng'></A><b>燃氣(LNG)</b> → 'lng'
    """
    match = re.search(r"NAME='(\w+)'", html_str)
    if match:
        return match.group(1)
    return 'unknown'


def _parse_energy_label(html_str):
    match = re.search(r'<b>(.*?)</b>', html_str)
    return unescape(match.group(1)).strip() if match else ''


def _get_type_info(type_key, type_html=''):
    type_info = ENERGY_TYPE_MAP.get(type_key)
    if type_info:
        return type_info

    label = _parse_energy_label(type_html)
    zh = re.sub(r'\s*\([^)]*\)\s*$', '', label).strip() or type_key
    en_match = re.search(r'\(([^)]*)\)', label)
    en = en_match.group(1).strip() if en_match else type_key
    return {'zh': zh, 'en': en, 'color': '#888888'}


def _parse_numeric_prefix(value, default=0):
    match = re.match(r'(-?[\d.]+)', str(value).strip())
    if not match:
        return default

    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return default


def _is_subtotal_row(name):
    return str(name).strip().startswith('小計')


def _clean_sub_type(sub_type):
    return re.sub(r'\(註\d+\)', '', unescape(sub_type or '')).strip() or '未分類'


def _strip_note_suffix(name):
    return re.sub(r'\(註\d+\)', '', unescape(name or '')).strip()


def _has_recorded_split_coordinates(name):
    return any(PLANT_COORDINATES.get(location['name']) for location in SPLIT_MAP_LOCATIONS.get(name, []))


def _ordered_type_keys(*collections):
    seen = set()
    ordered = []

    for type_key in TYPE_ORDER:
        if any(type_key in collection for collection in collections):
            ordered.append(type_key)
            seen.add(type_key)

    extras = set()
    for collection in collections:
        extras.update(collection)

    for type_key in sorted(extras):
        if type_key not in seen:
            ordered.append(type_key)

    return ordered


def _resolve_entry_display(unit, plant_name, has_exact_location):
    normalized_name = _strip_note_suffix(unit['name'])
    merged_name = MERGED_SOURCE_NAMES.get(normalized_name)
    has_split_coordinates = _has_recorded_split_coordinates(normalized_name)

    if merged_name:
        if merged_name in SPLIT_MAP_LOCATIONS:
            has_merged_split_coordinates = _has_recorded_split_coordinates(merged_name)
            return {
                'entry_name': merged_name,
                'on_map': has_merged_split_coordinates,
                'location_mode': 'exact' if has_merged_split_coordinates else 'no_location',
                'location_note': '' if has_merged_split_coordinates else '尚未在 plant_coordinates.py 設定座標，因此僅在右側面板顯示。',
            }

        merged_coords = PLANT_COORDINATES.get(merged_name)
        return {
            'entry_name': merged_name,
            'on_map': bool(merged_coords),
            'location_mode': 'exact' if merged_coords else 'no_location',
            'location_note': '' if merged_coords else '尚未設定座標，因此僅在右側面板顯示。',
        }

    if normalized_name in SPLIT_MAP_LOCATIONS:
        return {
            'entry_name': normalized_name,
            'on_map': has_split_coordinates,
            'location_mode': 'exact' if has_split_coordinates else 'no_location',
            'location_note': '' if has_split_coordinates else '尚未設定座標，因此僅在右側面板顯示。',
        }

    if unit['type_key'] == 'hydro' and '小水力' in normalized_name:
        return {
            'entry_name': '小水力',
            'on_map': False,
            'location_mode': 'no_location',
            'location_note': '各區小水力已整併為單一電廠項目，目前未設定座標，因此僅在右側面板顯示。',
        }

    if unit['type_key'] in PANEL_ONLY_TYPE_KEYS or normalized_name in PANEL_ONLY_NAMES_BY_TYPE.get(unit['type_key'], set()):
        return {
            'entry_name': plant_name if has_exact_location else normalized_name,
            'on_map': False,
            'location_mode': 'no_location',
            'location_note': '尚未設定座標，因此僅在右側面板顯示。',
        }

    if has_exact_location:
        return {
            'entry_name': plant_name,
            'on_map': True,
            'location_mode': 'exact',
            'location_note': '',
        }

    return {
        'entry_name': unit['name'],
        'on_map': False,
        'location_mode': 'no_location',
        'location_note': '尚未設定座標，因此僅在右側面板顯示。',
    }


def _get_marker_locations(map_plant):
    split_locations = SPLIT_MAP_LOCATIONS.get(map_plant['name'])
    if split_locations:
        resolved_locations = []
        for location in split_locations:
            coords = PLANT_COORDINATES.get(location['name'])
            if not coords:
                continue
            lat, lng = coords

            resolved_locations.append({
                'name': location.get('label', location['name']),
                'lat': lat,
                'lng': lng,
            })
        return resolved_locations

    return [{
        'name': map_plant['name'],
        'lat': map_plant['lat'],
        'lng': map_plant['lng'],
    }]


def _parse_generation_data(raw_data):
    """
    解析台電 JSON，回傳結構化資料。
    回傳:
        update_time: str
        summary: dict  {type_key: {zh, en, color, capacity, generation}}
        units: list  [{type_key, sub_type, name, capacity, generation, rate, note}]
    """
    update_time = raw_data.get('', '')
    aa_data = raw_data.get('aaData', [])

    summary = {}
    units = []

    for row in aa_data:
        if len(row) < 7:
            continue

        type_html = row[0]
        sub_type = row[1]
        name = unescape(row[2]).strip()
        capacity_str = row[3]
        generation_str = row[4]

        type_key = _parse_energy_type(type_html)

        # 小計行 (subtotal)
        if _is_subtotal_row(name):
            cap_val = _parse_numeric_prefix(capacity_str, default=0)
            gen_val = _parse_numeric_prefix(generation_str, default=0)

            type_info = _get_type_info(type_key, type_html)
            summary[type_key] = {
                'zh': type_info['zh'],
                'en': type_info['en'],
                'color': type_info['color'],
                'capacity': cap_val,
                'generation': gen_val,
            }
            continue

        # 個別機組
        gen_val = _parse_numeric_prefix(generation_str, default=0)
        cap_val = None if capacity_str == '-' else _parse_numeric_prefix(capacity_str, default=None)

        rate = row[5] if len(row) > 5 else ''
        note = row[6].strip() if len(row) > 6 else ''

        units.append({
            'type_key': type_key,
            'sub_type': unescape(sub_type).strip() if sub_type else '',
            'name': name,
            'capacity': cap_val,
            'generation': gen_val,
            'rate': rate,
            'note': note,
        })

    return update_time, summary, units


def _get_generation_payload(force_refresh=False):
    raw_data, fetch_meta = _get_taipower_data(force_refresh=force_refresh)
    update_time, summary, units = _parse_generation_data(raw_data)
    return {
        'update_time': update_time,
        'summary': summary,
        'units': units,
        **fetch_meta,
    }


def _should_force_refresh(request):
    return str(request.GET.get('refresh', '')).strip().lower() in {'1', 'true', 'yes', 'force'}


def dashboard_view(request):
    """Dashboard 頁面"""
    return render(request, 'EnergyMap/dashboard.html')


def map_view(request):
    """地圖頁面"""
    return render(request, 'EnergyMap/map.html')


def api_energy_data(request):
    """API: 回傳各能源類型的發電量彙總"""
    try:
        payload = _get_generation_payload(force_refresh=_should_force_refresh(request))
        update_time = payload['update_time']
        summary = payload['summary']

        # 排除儲能負載 (負值概念)
        display_summary = {
            k: v for k, v in summary.items()
            if k != 'EnergyStorageSystemLoad'
        }
        ordered_keys = _ordered_type_keys(display_summary)
        ordered_summary = {k: display_summary[k] for k in ordered_keys}

        # 計算總發電量
        total_gen = sum(v['generation'] for v in ordered_summary.values())

        return JsonResponse({
            'success': True,
            'update_time': update_time,
            'total_generation': round(total_gen, 1),
            'summary': ordered_summary,
            'cache_state': payload['cache_state'],
            'fetched_at': payload['fetched_at'],
        })
    except Exception:
        logger.exception('Energy summary API failed.')
        return JsonResponse({
            'success': False,
            'error': ENERGYMAP_LOAD_ERROR_MESSAGE,
        }, status=500)


def api_plant_locations(request):
    """API: 回傳各電廠位置與即時資料"""
    try:
        payload = _get_generation_payload(force_refresh=_should_force_refresh(request))
        update_time = payload['update_time']
        summary = payload['summary']
        units = payload['units']

        # 右側面板保留能源別拆分資料；地圖則另外整併同址多能源電廠。
        panel_plants = {}
        battery_load_by_name = defaultdict(float)

        for unit in units:
            if unit['type_key'] != 'EnergyStorageSystemLoad':
                continue
            if 'Battery' not in unit['sub_type']:
                continue
            battery_load_by_name[_strip_note_suffix(unit['name'])] += unit['generation']

        for unit in units:
            # 跳過儲能負載
            if unit['type_key'] == 'EnergyStorageSystemLoad':
                continue

            plant_name = get_plant_name(unit['name'])
            coords = PLANT_COORDINATES.get(plant_name) if plant_name else None
            type_info = _get_type_info(unit['type_key'])

            has_exact_location = bool(plant_name and coords)
            display = _resolve_entry_display(unit, plant_name, has_exact_location)
            entry_name = display['entry_name']
            entry_key = (unit['type_key'], entry_name)
            group_label = _clean_sub_type(unit['sub_type'])
            entry_coords = PLANT_COORDINATES.get(entry_name) if display['on_map'] else None
            has_entry_coordinates = bool(entry_coords)
            is_battery_storage = (
                unit['type_key'] == 'EnergyStorageSystem'
                and 'Battery' in unit['sub_type']
            )
            charging_generation = battery_load_by_name.get(_strip_note_suffix(unit['name']), 0) if is_battery_storage else 0
            discharging_generation = unit['generation']
            net_generation = discharging_generation + charging_generation

            if entry_key not in panel_plants:
                if display['on_map'] and has_entry_coordinates:
                    lat, lng = entry_coords
                elif display['on_map'] and entry_name in SPLIT_MAP_LOCATIONS:
                    split_locations = _get_marker_locations({'name': entry_name})
                    lat, lng = (
                        (split_locations[0]['lat'], split_locations[0]['lng'])
                        if split_locations
                        else (None, None)
                    )
                elif display['on_map'] and has_exact_location:
                    lat, lng = coords
                else:
                    lat, lng = None, None

                panel_plants[entry_key] = {
                    'id': f"{unit['type_key']}-{len(panel_plants) + 1}",
                    'name': entry_name,
                    'lat': lat,
                    'lng': lng,
                    'type_key': unit['type_key'],
                    'type_zh': type_info['zh'],
                    'type_en': type_info['en'],
                    'color': type_info['color'],
                    'plant_name': entry_name if has_entry_coordinates else (plant_name if has_exact_location else entry_name),
                    'group_label': group_label,
                    'group_labels': [],
                    'on_map': display['on_map'],
                    'location_mode': display['location_mode'],
                    'location_note': display['location_note'],
                    'map_plant_id': None,
                    'is_storage_asset': False,
                    'total_charging': 0,
                    'total_discharging': 0,
                    'total_official_generation': 0,
                    'net_output': 0,
                    'power_flow': 'generating',
                    'units': [],
                    'total_capacity': 0,
                    'total_generation': 0,
                }

            if group_label not in panel_plants[entry_key]['group_labels']:
                panel_plants[entry_key]['group_labels'].append(group_label)

            panel_plants[entry_key]['units'].append({
                'name': unit['name'],
                'sub_type': group_label,
                'type_key': unit['type_key'],
                'type_zh': type_info['zh'],
                'capacity': unit['capacity'],
                'official_generation': discharging_generation,
                'generation': net_generation,
                'discharging_generation': discharging_generation,
                'charging_generation': charging_generation,
                'note': unit['note'],
            })

            if unit['capacity']:
                panel_plants[entry_key]['total_capacity'] += unit['capacity']
            panel_plants[entry_key]['total_official_generation'] += discharging_generation
            panel_plants[entry_key]['total_generation'] += net_generation
            panel_plants[entry_key]['net_output'] += net_generation
            panel_plants[entry_key]['total_discharging'] += max(discharging_generation, 0)
            panel_plants[entry_key]['total_charging'] += abs(min(charging_generation, 0))
            panel_plants[entry_key]['is_storage_asset'] = panel_plants[entry_key]['is_storage_asset'] or is_battery_storage

        # 四捨五入
        for p in panel_plants.values():
            p['total_capacity'] = round(p['total_capacity'], 1)
            p['total_official_generation'] = round(p['total_official_generation'], 1)
            p['total_generation'] = round(p['total_generation'], 1)
            p['net_output'] = round(p['net_output'], 1)
            p['total_charging'] = round(p['total_charging'], 1)
            p['total_discharging'] = round(p['total_discharging'], 1)
            if p['is_storage_asset']:
                if p['net_output'] < 0:
                    p['power_flow'] = 'charging'
                elif p['net_output'] > 0:
                    p['power_flow'] = 'discharging'
                else:
                    p['power_flow'] = 'idle'
            group_labels = p.pop('group_labels', [])
            if len(group_labels) == 1:
                p['group_label'] = group_labels[0]
            elif len(group_labels) > 1:
                p['group_label'] = '多個子分類'

        map_plants = {}
        for panel_plant in panel_plants.values():
            if not panel_plant['on_map']:
                continue

            exact_group_name = (
                panel_plant['name']
                if panel_plant['name'] in SPLIT_MAP_LOCATIONS
                else panel_plant['plant_name']
            )
            map_key = f"exact:{exact_group_name}"
            map_name = exact_group_name

            if map_key not in map_plants:
                map_plants[map_key] = {
                    'id': map_key,
                    'name': map_name,
                    'lat': panel_plant['lat'],
                    'lng': panel_plant['lng'],
                    'on_map': True,
                    'location_mode': panel_plant['location_mode'],
                    'location_note': panel_plant['location_note'],
                    'is_storage_asset': False,
                    'total_charging': 0,
                    'total_discharging': 0,
                    'total_official_generation': 0,
                    'net_output': 0,
                    'power_flow': 'generating',
                    'source_entries': [],
                    'type_keys': [],
                    'type_labels': [],
                    'units': [],
                    'total_capacity': 0,
                    'total_generation': 0,
                }

            map_plant = map_plants[map_key]
            panel_plant['map_plant_id'] = map_key

            map_plant['source_entries'].append({
                'id': panel_plant['id'],
                'name': panel_plant['name'],
                'type_key': panel_plant['type_key'],
                'type_zh': panel_plant['type_zh'],
                'color': panel_plant['color'],
                'group_label': panel_plant['group_label'],
                'total_capacity': panel_plant['total_capacity'],
                'total_official_generation': panel_plant['total_official_generation'],
                'total_generation': panel_plant['total_generation'],
                'total_charging': panel_plant['total_charging'],
                'total_discharging': panel_plant['total_discharging'],
            })

            if panel_plant['type_key'] not in map_plant['type_keys']:
                map_plant['type_keys'].append(panel_plant['type_key'])
                map_plant['type_labels'].append({
                    'key': panel_plant['type_key'],
                    'zh': panel_plant['type_zh'],
                    'color': panel_plant['color'],
                })

            for unit in panel_plant['units']:
                map_plant['units'].append({
                    **unit,
                    'type_key': panel_plant['type_key'],
                    'type_zh': panel_plant['type_zh'],
                    'color': panel_plant['color'],
                })

            map_plant['total_capacity'] += panel_plant['total_capacity']
            map_plant['total_official_generation'] += panel_plant['total_official_generation']
            map_plant['total_generation'] += panel_plant['total_generation']
            map_plant['net_output'] += panel_plant['net_output']
            map_plant['total_charging'] += panel_plant['total_charging']
            map_plant['total_discharging'] += panel_plant['total_discharging']
            map_plant['is_storage_asset'] = map_plant['is_storage_asset'] or panel_plant['is_storage_asset']

        for map_plant in map_plants.values():
            map_plant['total_capacity'] = round(map_plant['total_capacity'], 1)
            map_plant['total_official_generation'] = round(map_plant['total_official_generation'], 1)
            map_plant['total_generation'] = round(map_plant['total_generation'], 1)
            map_plant['net_output'] = round(map_plant['net_output'], 1)
            map_plant['total_charging'] = round(map_plant['total_charging'], 1)
            map_plant['total_discharging'] = round(map_plant['total_discharging'], 1)
            if map_plant['is_storage_asset']:
                if map_plant['net_output'] < 0:
                    map_plant['power_flow'] = 'charging'
                elif map_plant['net_output'] > 0:
                    map_plant['power_flow'] = 'discharging'
                else:
                    map_plant['power_flow'] = 'idle'
            map_plant['type_labels'].sort(
                key=lambda item: TYPE_ORDER.index(item['key']) if item['key'] in TYPE_ORDER else len(TYPE_ORDER)
            )
            map_plant['type_keys'] = [item['key'] for item in map_plant['type_labels']]
            map_plant['units'].sort(
                key=lambda unit: (
                    TYPE_ORDER.index(unit['type_key']) if unit['type_key'] in TYPE_ORDER else len(TYPE_ORDER),
                    unit['sub_type'],
                    unit['name'],
                )
            )
            map_plant['primary_color'] = (
                map_plant['type_labels'][0]['color']
                if len(map_plant['type_labels']) == 1
                else '#cbd5e1'
            )
            map_plant['marker_locations'] = _get_marker_locations(map_plant)

        type_counts = defaultdict(int)
        for plant in panel_plants.values():
            type_counts[plant['type_key']] += 1

        categories = []
        ordered_type_keys = _ordered_type_keys(summary, type_counts)
        for type_key in ordered_type_keys:
            if type_key == 'EnergyStorageSystemLoad':
                continue

            type_info = _get_type_info(type_key)
            summary_entry = summary.get(type_key, {})
            categories.append({
                'key': type_key,
                'zh': type_info['zh'],
                'en': type_info['en'],
                'color': type_info['color'],
                'count': type_counts.get(type_key, 0),
                'generation': round(summary_entry.get('generation', 0), 1),
                'capacity': round(summary_entry.get('capacity', 0), 1),
            })

        return JsonResponse({
            'success': True,
            'update_time': update_time,
            'categories': categories,
            'panel_plants': list(panel_plants.values()),
            'map_plants': list(map_plants.values()),
            'cache_state': payload['cache_state'],
            'fetched_at': payload['fetched_at'],
        })
    except Exception:
        logger.exception('Plant locations API failed.')
        return JsonResponse({
            'success': False,
            'error': ENERGYMAP_LOAD_ERROR_MESSAGE,
        }, status=500)
