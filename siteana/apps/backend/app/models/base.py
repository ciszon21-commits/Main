from typing import Optional, List, Any
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    client: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    sites: List["Site"] = Relationship(back_populates="project")

class Site(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    
    # PostGIS Polygon geometry
    geometry: Any = Field(sa_column=Column(Geometry("POLYGON", srid=4326)))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Project = Relationship(back_populates="sites")
    snapshots: List["SiteLayerSnapshot"] = Relationship(back_populates="site")

class LayerSource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    layer_type: str  # roads, buildings, parks, etc.
    source_url: Optional[str] = None
    is_active: bool = True

class SiteLayerSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: int = Field(foreign_key="site.id")
    layer_source_id: int = Field(foreign_key="layersource.id")
    
    # Clipped geometry for this site
    geometry: Any = Field(sa_column=Column(Geometry("GEOMETRY", srid=4326)))
    
    site: Site = Relationship(back_populates="snapshots")
