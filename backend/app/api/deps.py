from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Path, status, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core import get_async_session
from app.models import Department
from app.schemas import (DepartmentDetailParams,
                         DepartmentDeleteParams)
from .crud import get_department_by_id


SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
DepDetailParams = Annotated[DepartmentDetailParams, Depends()]
DepDeleteParams = Annotated[DepartmentDeleteParams, Depends()]


async def get_department_or_404(
    session: SessionDep,
    id: int = Path(..., ge=1, description="Идентификатор департамента"),
) -> Department | None:
    dep: Department | None = await get_department_by_id(
        id, session,
        include_employees=False,
        include_sub_deps=False
    )

    if dep is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не найден департамен с id: {id}"
        )

    return dep


async def get_department_with_relations_or_404(
    session: SessionDep,
    id: int = Path(..., ge=1, description="Идентификатор департамента")
) -> Department:
    stmt = (
        select(Department)
        .where(Department.id == id)
        .options(
            selectinload(Department.employees),
            selectinload(Department.sub_deps),
            selectinload(Department.parent),
        )
    )
    result = await session.execute(stmt)
    dep = result.scalar_one_or_none()
    if dep is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Департамент с id {id} не найден"
        )
    return dep

ExistingDepartmentFull = Annotated[Department, Depends(get_department_with_relations_or_404)]
ExistingDepartment = Annotated[Department, Depends(get_department_or_404)]
