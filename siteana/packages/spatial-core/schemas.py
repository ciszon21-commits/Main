from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Point(BaseModel):
    x: float
    y: float

class SiteBase(BaseModel):
    name: str
    description: Optional[str] = None
    geometry: Dict[str, Any]  # GeoJSON format

class ProjectBase(BaseModel):
    name: str
    client: Optional[str] = None
