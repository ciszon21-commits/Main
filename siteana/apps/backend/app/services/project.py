from typing import List, Optional
from sqlmodel import Session, select
from app.models.base import Project, Site
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    @staticmethod
    def create_project(db: Session, project_in: ProjectCreate) -> Project:
        db_project = Project.from_orm(project_in)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        statement = select(Project).offset(skip).limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        return db.get(Project, project_id)
