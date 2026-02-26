from sqlalchemy import select, CTE, Integer, func
from sqlalchemy.orm import Query, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department
from app.schemas import DepartmentDetailResponse


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
