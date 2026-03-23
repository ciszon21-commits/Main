import logging
import os
import re
import requests
import uuid
from urllib.parse import urljoin
from django.core.files.base import ContentFile
from django.db import transaction, models

from site360.models import Project, Scene, Hotspot, HazardType
from typing import Dict, Any

logger = logging.getLogger(__name__)


from django.core.exceptions import ImproperlyConfigured

# ── 外部 API 設定 ─────────────────────────────────────────────────────────────
# 憑證由 CoDevStudio/settings_local/_local_settings.py 統一管理。
# 請在 _local_settings.py（參考 _local_settings.example.py）中填入實際的 CMS 憑證。
from django.conf import settings as _django_settings

CMS_BASE_URL  = _django_settings.CMS_BASE_URL
CMS_API_TOKEN = _django_settings.CMS_API_TOKEN
CMS_USERNAME  = _django_settings.CMS_USERNAME
CMS_PASSWORD  = _django_settings.CMS_PASSWORD

# if not CMS_BASE_URL or not CMS_API_TOKEN:
#     raise ImproperlyConfigured(
#         "CMS_BASE_URL 與 CMS_API_TOKEN 未設定。\n"
#         "請在 CoDevStudio/settings_local/_local_settings.py 中加入正確的 CMS 憑證，\n"
#         "可參考 _local_settings.example.py 的範本。"
#     )
# # ─────────────────────────────────────────────────────────────────────────────


def _parse_cookies(set_cookie_raw: str) -> str:
    """
    將 Set-Cookie Header 原始字串解析成 Cookie Header 字串。
    例：「sessionid=abc; Path=/」→「sessionid=abc」
    """
    if not set_cookie_raw:
        return ""
    parts = re.split(r",(?=[^;]+=)", set_cookie_raw)
    pairs = []
    for part in parts:
        first = part.split(";")[0].strip()
        if "=" in first:
            pairs.append(first)
    return "; ".join(pairs)


def cms_api_get(url: str) -> tuple[requests.Response, str]:
    """
    兩段式 Middleware 自動登入，向 CMS 平台發起 GET 請求。

    Step 1：帶 X-Platform-Username/Password Header，觸發 Middleware 登入 → 302 + Session Cookie
    Step 2：帶 Session Cookie 重新請求 → 取得實際資料（200）

    :param url: 完整的 CMS API URL
    :return: (Response 物件, cookie_header 字串)
             — cookie_header 可供後續請求（如圖片下載）重用
    :raises requests.HTTPError: HTTP 層級錯誤
    """
    step1_headers = {
        "Authorization": f"Token {CMS_API_TOKEN}",
        "Accept": "application/json",
        "X-Platform-Username": CMS_USERNAME,
        "X-Platform-Password": CMS_PASSWORD,
    }

    # Step 1：觸發 Middleware，不跟隨 Redirect
    resp1 = requests.get(url, headers=step1_headers, allow_redirects=False, timeout=15)
    logger.info(f"[CMS API] Step1 {url} → {resp1.status_code}")

    if resp1.status_code not in (301, 302):
        # 有些環境可能直接回 200（已有 session），直接使用
        logger.warning(f"[CMS API] 預期 302，但收到 {resp1.status_code}，嘗試直接使用此回應")
        resp1.raise_for_status()
        return resp1, ""

    location = resp1.headers.get("location", "")
    cookie_header = _parse_cookies(resp1.headers.get("set-cookie", ""))
    redirect_url = f"{CMS_BASE_URL}{location}" if location.startswith("/") else location

    # Step 2：帶 Cookie 取得實際資料
    step2_headers = {
        "Authorization": f"Token {CMS_API_TOKEN}",
        "Accept": "application/json",
        "Cookie": cookie_header,
    }
    resp2 = requests.get(redirect_url, headers=step2_headers, allow_redirects=False, timeout=15)
    logger.info(f"[CMS API] Step2 {redirect_url} → {resp2.status_code}")
    resp2.raise_for_status()
    return resp2, cookie_header


def cms_download_file(url: str, cookie_header: str) -> requests.Response:
    """
    使用已取得的 Session Cookie 下載 CMS 媒體檔案（圖片等），
    不需要重新走一次兩段式登入。

    :param url: 完整的媒體檔案 URL
    :param cookie_header: 由 cms_api_get 取得的 Session Cookie 字串
    :return: Response 物件
    """
    headers = {
        "Authorization": f"Token {CMS_API_TOKEN}",
        "Cookie": cookie_header,
    }
    resp = requests.get(url, headers=headers, timeout=30)
    logger.info(f"[CMS Download] {url} → {resp.status_code}, Content-Type: {resp.headers.get('content-type', '')}")
    resp.raise_for_status()
    return resp


class SinoTechAPIParser:
    """
    負責將外部平台 (Sinotech CMS) 傳送的 JSON 資料
    解析並轉換為我們系統內的 Project, Scene, Hotspot 實例
    """

    def __init__(self, data: Dict[str, Any], base_url: str = CMS_BASE_URL, session_cookie: str = ""):
        """
        初始化解析器
        :param data: JSON 內的 'data' 物件
        :param base_url: 外部平台的 Base URL（用於組裝圖片完整 URL）
        :param session_cookie: 由 cms_api_get 取得的 Session Cookie，供圖片下載重用
        """
        self.data = data
        self.base_url = base_url
        self.session_cookie = session_cookie
        
    def _calculate_geo_bounds(self) -> tuple[float, float]:
        """
        根據 geo_bounds 的 type 算出代表性的經緯度 (lat, lng)
        """
        geo = self.data.get('geo_bounds', {})
        geo_type = geo.get('type')
        
        if not geo_type:
            return None, None
            
        try:
            if geo_type == "單點":
                return float(geo.get('lat', 0)), float(geo.get('lng', 0))
                
            elif geo_type == "圓形":
                center = geo.get('center', [0, 0])
                if len(center) >= 2:
                    return float(center[0]), float(center[1])
                    
            elif geo_type == "方形":
                north = float(geo.get('north', 0))
                south = float(geo.get('south', 0))
                east = float(geo.get('east', 0))
                west = float(geo.get('west', 0))
                return (north + south) / 2, (east + west) / 2
                
            elif geo_type == "多邊形":
                points = geo.get('points', [])
                if not points:
                    return None, None
                lat_sum = sum(p[0] for p in points)
                lng_sum = sum(p[1] for p in points)
                return lat_sum / len(points), lng_sum / len(points)
                
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing geo_bounds: {e}, data: {geo}")
            
        return None, None

    def _reverse_geocode(self, lat: float, lng: float) -> tuple[str, str]:
        """
        使用 Nominatim API 根據經緯度推估縣市與區域名稱。
        """
        if not lat or not lng:
            return "", ""
            
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "json",
            "lat": lat,
            "lon": lng,
            "zoom": 18,  # 提高縮放層級以取得區域 (district)
            "addressdetails": 1,
            "accept-language": "zh-TW"
        }
        headers = {
            "User-Agent": "Site360-SinoTech-Sync-Agent"
        }
        
        try:
            logger.info(f"[Geocode] 請求逆向地理編碼：({lat}, {lng})")
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            address = data.get("address", {})
            
            # 臺灣地址的縣市名稱可能出現在不同欄位
            city = address.get("city") or address.get("state") or address.get("county")
            # 臺灣區域名稱通常在 town (例如：龜山區)，其次才是 suburb, district, 或 city_district
            district = address.get("town") or address.get("suburb") or address.get("district") or address.get("city_district")
            
            if city or district:
                logger.info(f"[Geocode] 辨識結果：縣市={city}, 區域={district}")
                return city or "", district or ""
                
        except Exception as e:
            logger.warning(f"[Geocode] 逆向地理編碼失敗：{e}")
            
        return "", ""

    def _get_or_create_project(self) -> Project:
        """建立或取得 Project 實例，並更新經緯度與描述以符合外部資料"""
        project_code = self.data.get('project_code', '')
        tender_code = self.data.get('tender_code', '')
        tender_name = self.data.get('tender_name', '')
        workitem = self.data.get('workitem', '')
        first_worklayer = self.data.get('first_worklayer', '')
        
        # 組裝專案名稱: 採用使用者要求格式 "{{workitem}}_{{first_worklayer}}"
        project_name = f"{workitem}_{first_worklayer}"
        
        # 組裝描述 (使用者需求：改為固定字串 "自動建立")
        description = "自動建立"
        
        # 取得表單日期
        doc_date = self.data.get('doc_date')

        # 取得經緯度與地址資訊 (用於標記位置與逆向地理編碼)
        geo_bounds = self.data.get('geo_bounds', {})
        lat = geo_bounds.get('lat')
        lng = geo_bounds.get('lng')
        
        city = ""
        district = ""

        if lat and lng:
            # 取得縣市與區域資訊 (優化為一次調用)
            city, district = self._reverse_geocode(lat, lng)

        # 4. 建立或更新 Project
        project, created = Project.objects.update_or_create(
            name=project_name,
            defaults={
                'description': description,
                'project_code': project_code,
                'tender_code': tender_code,
                'tender_name': tender_name,
                'doc_date': doc_date,
                'form_uid': self.data.get('form_uid'),
                'latitude': lat,
                'longitude': lng,
                'city': city,
                'district': district
            }
        )
        
        status = "建立" if created else "更新"
        logger.info(f"[CMS Sync] {status}專案：{project_name} (pk={project.pk}, lat={lat}, lng={lng})")
        return project, created

    def _create_hazard_types(self, assessments: list) -> dict:
        """
        確保所需的 HazardType 存在，回傳 category 與 HazardType 的 mapping
        """
        mapping = {}
        for item in assessments:
            category = item.get('category')
            if not category or category in mapping:
                continue
                
            hazard_type = HazardType.objects.filter(name=category).first()
            if not hazard_type:
                max_serial = HazardType.objects.aggregate(
                    models.Max('serial_number')
                )['serial_number__max'] or 0
                
                hazard_type = HazardType.objects.create(
                    serial_number=max_serial + 1,
                    name=category,
                    description=f"自動自外部系統同步新增的危害類別 ({category})"
                )
                logger.info(f"[CMS Sync] 自動建立 HazardType：{category}")

            mapping[category] = hazard_type
        return mapping

    def _download_image(self, photo: dict) -> ContentFile | None:
        """
        使用 /auth/file/{uuid}/ 格式下載圖片（只需 Token，不需 Session Cookie）。

        :param photo: photos[] 陣列中的單一 photo 物件（需含 uuid 和 name）
        """
        file_uuid = photo.get('uuid', '')
        filename   = photo.get('name') or f"{uuid.uuid4().hex}.jpg"

        if not file_uuid:
            logger.error("[CMS Sync] photo 物件缺少 uuid，無法下載圖片")
            return None

        download_url = f"{self.base_url}/auth/file/{file_uuid}/"
        logger.info(f"[CMS Sync] 下載圖片：{download_url}")

        try:
            headers = {"Authorization": f"Token {CMS_API_TOKEN}"}
            response = requests.get(download_url, headers=headers, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "image/" not in content_type:
                logger.error(
                    f"[CMS Sync] 非預期的 Content-Type：{content_type}（URL: {download_url}）"
                )
                return None

            logger.info(f"[CMS Sync] 圖片下載成功：{filename}，{len(response.content)} bytes")
            return ContentFile(response.content, name=filename)

        except Exception as e:
            logger.error(f"[CMS Sync] 圖片下載失敗 {download_url}: {e}")
            return None

    @transaction.atomic
    def process(self) -> dict:
        """
        執行主要解析建立流程，回傳包含 Project 及建立統計後的結果字典
        """
        # 1. 處理 Project
        project, project_created = self._get_or_create_project()
        
        # 2. 處理 Scene（每張照片建一個 Scene）
        photos = self.data.get('photos', [])
        
        # 取得現有的 Scene external_ids，避免重複建立
        existing_external_ids = set(project.scenes.values_list('external_id', flat=True))
        
        # 取得目前最大的排序值，用於累加
        max_order = project.scenes.aggregate(models.Max('order'))['order__max']
        next_order = (max_order or 0) + 1 if max_order is not None else 0

        created_scenes = []
        for idx, photo in enumerate(photos):
            photo_uuid = photo.get('uuid')
            
            # 使用者需求：偵測到已建立過的 360 圖片 (UID可比對)，就不動他 (不更新)
            if photo_uuid and photo_uuid in existing_external_ids:
                logger.info(f"[CMS Sync] 跳過 Scene (UUID={photo_uuid})：已存在於專案中")
                continue

            if not photo.get('url') and not photo_uuid:
                continue
                
            # 使用者需求：使用 photos 內的 name 來命名，並去掉副檔名
            photo_name = photo.get('name', '')
            if photo_name:
                scene_title = os.path.splitext(photo_name)[0]
            else:
                scene_title = f"未命名場景 ({idx+1})"
            image_content = self._download_image(photo)
            
            if not image_content:
                logger.warning(f"[CMS Sync] 跳過 Scene {scene_title}：圖片下載失敗")
                continue

            scene = Scene(
                project=project,
                title=scene_title,
                order=next_order,
                external_id=photo_uuid,
            )
            scene.image.save(image_content.name, image_content, save=False)
            scene.save()

            # 使用者需求：若專案尚未有封面圖，則將第一張成功匯入的照片設為封面
            if not project.cover_image:
                # 重新利用 image_content 以免重複下載
                project.cover_image.save(image_content.name, image_content, save=True)
                logger.info(f"[CMS Sync] 設定專案預設封面：{scene_title} (pk={project.pk})")

            created_scenes.append(scene)
            next_order += 1
            logger.info(f"[CMS Sync] 建立 Scene：{scene_title} (pk={scene.pk}, external_id={photo_uuid})")
            
        # 3. 處理 Hotspot（設為「未分配專案」，不放入任何 Scene）
        assessments = self.data.get('assessments', [])
        form_uid    = self.data.get('form_uid', '')
        hotspots_added_count = 0

        for item in assessments:
            title = item.get('survey_content', '未命名危害')
            hazard_status  = item.get('hazard_status', '')
            safety_measure = item.get('safety_measure', '')
            description = f"**危害狀態**：\n{hazard_status}\n\n**安全措施**：\n{safety_measure}"
            
            # 使用者需求：比對標題與內容，相同建立過且 form_id 都一樣的就不再新增
            duplicate_hotspot = Hotspot.objects.filter(
                title=title,
                description=description,
                external_form_uid=form_uid
            ).exists()
            
            if duplicate_hotspot:
                logger.info(f"[CMS Sync] 跳過 Hotspot (Title={title})：內容與 form_uid 已存在")
                continue

            hotspot = Hotspot.objects.create(
                scene=None,              # 未分配到任何場景
                project=project,         # 分配至專案 (外部匯入字卡概念)
                hotspot_type='text_hover',
                title=title,
                description=description,
                pitch=0,
                yaw=0,
                external_form_uid=form_uid,
            )
            hotspots_added_count += 1
            logger.info(f"[CMS Sync] 建立未分配 Hotspot：{hotspot.title} (form_uid={form_uid})")

        return {
            'project': project,
            'project_created': project_created,
            'scenes_added': len(created_scenes),
            'hotspots_added': hotspots_added_count
        }
