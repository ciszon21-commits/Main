from typing import List, Optional
from sqlmodel import Session, select
from app.models.base import Site
from app.schemas.site import SiteCreate, SiteUpdate

class SiteService:
    @staticmethod
    def create_site(db: Session, site_in: SiteCreate) -> Site:
        db_site = Site.from_orm(site_in)
        db.add(db_site)
        db.commit()
        db.refresh(db_site)
        return db_site

    @staticmethod
    def get_sites(db: Session, project_id: int) -> List[Site]:
        statement = select(Site).where(Site.project_id == project_id)
        return db.exec(statement).all()

    @staticmethod
    def get_site(db: Session, site_id: int) -> Optional[Site]:
        return db.get(Site, site_id)
