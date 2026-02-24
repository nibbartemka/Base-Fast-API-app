from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class EmployeeBase(BaseModel):
    full_name: str = Field(...,
                           min_length=1,
                           max_length=200,
                           description="Полное имя сотрудника")
    position: str = Field(...,
                          min_length=1,
                          max_length=200,
                          description="Должность сотружника")
    hired_at: Optional[date] = Field(None, description="Hire date")


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    id: int
    department_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
