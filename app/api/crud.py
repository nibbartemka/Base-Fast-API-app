from sqlalchemy import select, CTE, Integer, func, update, delete
from sqlalchemy.orm import Query, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department, Employee
from app.schemas import DepartmentDetailResponse, DeleteModes


async def get_department_by_id(
    id: int,
    session: AsyncSession,
    include_employees: bool = False,
    include_sub_deps: bool = False
) -> Department | None:
    options = []

    if include_employees:
        options.append(selectinload(Department.employees))
    if include_sub_deps:
        options.append(selectinload(Department.sub_deps))

    query = (
        select(Department)
        .where(Department.id == id)
        .options(*options)
    )

    result = await session.execute(query)

    dep: Department = result.scalar_one_or_none()

    return dep


async def get_department_tree(
    id: int,
    session: AsyncSession,
    include_employees: bool = True,
    depth: int | None = None,
) -> list[Department]:
    cte: CTE = (
        select(
            Department.id,
            Department.name,
            Department.parent_id,
            func.cast(0, Integer).label('level')
        )
        .where(Department.id == id)
        .cte(name='dept_tree', recursive=True)
    )

    cte_alias = cte.alias()

    children: Query = (
        select(
            Department.id,
            Department.name,
            Department.parent_id,
            (cte_alias.c.level + 1).label('level')
        )
        .join(cte_alias, Department.parent_id == cte_alias.c.id)
    )

    if depth:
        children = children.where(cte_alias.c.level < depth)

    cte = cte.union_all(children)

    tree_query: Query = (
        select(Department)
        .join(cte, Department.id == cte.c.id)
        .order_by(cte.c.level)
    )

    if include_employees:
        tree_query = tree_query.options(selectinload(Department.employees))

    result = await session.execute(tree_query)

    return list(result.scalars().all())


def build_department_tree(
    deps: list[Department],
    root_id: int
) -> DepartmentDetailResponse:
    dep_map: dict[int, Department] = {
        d.id: DepartmentDetailResponse.model_validate(d)
        for d in deps
    }

    for dep in dep_map.values():
        dep.children = []

    root: Department | None = None

    for dep in dep_map.values():
        if dep.parent_id and dep.parent_id in dep_map:
            dep_map[dep.parent_id].children.append(dep)
        elif dep.id == root_id:
            root = dep

    if root is None:
        raise ValueError(f"Корневой департамент с id={root_id} отсутствует в переданных данных")

    return root


async def get_detailed_department(
    id: int,
    session: AsyncSession,
    depth: int,
    include_employees: bool = False,
) -> DepartmentDetailResponse:
    deps = await get_department_tree(
        id=id,
        session=session,
        include_employees=include_employees,
        depth=depth
    )

    return build_department_tree(deps, id)


async def check_cycle(
    department_id: int,
    new_parent_id: int,
    session: AsyncSession
) -> bool:
    current_id = new_parent_id
    current = await get_department_by_id(new_parent_id, session)

    while current_id:
        if current_id == department_id:
            return True

        parent = current.parent

        if parent is None:
            break

        current_id = parent.parent_id

    return False


async def delete_department_cascade(
    existing_department: Department,
    session: AsyncSession
) -> None:
    await session.delete(existing_department)
    await session.commit()


# async def delete_department_reassign(
#     target_department: Department | None,
#     existing_department: Department,
#     session: AsyncSession
# ) -> None:
#     if target_department and target_department.id == existing_department.id:
#         raise ValueError("Невозможно переместить в тот же самый департамент")

#     sub_deps_to_reassign = (dep for dep in existing_department.sub_deps)
#     employees_to_reassign = (emp for emp in existing_department.employees)

#     parent = existing_department.parent

#     for employee in employees_to_reassign:
#         employee.department = target_department

#     for sub_dep in sub_deps_to_reassign:
#         sub_dep.parent = parent

#     await session.flush()

#     await session.delete(existing_department)
#     await session.commit()

async def delete_department_reassign(
    target_department: Department | None,
    existing_department: Department,
    session: AsyncSession
) -> None:
    if target_department and target_department.id == existing_department.id:
        raise ValueError("Невозможно переместить в тот же самый департамент")

    sub_dep_ids = (sub_dep.id for sub_dep in existing_department.sub_deps)
    employee_ids = (emp.id for emp in existing_department.employees)

    if sub_dep_ids:
        new_parent_id = existing_department.parent.id if existing_department.parent else None

        await session.execute(
            update(Department)
            .where(Department.id.in_(sub_dep_ids))
            .values(parent_id=new_parent_id)
        )

    if employee_ids and target_department:
        await session.execute(
            update(Employee)
            .where(Employee.id.in_(employee_ids))
            .values(department_id=target_department.id)
        )

    await session.flush()

    await session.execute(
        delete(Department)
        .where(Department.id == existing_department.id)
    )
    await session.commit()
