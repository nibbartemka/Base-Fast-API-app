from typing import Optional, List
from datetime import datetime
from enum import StrEnum

from pydantic import (BaseModel,
                      Field,
                      ConfigDict,
                      field_validator,
                      model_validator)

from app.schemas.employee import EmployeeResponse


class TrimNameMixin:
    @field_validator('name')
    @classmethod
    def trim_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class DeleteModes(StrEnum):
    CASCADE = "cascade"
    REASSIGN = "reassign"


class DepartmentBase(BaseModel):
    name: str = Field(...,
                      min_length=1,
                      max_length=200,
                      description="Имя департамента",
                      examples=["Back-End", "Front-End"])
    parent_id: Optional[int] = Field(None, examples=[1, 5],
                                     description="Департамент-родитель")


class DepartmentCreate(DepartmentBase, TrimNameMixin):
    pass


class DepartmentUpdate(BaseModel, TrimNameMixin):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Имя департамента",
        examples=["Back-End Team"]
    )
    parent_id: Optional[int] = Field(
        None,
        examples=[2,],
        description="Департамент-родитель"
    )


class DepartmentResponse(DepartmentBase):
    id: int = Field(..., examples=[1, 2])
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Back-End",
                "parent_id": None,
                "created_at": "2026-02-26T10:00:00"
            }
        }
    )


class DepartmentDetailResponse(DepartmentResponse):
    employees: List[EmployeeResponse] = Field(
        default_factory=list,
        description="Список сотрудников"
    )
    children: List['DepartmentDetailResponse'] = Field(
        default_factory=list,
        description="Подчиненные департаменты"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Engineering",
                "parent_id": None,
                "created_at": "2026-01-01T00:00:00",
                "employees": [
                    {
                        "id": 1,
                        "name": "Ivanov Ivan",
                        "position": "Senior Developer",
                        "hired_at": "2025-01-01"
                    }
                ],
                "children": [
                    {
                        "id": 2,
                        "name": "Back-End",
                        "parent_id": 1,
                        "created_at": "2026-01-02T00:00:00",
                        "employees": [],
                        "children": []
                    }
                ]
            }
        }
    )


class DepartmentDeleteParams(BaseModel):
    mode: DeleteModes = Field(
        default=...,
        description="Тип удаления",
        examples=["cascade", "reassign"],
    )
    reassign_to_deparment_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="Id департамента, к которому будут переназначен персонал",
        examples=[None, 1, 2],
    )

    @model_validator(mode='after')
    def validate_dep_id_based_on_mode(self) -> 'DepartmentDeleteParams':
        if (self.mode == DeleteModes.REASSIGN
           and self.reassign_to_deparment_id is None):
            raise ValueError("При mode=reassign необходимо "
                             "указать reassign_to_deparment_id")
        if (self.mode == DeleteModes.CASCADE
           and self.reassign_to_deparment_id):
            raise ValueError("При mode=cascade нельзя указывать "
                             "reassign_to_deparment_id отличное от None")

        return self


class DepartmentDetailParams(BaseModel):
    depth: int = Field(
        1,
        ge=1,
        le=5,
        description="Глубина вывода дерева",
        examples=[1, 2, 3, 4, 5]
    )
    include_employees: bool = Field(
        True,
        description="Включать ли сотрудников",
        examples=[True, False]
    )


DepartmentDetailResponse.model_rebuild()
