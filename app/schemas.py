"""Pydantic schemas for API responses."""

from __future__ import annotations

import json
from typing import List, Sequence

from pydantic import BaseModel, Field


def parse_gallery(value: str | Sequence[str] | None) -> List[str]:
    """Parse gallery JSON/text to a list of URLs."""

    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            return []
        return [str(item) for item in data if isinstance(item, str) and item]
    return [str(item) for item in value if isinstance(item, str) and item]


def split_specs(specs: str | None) -> List[str]:
    """Split multi-line specs into a list."""

    if not specs:
        return []
    return [line.strip() for line in specs.splitlines() if line.strip()]


class BaseCatalogSchema(BaseModel):
    id: int
    code: str
    name: str
    price: int
    main_image_url: str | None = None
    gallery_image_urls: List[str] = Field(default_factory=list)
    specs_short: List[str] = Field(default_factory=list)
    active: bool


class CoffeeMachineSchema(BaseCatalogSchema):
    short_title: str | None = None


class FridgeSchema(BaseCatalogSchema):
    pass


class ColorRefSchema(BaseModel):
    id: int
    code: str
    name: str


class CarcassVariationSchema(BaseModel):
    id: int
    carcass_color: ColorRefSchema
    design_color: ColorRefSchema
    main_image_url: str | None = None
    gallery_image_urls: List[str] = Field(default_factory=list)
    syrup_image_url: str | None = None
    active: bool
    is_default: bool


class CarcassSchema(BaseCatalogSchema):
    has_syrup: bool = False
    variations: List[CarcassVariationSchema] = Field(default_factory=list)


class TerminalSchema(BaseCatalogSchema):
    pass


class BaseColorSchema(BaseModel):
    id: int
    code: str
    name: str
    price_delta: int
    main_image_url: str | None = None
    gallery_image_urls: List[str] = Field(default_factory=list)
    active: bool


class CarcassColorSchema(BaseColorSchema):
    pass


class DesignColorSchema(BaseColorSchema):
    pass


class MetaResponse(BaseModel):
    machines: List[CoffeeMachineSchema]
    fridges: List[FridgeSchema]
    carcasses: List[CarcassSchema]
    carcass_colors: List[CarcassColorSchema]
    design_colors: List[DesignColorSchema]
    terminals: List[TerminalSchema]


class BundleSchema(BaseModel):
    id: int
    name: str
    coffee_machine_id: int
    fridge_id: int | None = None
    carcass_id: int
    carcass_color_id: int
    design_color_id: int
    terminal_id: int | None = None
    carcass_design_combination_id: int | None = None
    custom_price: int | None = None
    ozon_url: str | None = None
    is_available: bool


class PreviewResponse(BaseModel):
    is_exact_bundle: bool
    bundle_id: int | None = None
    custom_price: int | None = None
    ozon_url: str | None = None
