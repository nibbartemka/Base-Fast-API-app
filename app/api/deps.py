from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Path, status, HTTPException

from app.core import get_async_session
from app.models import Department
from app.schemas import DepartmentDetailParams
from .crud import get_department_by_id


SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
DepDetailParams = Annotated[DepartmentDetailParams, Depends()]


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


ExistingDepartment = Annotated[Department, Depends(get_department_or_404)]
