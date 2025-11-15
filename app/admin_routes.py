"""Custom admin-only routes for managing carcass color variations."""

from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import Select, and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from .db import get_session
from .models import Carcass, CarcassColor, CarcassDesignCombination, DesignColor
from .storage import save_upload_file

router = APIRouter(tags=["admin-variations"])


def _ensure_admin(request: Request) -> None:
    if not request.session.get("admin_session"):
        raise HTTPException(status_code=403)


async def _save_optional(file: UploadFile | None) -> str | None:
    if file and getattr(file, "filename", ""):
        return await save_upload_file(file)
    return None


async def _save_gallery(files: List[UploadFile] | UploadFile | None) -> List[str]:
    urls: List[str] = []
    if not files:
        return urls
    uploads = files if isinstance(files, list) else [files]
    for upload in uploads:
        if getattr(upload, "filename", ""):
            saved = await save_upload_file(upload)
            urls.append(saved)
    return urls


async def _set_default_variation(session: AsyncSession, carcass_id: int, variation_id: int) -> None:
    stmt: Select = select(CarcassDesignCombination).where(CarcassDesignCombination.carcass_id == carcass_id)
    result = await session.execute(stmt)
    combos = result.scalars().all()
    for combo in combos:
        combo.is_default = combo.id == variation_id
    await session.commit()


@router.post("/admin/carcasses/{carcass_id}/variations", name="admin_create_variation")
async def create_variation(
    carcass_id: int,
    request: Request,
    carcass_color_id: int = Form(...),
    design_color_id: int = Form(...),
    main_image_upload: UploadFile | None = File(None),
    gallery_uploads: List[UploadFile] | UploadFile | None = File(None),
    is_default: bool = Form(False),
    session: AsyncSession = Depends(get_session),
):
    _ensure_admin(request)
    carcass = await session.get(Carcass, carcass_id)
    if not carcass:
        raise HTTPException(status_code=404, detail="Carcass not found")

    stmt: Select = select(CarcassDesignCombination).where(
        and_(
            CarcassDesignCombination.carcass_id == carcass_id,
            CarcassDesignCombination.carcass_color_id == carcass_color_id,
            CarcassDesignCombination.design_color_id == design_color_id,
        )
    )
    existing = await session.execute(stmt)
    if existing.scalars().first():
        return RedirectResponse(
            str(
                request.url_for("admin:edit", identity="carcass", pk=str(carcass_id))
            )
            + "?variation_error=duplicate",
            status_code=302,
        )

    carcass_color = await session.get(CarcassColor, carcass_color_id)
    design_color = await session.get(DesignColor, design_color_id)
    if not carcass_color or not design_color:
        raise HTTPException(status_code=404, detail="Color not found")

    main_url = await _save_optional(main_image_upload)
    gallery_urls = await _save_gallery(gallery_uploads)

    combination = CarcassDesignCombination(
        carcass_id=carcass_id,
        carcass_color_id=carcass_color_id,
        design_color_id=design_color_id,
        name=f"{carcass.name} · {carcass_color.name} + {design_color.name}",
        main_image_url=main_url,
        gallery_image_urls=json.dumps(gallery_urls, ensure_ascii=False),
        is_default=is_default,
    )
    session.add(combination)
    await session.commit()
    await session.refresh(combination)
    if is_default:
        await _set_default_variation(session, carcass_id, combination.id)

    return RedirectResponse(
        str(request.url_for("admin:edit", identity="carcass", pk=str(carcass_id)))
        + "?variation_status=created",
        status_code=302,
    )


@router.post(
    "/admin/carcasses/{carcass_id}/variations/{variation_id}/delete",
    name="admin_delete_variation",
)
async def delete_variation(
    carcass_id: int,
    variation_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _ensure_admin(request)
    variation = await session.get(CarcassDesignCombination, variation_id)
    if not variation or variation.carcass_id != carcass_id:
        raise HTTPException(status_code=404, detail="Variation not found")
    await session.delete(variation)
    await session.commit()
    return RedirectResponse(
        str(request.url_for("admin:edit", identity="carcass", pk=str(carcass_id)))
        + "?variation_status=deleted",
        status_code=302,
    )


@router.post(
    "/admin/carcasses/{carcass_id}/variations/{variation_id}/default",
    name="admin_set_default_variation",
)
async def set_default_variation(
    carcass_id: int,
    variation_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    _ensure_admin(request)
    variation = await session.get(CarcassDesignCombination, variation_id)
    if not variation or variation.carcass_id != carcass_id:
        raise HTTPException(status_code=404, detail="Variation not found")
    await _set_default_variation(session, carcass_id, variation_id)
    return RedirectResponse(
        str(request.url_for("admin:edit", identity="carcass", pk=str(carcass_id)))
        + "?variation_status=updated",
        status_code=302,
    )


@router.post("/admin/{identity}/import", name="admin_import")
async def import_from_xlsx(
    identity: str,
    request: Request,
    file: UploadFile = File(...),
):
    _ensure_admin(request)
    admin = request.app.state.admin
    model_view = admin._find_model_view(identity)  # type: ignore[attr-defined]
    if not hasattr(model_view, "handle_import_bytes"):
        raise HTTPException(status_code=404, detail="Import not supported")
    contents = await file.read()
    await model_view.handle_import_bytes(contents)
    return RedirectResponse(
        str(request.url_for("admin:list", identity=identity))
        + "?import_status=success",
        status_code=302,
    )
