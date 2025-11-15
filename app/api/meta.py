"""Meta endpoints returning catalog dictionaries."""

from __future__ import annotations

from typing import Dict, Iterable, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import (
    Carcass,
    CarcassColor,
    CarcassDesignCombination,
    CoffeeMachine,
    DesignColor,
    Fridge,
    Terminal,
)
from ..schemas import (
    CarcassColorSchema,
    CarcassSchema,
    CarcassVariationSchema,
    ColorRefSchema,
    CoffeeMachineSchema,
    DesignColorSchema,
    FridgeSchema,
    MetaResponse,
    TerminalSchema,
    parse_gallery,
    split_specs,
)

router = APIRouter(tags=["meta"])


async def _fetch_active(session: AsyncSession, model) -> Iterable:
    stmt: Select = select(model).where(model.active.is_(True)).order_by(model.id)
    result = await session.execute(stmt)
    return result.scalars().all()


def _absolute_url(value: str | None, request: Request) -> str | None:
    if not value:
        return value
    if value.startswith(("http://", "https://")):
        return value
    base = str(request.base_url).rstrip("/")
    path = value if value.startswith("/") else f"/{value}"
    return f"{base}{path}"


def _absolute_gallery(urls: List[str], request: Request) -> List[str]:
    return [_absolute_url(url, request) for url in urls if url]


def _catalog_schema(item, schema_cls, request: Request):
    payload = {
        "id": item.id,
        "code": item.code,
        "name": item.name,
        "price": item.price,
        "main_image_url": _absolute_url(item.main_image_url, request),
        "gallery_image_urls": _absolute_gallery(parse_gallery(item.gallery_image_urls), request),
        "specs_short": split_specs(getattr(item, "specs", "")),
        "active": item.active,
    }
    if hasattr(item, "short_title"):
        payload["short_title"] = getattr(item, "short_title")
    return schema_cls(**payload)


def _color_schema(item, schema_cls, request: Request):
    return schema_cls(
        id=item.id,
        code=item.code,
        name=item.name,
        price_delta=item.price_delta,
        main_image_url=_absolute_url(item.main_image_url, request),
        gallery_image_urls=_absolute_gallery(parse_gallery(item.gallery_image_urls), request),
        active=item.active,
    )


async def _load_variations(
    session: AsyncSession, request: Request
) -> Dict[int, List[CarcassVariationSchema]]:
    stmt: Select = (
        select(CarcassDesignCombination)
        .where(CarcassDesignCombination.active.is_(True))
        .order_by(CarcassDesignCombination.id)
    )
    result = await session.execute(stmt)
    combinations = result.scalars().all()
    variations: Dict[int, List[CarcassVariationSchema]] = {}
    for combo in combinations:
        carcass_color = ColorRefSchema(
            id=combo.carcass_color.id,
            code=combo.carcass_color.code,
            name=combo.carcass_color.name,
        )
        design_color = ColorRefSchema(
            id=combo.design_color.id,
            code=combo.design_color.code,
            name=combo.design_color.name,
        )
        variations.setdefault(combo.carcass_id, []).append(
            CarcassVariationSchema(
                id=combo.id,
                carcass_color=carcass_color,
                design_color=design_color,
                main_image_url=_absolute_url(combo.main_image_url, request),
                gallery_image_urls=_absolute_gallery(parse_gallery(combo.gallery_image_urls), request),
                active=combo.active,
                is_default=combo.is_default,
            )
        )
    return variations


@router.get("/meta", response_model=MetaResponse)
async def get_meta(
    request: Request, session: AsyncSession = Depends(get_session)
) -> MetaResponse:
    """Return all active catalog data."""

    machines = await _fetch_active(session, CoffeeMachine)
    fridges = await _fetch_active(session, Fridge)
    carcasses = await _fetch_active(session, Carcass)
    terminals = await _fetch_active(session, Terminal)
    carcass_colors = await _fetch_active(session, CarcassColor)
    design_colors = await _fetch_active(session, DesignColor)
    variations = await _load_variations(session, request)

    return MetaResponse(
        machines=[_catalog_schema(item, CoffeeMachineSchema, request) for item in machines],
        fridges=[_catalog_schema(item, FridgeSchema, request) for item in fridges],
        carcasses=[
            CarcassSchema(
                **_catalog_schema(item, CarcassSchema, request).model_dump(
                    exclude={"variations"}
                ),
                variations=variations.get(item.id, []),
            )
            for item in carcasses
        ],
        terminals=[_catalog_schema(item, TerminalSchema, request) for item in terminals],
        carcass_colors=[_color_schema(item, CarcassColorSchema, request) for item in carcass_colors],
        design_colors=[_color_schema(item, DesignColorSchema, request) for item in design_colors],
    )


@router.get("/machines", response_model=List[CoffeeMachineSchema], tags=["catalog"])
async def list_machines(
    request: Request, session: AsyncSession = Depends(get_session)
) -> List[CoffeeMachineSchema]:
    """Return all active coffee machines."""

    machines = await _fetch_active(session, CoffeeMachine)
    return [_catalog_schema(item, CoffeeMachineSchema, request) for item in machines]


@router.get("/fridges", response_model=List[FridgeSchema], tags=["catalog"])
async def list_fridges(
    request: Request, session: AsyncSession = Depends(get_session)
) -> List[FridgeSchema]:
    """Return all active fridges."""

    fridges = await _fetch_active(session, Fridge)
    return [_catalog_schema(item, FridgeSchema, request) for item in fridges]


@router.get("/terminals", response_model=List[TerminalSchema], tags=["catalog"])
async def list_terminals(
    request: Request, session: AsyncSession = Depends(get_session)
) -> List[TerminalSchema]:
    """Return all active payment terminals."""

    terminals = await _fetch_active(session, Terminal)
    return [_catalog_schema(item, TerminalSchema, request) for item in terminals]


@router.get("/carcasses", response_model=List[CarcassSchema], tags=["catalog"])
async def list_carcasses(
    request: Request, session: AsyncSession = Depends(get_session)
) -> List[CarcassSchema]:
    """Return all active carcasses with linked variations."""

    carcasses = await _fetch_active(session, Carcass)
    variations = await _load_variations(session, request)
    return [
        CarcassSchema(
            **_catalog_schema(item, CarcassSchema, request).model_dump(
                exclude={"variations"}
            ),
            variations=variations.get(item.id, []),
        )
        for item in carcasses
    ]


@router.get("/carcass-colors", response_model=List[CarcassColorSchema], tags=["catalog"])
async def list_carcass_colors(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> List[CarcassColorSchema]:
    """Return active carcass color reference data."""

    colors = await _fetch_active(session, CarcassColor)
    return [_color_schema(item, CarcassColorSchema, request) for item in colors]


@router.get("/design-colors", response_model=List[DesignColorSchema], tags=["catalog"])
async def list_design_colors(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> List[DesignColorSchema]:
    """Return active design color reference data."""

    colors = await _fetch_active(session, DesignColor)
    return [_color_schema(item, DesignColorSchema, request) for item in colors]
