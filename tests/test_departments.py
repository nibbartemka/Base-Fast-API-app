import pytest
from datetime import date

from sqlalchemy import select
from httpx import AsyncClient

from app.models import Department, Employee


@pytest.mark.asyncio
async def test_create_department_without_parent(
    client: AsyncClient,
    test_session
):
    payload = {"name": "IT департамент"}
    response = await client.post("/departments/", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "IT департамент"
    assert "id" in data
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_create_department_with_parent(client: AsyncClient, test_session):
    parent = Department(name="Parent")

    test_session.add(parent)

    await test_session.commit()
    await test_session.refresh(parent)

    payload = {"name": "Child", "parent_id": parent.id}
    response = await client.post("/departments/", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["parent_id"] == parent.id
    assert data["name"] == "Child"


@pytest.mark.asyncio
async def test_create_department_invalid_parent(client: AsyncClient):
    payload = {"name": "Child", "parent_id": 9999999999999}

    response = await client.post("/departments/", json=payload)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_employee(client: AsyncClient, test_session):
    dep = Department(name="HR")

    test_session.add(dep)

    await test_session.commit()
    await test_session.refresh(dep)

    payload = {
        "name": "Ivanov Ivan",
        "position": "Manager",
        "hired_at": "2024-01-01",
    }

    response = await client.post(f"/departments/{dep.id}/employees",
                                 json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Ivanov Ivan"
    assert data["department_id"] == dep.id


@pytest.mark.asyncio
async def test_create_employee_for_invalid_department(
    client: AsyncClient,
    test_session
):
    payload = {
        "name": "Ivanov Ivan",
        "position": "Manager",
        "hired_at": "2024-01-01"
    }

    response = await client.post("/departments/999999999/employees",
                                 json=payload)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_department(client: AsyncClient, test_session):
    dep = Department(name="Sales")
    test_session.add(dep)

    await test_session.commit()
    await test_session.refresh(dep)

    response = await client.get(f"/departments/{dep.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sales"
    assert data["id"] == dep.id


@pytest.mark.asyncio
async def test_get_department_404(client: AsyncClient):
    response = await client.get("/departments/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_department_with_details(client: AsyncClient, test_session):
    parent_dep = Department(name="IT")
    child_dep = Department(name="Python", parent=parent_dep)

    parent_emp = Employee(
        name="Dev1",
        department=parent_dep,
        position="Coder",
        hired_at=date(2024, 1, 1)
    )
    child_emp = Employee(
        name="Dev2",
        department=child_dep,
        position="Coder",
        hired_at=date(2024, 1, 1)
    )

    test_session.add_all([
        parent_dep,
        child_dep,
        parent_emp,
        child_emp
    ])

    await test_session.commit()
    await test_session.refresh(parent_dep)
    await test_session.refresh(child_dep)

    response = await client.get(f"/departments/{parent_dep.id}?depth=2&include_employees=true")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == parent_dep.id
    assert data["parent_id"] is None

    print(data)
    assert parent_emp.id == data["employees"][0]["id"]
    assert child_dep.id == data["children"][0]["id"]
    assert child_emp.id == data["children"][0]["employees"][0]["id"]


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, test_session):
    dep = Department(name="Old Name")
    test_session.add(dep)
    await test_session.commit()

    payload = {"name": "New Name"}
    response = await client.patch(f"/departments/{dep.id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"


@pytest.mark.asyncio
async def test_update_department_cycle_detection(
    client: AsyncClient,
    test_session
):
    parent = Department(name="Parent")
    child = Department(name="Child", parent=parent)
    test_session.add_all([parent, child])
    await test_session.commit()
    await test_session.refresh(child)

    payload = {"parent_id": child.id}
    response = await client.patch(f"/departments/{parent.id}", json=payload)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_department_cascade(client: AsyncClient, test_session):
    parent_dep = Department(name="IT")
    child_dep = Department(name="Python", parent=parent_dep)

    test_session.add_all([parent_dep, child_dep])

    await test_session.commit()
    await test_session.refresh(parent_dep)

    response = await client.delete(f"/departments/{parent_dep.id}",
                                   params={"mode": "cascade"})

    assert response.status_code == 204

    result = await test_session.execute(
        select(Department)
        .where(Department.id == parent_dep.id)
    )

    assert result.scalar_one_or_none() is None

    result = await test_session.execute(
        select(Department)
        .where(Department.id == child_dep.id)
    )

    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_department_reassign(client: AsyncClient, test_session):
    target = Department(name="Target")
    source = Department(name="Source")

    emp = Employee(
        name="Emp",
        department=source,
        position="Dev",
        hired_at=date(2024, 1, 1),
    )

    test_session.add_all([target, source, emp])

    await test_session.commit()
    await test_session.refresh(source)
    await test_session.refresh(emp)

    response = await client.delete(
        f"/departments/{source.id}",
        params={"mode": "reassign", "reassign_to_deparment_id": target.id}
    )

    assert response.status_code == 204

    await test_session.refresh(emp)
    assert emp.department_id == target.id
