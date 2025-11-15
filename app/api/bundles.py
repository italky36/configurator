"""Bundle related API endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Bundle
from ..schemas import BundleSchema, PreviewResponse

router = APIRouter(tags=["bundles"])


def _bundle_to_schema(bundle: Bundle) -> BundleSchema:
    return BundleSchema(
        id=bundle.id,
        name=bundle.name,
        coffee_machine_id=bundle.coffee_machine_id,
        fridge_id=bundle.fridge_id,
        carcass_id=bundle.carcass_id,
        carcass_color_id=bundle.carcass_color_id,
        design_color_id=bundle.design_color_id,
        terminal_id=bundle.terminal_id,
        carcass_design_combination_id=bundle.carcass_design_combination_id,
        custom_price=bundle.custom_price,
        ozon_url=bundle.ozon_url,
        is_available=bundle.is_available,
    )


@router.get("/bundles", response_model=List[BundleSchema])
async def list_bundles(session: AsyncSession = Depends(get_session)) -> List[BundleSchema]:
    """Return all bundles marked for show_on_site."""

    stmt: Select = select(Bundle).where(Bundle.show_on_site.is_(True)).order_by(Bundle.id)
    result = await session.execute(stmt)
    bundles = result.scalars().all()
    return [_bundle_to_schema(bundle) for bundle in bundles]


@router.get("/preview", response_model=PreviewResponse)
async def preview_bundle(
    coffee_machine_id: int = Query(..., ge=1),
    fridge_id: int | None = Query(default=None, ge=1),
    carcass_id: int = Query(..., ge=1),
    carcass_color_id: int = Query(..., ge=1),
    design_color_id: int = Query(..., ge=1),
    terminal_id: int | None = Query(default=None, ge=1),
    carcass_design_combination_id: int | None = Query(default=None, ge=1),
    session: AsyncSession = Depends(get_session),
) -> PreviewResponse:
    """Return matching bundle preview if exists."""

    filters = [
        Bundle.coffee_machine_id == coffee_machine_id,
        Bundle.carcass_id == carcass_id,
        Bundle.carcass_color_id == carcass_color_id,
        Bundle.design_color_id == design_color_id,
    ]
    if fridge_id is None:
        filters.append(Bundle.fridge_id.is_(None))
    else:
        filters.append(Bundle.fridge_id == fridge_id)
    if carcass_design_combination_id is not None:
        filters.append(Bundle.carcass_design_combination_id == carcass_design_combination_id)
    if terminal_id is None:
        filters.append(Bundle.terminal_id.is_(None))
    else:
        filters.append(Bundle.terminal_id == terminal_id)

    stmt: Select = select(Bundle).where(and_(*filters)).limit(1)
    result = await session.execute(stmt)
    bundle = result.scalars().first()

    if not bundle:
        return PreviewResponse(is_exact_bundle=False)

    return PreviewResponse(
        is_exact_bundle=True,
        bundle_id=bundle.id,
        custom_price=bundle.custom_price,
        ozon_url=bundle.ozon_url,
    )
