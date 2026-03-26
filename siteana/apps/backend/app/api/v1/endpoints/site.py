from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.db.session import get_db
from app.services.site import SiteService
from app.schemas.site import Site, SiteCreate, SiteUpdate

router = APIRouter()

@router.post("/", response_model=Site)
def create_site(site_in: SiteCreate, db: Session = Depends(get_db)):
    return SiteService.create_site(db, site_in)

@router.get("/project/{project_id}", response_model=List[Site])
def read_project_sites(project_id: int, db: Session = Depends(get_db)):
    return SiteService.get_sites(db, project_id)

@router.get("/{site_id}", response_model=Site)
def read_site(site_id: int, db: Session = Depends(get_db)):
    site = SiteService.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site
