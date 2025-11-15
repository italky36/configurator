"""SQLAlchemy models for CoffeeZone Configurator."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class TimestampMixin:
    """Shared timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CatalogBase(Base):
    """Base class for catalog entities that have price & specs fields."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specs: Mapped[str | None] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    main_image_url: Mapped[str | None] = mapped_column(String(500))
    gallery_image_urls: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __str__(self) -> str:  # pragma: no cover
        return self.name or f"{self.__class__.__name__} #{self.id}"


class CoffeeMachine(CatalogBase):
    __tablename__ = "coffee_machines"

    short_title: Mapped[str | None] = mapped_column(String(120))


class Fridge(CatalogBase):
    __tablename__ = "fridges"


class Carcass(CatalogBase):
    __tablename__ = "carcasses"

    design_combinations: Mapped[List["CarcassDesignCombination"]] = relationship(
        "CarcassDesignCombination",
        back_populates="carcass",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Terminal(CatalogBase):
    __tablename__ = "terminals"


class ColorBase(Base):
    """Base class for carcass/design color entities."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_delta: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    main_image_url: Mapped[str | None] = mapped_column(String(500))
    gallery_image_urls: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __str__(self) -> str:  # pragma: no cover
        return self.name or f"{self.__class__.__name__} #{self.id}"


class CarcassColor(ColorBase):
    __tablename__ = "carcass_colors"


class DesignColor(ColorBase):
    __tablename__ = "design_colors"


class CarcassDesignCombination(TimestampMixin, Base):
    __tablename__ = "carcass_design_combinations"
    __table_args__ = (
        UniqueConstraint(
            "carcass_id", "carcass_color_id", "design_color_id", name="uq_carcass_design_combo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    carcass_id: Mapped[int] = mapped_column(ForeignKey("carcasses.id"), nullable=False)
    carcass_color_id: Mapped[int] = mapped_column(ForeignKey("carcass_colors.id"), nullable=False)
    design_color_id: Mapped[int] = mapped_column(ForeignKey("design_colors.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    main_image_url: Mapped[str | None] = mapped_column(String(500))
    gallery_image_urls: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    carcass: Mapped["Carcass"] = relationship(
        "Carcass", back_populates="design_combinations", lazy="joined"
    )
    carcass_color: Mapped["CarcassColor"] = relationship("CarcassColor", lazy="joined")
    design_color: Mapped["DesignColor"] = relationship("DesignColor", lazy="joined")

    @property
    def gallery_urls(self) -> List[str]:
        raw = self.gallery_image_urls or "[]"
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return []
        else:
            data = raw
        if isinstance(data, list):
            return [str(item) for item in data if isinstance(item, str) and item]
        return []

    def __str__(self) -> str:  # pragma: no cover
        carcass_name = self.carcass.name if self.carcass else ""
        color_name = self.carcass_color.name if self.carcass_color else " "
        design_name = self.design_color.name if self.design_color else " "
        return f"{carcass_name}: {color_name} + {design_name}"


class Bundle(TimestampMixin, Base):
    __tablename__ = "bundles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    coffee_machine_id: Mapped[int] = mapped_column(ForeignKey("coffee_machines.id"), nullable=False)
    fridge_id: Mapped[int | None] = mapped_column(
        ForeignKey("fridges.id"), nullable=True, default=None
    )
    carcass_id: Mapped[int] = mapped_column(ForeignKey("carcasses.id"), nullable=False)
    carcass_color_id: Mapped[int] = mapped_column(ForeignKey("carcass_colors.id"), nullable=False)
    design_color_id: Mapped[int] = mapped_column(ForeignKey("design_colors.id"), nullable=False)
    terminal_id: Mapped[int | None] = mapped_column(
        ForeignKey("terminals.id"), nullable=True, default=None
    )
    carcass_design_combination_id: Mapped[int | None] = mapped_column(
        ForeignKey("carcass_design_combinations.id"), nullable=True
    )
    custom_price: Mapped[int | None] = mapped_column(Integer)
    ozon_url: Mapped[str | None] = mapped_column(String(500))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_on_site: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    carcass_design_combination: Mapped["CarcassDesignCombination"] = relationship(
        "CarcassDesignCombination", lazy="joined"
    )
    coffee_machine: Mapped["CoffeeMachine"] = relationship("CoffeeMachine", lazy="joined")
    fridge: Mapped["Fridge"] = relationship("Fridge", lazy="joined")
    carcass: Mapped["Carcass"] = relationship("Carcass", lazy="joined")
    carcass_color: Mapped["CarcassColor"] = relationship("CarcassColor", lazy="joined")
    design_color: Mapped["DesignColor"] = relationship("DesignColor", lazy="joined")
    terminal: Mapped["Terminal"] = relationship("Terminal", lazy="joined")


def _ensure_code(mapper, connection, target) -> None:
    code = getattr(target, "code", None)
    if code:
        return
    table = getattr(target, "__tablename__", target.__class__.__name__).rstrip("s")
    target.code = f"{table}-{uuid4().hex[:8]}"


for _model in (
    CoffeeMachine,
    Fridge,
    Carcass,
    Terminal,
    CarcassColor,
    DesignColor,
    CarcassDesignCombination,
):
    event.listen(_model, "before_insert", _ensure_code)
