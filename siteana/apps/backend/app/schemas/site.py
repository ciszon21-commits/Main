from pydantic import BaseModel
from typing import Optional, Dict, Any

class SiteBase(BaseModel):
    name: str
    geometry: Dict[str, Any]  # GeoJSON format

class SiteCreate(SiteBase):
    project_id: int

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None

class Site(SiteBase):
    id: int
    project_id: int

    model_config = {
        "from_attributes": True
    }
