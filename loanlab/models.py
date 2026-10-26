"""Database tables (SQLAlchemy 2.0, typed declarative style)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str | None] = mapped_column(String(20), unique=True)
    customer_name: Mapped[str] = mapped_column(String(100))
    product_code: Mapped[str] = mapped_column(String(10), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    annual_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    months: Mapped[int] = mapped_column(Integer)
    monthly_payment: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    outstanding: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(10), default="active", index=True)
    created_on: Mapped[date] = mapped_column(Date)

    repayments: Mapped[list[Repayment]] = relationship(
        back_populates="loan", order_by="Repayment.id", cascade="all, delete-orphan"
    )


class Repayment(Base):
    __tablename__ = "repayments"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid_on: Mapped[date] = mapped_column(Date)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    loan: Mapped[Loan] = relationship(back_populates="repayments")
