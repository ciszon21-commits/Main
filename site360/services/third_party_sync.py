import logging
import re
import requests
import uuid
from urllib.parse import urljoin
from django.core.files.base import ContentFile
from django.db import transaction, models

from site360.models import Project, Scene, Hotspot, HazardType
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ── 外部 API 設定 ─────────────────────────────────────────────────────────────
# 憑證存放於 cms_secrets.py（已列入 .gitignore，不進版本控制）。
# 首次部署時請複製 cms_secrets.example.py → cms_secrets.py 並填入實際值。
try:
    from site360.services.cms_secrets import (
        CMS_BASE_URL,
        CMS_API_TOKEN,
        CMS_USERNAME,
        CMS_PASSWORD,
    )
except ImportError:
    raise RuntimeError(
        "找不到 site360/services/cms_secrets.py！\n"
        "請複製 cms_secrets.example.py → cms_secrets.py 並填入正確的 CMS 憑證。"
    )
# ─────────────────────────────────────────────────────────────────────────────


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

    def _get_or_create_project(self) -> Project:
        """建立或取得 Project 實例，並更新經緯度與描述以符合外部資料"""
        project_code = self.data.get('project_code', '')
        tender_code = self.data.get('tender_code', '')
        tender_name = self.data.get('tender_name', '')
        
        # 組裝專案名稱: 預設格式 "6732D_第七標_機場捷運..."
        project_name = f"{project_code}_{tender_code}_{tender_name}"
        
        # 組裝描述
        workitem = self.data.get('workitem', '')
        first_worklayer = self.data.get('first_worklayer', '')
        doc_date = self.data.get('doc_date', '')
        form_uid = self.data.get('form_uid', '')
        
        description = (
            f"外部表單 UID: {form_uid}\n"
            f"文件日期: {doc_date}\n"
            f"工項: {workitem}\n"
            f"工作層: {first_worklayer}"
        )
        
        # 計算經緯度
        lat, lng = self._calculate_geo_bounds()
        
        # 使用 update_or_create 確保經緯度與描述會隨外部表單更新
        project, created = Project.objects.update_or_create(
            name=project_name,
            defaults={
                'description': description,
                'latitude': lat,
                'longitude': lng
            }
        )
        
        status = "建立" if created else "更新"
        logger.info(f"[CMS Sync] {status}專案：{project_name} (pk={project.pk}, lat={lat}, lng={lng})")
        return project

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
    def process(self) -> Project:
        """
        執行主要解析建立流程，回傳建立好的 Project 實例
        """
        # 1. 處理 Project
        project = self._get_or_create_project()
        
        # 2. 處理 Scene（每張照片建一個 Scene）
        photos = self.data.get('photos', [])
        workitem = self.data.get('workitem', '')
        first_worklayer = self.data.get('first_worklayer', '')
        scene_title_base = f"{workitem} - {first_worklayer}"
        
        created_scenes = []
        for idx, photo in enumerate(photos):
            if not photo.get('url') and not photo.get('uuid'):
                continue
                
            scene_title = f"{scene_title_base} ({idx+1})"
            image_content = self._download_image(photo)
            
            if not image_content:
                logger.warning(f"[CMS Sync] 跳過 Scene {scene_title}：圖片下載失敗")
                continue

            scene = Scene(
                project=project,
                title=scene_title,
                order=idx,
            )
            scene.image.save(image_content.name, image_content, save=False)
            scene.save()
            created_scenes.append(scene)
            logger.info(f"[CMS Sync] 建立 Scene：{scene_title} (pk={scene.pk})")
            
        # 3. 處理 Hotspot（設為「未分配專案」，不放入任何 Scene）
        # 對應規則：
        #   - survey_content → 熱點標題
        #   - hazard_status  → 描述的「危害狀態」（category 忽略，危害類別暫不設定）
        #   - safety_measure → 描述的「安全措施」
        assessments = self.data.get('assessments', [])
        form_uid    = self.data.get('form_uid', '')

        for item in assessments:
            hazard_status  = item.get('hazard_status', '')
            safety_measure = item.get('safety_measure', '')

            hotspot = Hotspot.objects.create(
                scene=None,              # 未分配到任何場景
                hotspot_type='text_hover',
                title=item.get('survey_content', '未命名危害'),
                description=f"**危害狀態**：\n{hazard_status}\n\n**安全措施**：\n{safety_measure}",
                pitch=0,
                yaw=0,
                external_form_uid=form_uid,
                # 危害類別（hazard_types）暫不設定，待後續整理規則後再對應
            )

            logger.info(f"[CMS Sync] 建立未分配 Hotspot：{hotspot.title} (form_uid={form_uid})")

        return project

