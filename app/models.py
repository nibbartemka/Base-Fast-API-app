from datetime import datetime, date

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from .core import Base


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("parent_id", "name", name="uq_department_parent_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    parent: Mapped["Department | None"] = relationship(
        "Department",
        remote_side=[id],
        back_populates="sub_deps",
        lazy="selectin",
    )

    sub_deps: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="selectin",
    )

    employees = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Employee(Base):
    __tablename__ = 'staff'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[str] = mapped_column(nullable=False)
    hired_at: Mapped[date | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    department = relationship(
        "Department",
        back_populates="employees",
    )
