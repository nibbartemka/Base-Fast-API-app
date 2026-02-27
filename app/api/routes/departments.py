from typing import Any

from fastapi import (APIRouter,
                     status,
                     HTTPException,
                     Body)
from app.schemas import (DepartmentResponse,
                         DepartmentCreate,
                         DepartmentUpdate,
                         DepartmentDetailResponse,
                         EmployeeCreate,
                         EmployeeResponse,
                         DeleteModes)
from app.models import Department, Employee
from app.api.deps import (ExistingDepartment,
                          DepDetailParams,
                          DepDeleteParams,
                          ExistingDepartmentFull,
                          SessionDep)
from app.api.crud import (check_cycle, get_department_by_id,
                          get_detailed_department,
                          delete_department_cascade,
                          delete_department_reassign)


router: APIRouter = APIRouter(prefix="/departments",
                              tags=["departments"])


@router.post("/", status_code=status.HTTP_201_CREATED,
             response_model=DepartmentResponse)
async def create_department(
    session: SessionDep,
    department: DepartmentCreate = Body(
        description="Данные для создания департамента",
        examples=[{
            "name": "Back-End",
            "parent_id": 1
        }]
    )
) -> DepartmentResponse:
    if department.parent_id:
        parent = await get_department_by_id(
            department.parent_id,
            session,
        )

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Департамент-родитель с id {department.parent_id} не найден"
            )

    new_department: Department = Department(**department.model_dump())

    session.add(new_department)
    await session.commit()
    await session.refresh(new_department)

    return new_department


@router.post("/{id}/employees",
             status_code=status.HTTP_201_CREATED,
             response_model=EmployeeResponse)
async def create_employee_for_department(
    session: SessionDep,
    existing_department: ExistingDepartment,
    employee: EmployeeCreate = Body(
        description="Данные сотрудника",
        examples=[{
            "name": "Ivanov Ivan Ivanovich",
            "position": "Developer of smth",
            "hired_at": "2026-01-01"
        }]
    ),
) -> EmployeeResponse:
    employee: Employee = Employee(
        **employee.model_dump(),
        department_id=existing_department.id
    )

    session.add(employee)
    await session.commit()
    await session.refresh(employee)

    return employee


@router.get("/{id}",
            status_code=status.HTTP_200_OK,
            response_model=DepartmentDetailResponse)
async def get_department(
    session: SessionDep,
    existing_department: ExistingDepartment,
    detail_params: DepDetailParams
) -> DepartmentDetailResponse:
    result = await get_detailed_department(
        existing_department.id,
        session,
        detail_params.depth,
        detail_params.include_employees
    )

    return result


@router.patch("/{id}",
              status_code=status.HTTP_200_OK,
              response_model=DepartmentResponse)
async def update_department(
    session: SessionDep,
    existing_department: ExistingDepartment,
    update_body: DepartmentUpdate = Body(
        description="Данные для обновления департамента",
        examples=[{
            "name": "John Doe Dep",
            "parent_id": 1
        }]
    )
) -> DepartmentResponse:
    if update_body.parent_id:
        parent_department = await get_department_by_id(
            update_body.parent_id,
            session,
        )

        if parent_department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Департамент-родитель с id {update_body.parent_id} не найден"
            )

        if await check_cycle(existing_department.id,
                             update_body.parent_id, session):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Невозможно обновить: цикл в иерархии"
            )

    update_dict: dict[str, Any] = update_body.model_dump(exclude_unset=True)

    for key, value in update_dict.items():
        setattr(existing_department, key, value)

    try:
        await session.commit()
        await session.refresh(existing_department)
        return existing_department
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении"
        ) from e


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    existing_department: ExistingDepartmentFull,
    delete_params: DepDeleteParams,
    session: SessionDep,
) -> None:
    if delete_params.mode == DeleteModes.CASCADE:
        await delete_department_cascade(existing_department,
                                        session)
    elif delete_params.mode == DeleteModes.REASSIGN:
        target_dep_id = delete_params.reassign_to_deparment_id
        target_dep = await get_department_by_id(target_dep_id, session)
        await delete_department_reassign(target_dep,
                                         existing_department,
                                         session)
