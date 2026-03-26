from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.db.session import get_db
from app.services.project import ProjectService
from app.schemas.project import Project, ProjectCreate, ProjectUpdate

router = APIRouter()

@router.post("/", response_model=Project)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    return ProjectService.create_project(db, project_in)

@router.get("/", response_model=List[Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ProjectService.get_projects(db, skip=skip, limit=limit)

@router.get("/{project_id}", response_model=Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
