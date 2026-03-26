from pydantic import BaseModel
from typing import Optional

class ProjectBase(BaseModel):
    name: str
    client: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    name: Optional[str] = None

class Project(ProjectBase):
    id: int

    model_config = {
        "from_attributes": True
    }
