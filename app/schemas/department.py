from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Any
from datetime import datetime
from app.schemas.employee import EmployeeResponse


class TrimNameMixin:
    @model_validator(mode='before')
    @classmethod
    def trim_name(values: dict[str, Any]):
        if isinstance(values, dict):
            if "name" in values:
                values["name"] = values["name"].strip()
        return values


class DepartmentBase(BaseModel):
    name: str = Field(...,
                      min_length=1,
                      max_length=200,
                      description="Имя департамента")
    parent_id: Optional[int] = Field(None,
                                     description="Департамент-родитель")


class DepartmentCreate(DepartmentBase, TrimNameMixin):
    pass


class DepartmentUpdate(DepartmentBase, TrimNameMixin):
    pass


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentDetailResponse(DepartmentResponse):
    employees: List[EmployeeResponse] = []
    children: List['DepartmentDetailResponse'] = []

    model_config = ConfigDict(from_attributes=True)


DepartmentDetailResponse.model_rebuild()
