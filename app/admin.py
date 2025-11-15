"""sqladmin configuration for the CoffeeZone Configurator."""



from __future__ import annotations



import json

import re

from io import BytesIO
from pathlib import Path

from secrets import token_urlsafe

from typing import Any, Iterable, List

from uuid import uuid4



from fastapi import FastAPI

from sqlalchemy import select

from sqlalchemy.orm import selectinload

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import StreamingResponse
from wtforms import HiddenField



from .config import settings

from .db import AsyncSessionLocal, engine

from .forms import GalleryUploadField, ImageUploadField
from .models import (
    Bundle,
    Carcass,
    CarcassColor,
    CarcassDesignCombination,
    CoffeeMachine,
    DesignColor,
    Fridge,
    Terminal,
)
from .schemas import parse_gallery
from .storage import save_upload_file
from .excel import build_xlsx, parse_xlsx
from sqladmin.helpers import secure_filename





class AdminAuth(AuthenticationBackend):

    """Simple credential-based authentication backend for sqladmin."""



    def __init__(self) -> None:

        super().__init__(secret_key=settings.session_secret_key)



    async def login(self, request: Request) -> bool:

        form = await request.form()

        username = form.get("username")

        password = form.get("password")



        if username == settings.admin_username and password == settings.admin_password:

            request.session.update({"admin_session": token_urlsafe(16)})

            return True

        return False



    async def logout(self, request: Request) -> bool:

        request.session.clear()

        return True



    async def authenticate(self, request: Request) -> bool:

        return request.session.get("admin_session") is not None





class MediaUploadMixin:

    """Mixin injecting upload fields & persistence for image columns."""



    main_upload_field = "main_image_upload"

    gallery_upload_field = "gallery_uploads"

    form_overrides = {
        "main_image_url": HiddenField,
        "gallery_image_urls": HiddenField,
    }


    async def scaffold_form(self):

        form_class = await super().scaffold_form()

        if hasattr(form_class, "main_image_url") and not hasattr(

            form_class, self.main_upload_field

        ):

            setattr(

                form_class,

                self.main_upload_field,

                ImageUploadField("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0433\u043b\u0430\u0432\u043d\u0443\u044e \u043a\u0430\u0440\u0442\u0438\u043d\u043a\u0443"),

            )

        if hasattr(form_class, "gallery_image_urls") and not hasattr(

            form_class, self.gallery_upload_field

        ):

            setattr(

                form_class,

                self.gallery_upload_field,

                GalleryUploadField("\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f \u0433\u0430\u043b\u0435\u0440\u0435\u0438"),

            )

        if hasattr(form_class, "active"):

            form_class.active.default = True

        return form_class



    async def get_object_for_edit(self, value: Any) -> Any:

        obj = await super().get_object_for_edit(value)

        self._ensure_placeholder_fields(obj)

        return obj



    async def on_model_change(

        self, data: dict, model: Any, is_created: bool, request: Request | None = None

    ) -> None:

        await self._persist_uploads(data, model)

        self._ensure_code_field(data, model)

        await super().on_model_change(data, model, is_created)



    async def _persist_uploads(self, data: dict, model: Any) -> None:

        upload = data.pop(self.main_upload_field, None)

        main_url = await self._save_upload(upload)

        if main_url:

            data["main_image_url"] = main_url



        gallery_uploads = data.pop(self.gallery_upload_field, None)

        gallery_urls: List[str] = []

        for item in self._iter_uploads(gallery_uploads):

            saved = await self._save_upload(item)

            if saved:

                gallery_urls.append(saved)



        if gallery_urls:

            base = data.get("gallery_image_urls") or getattr(

                model, "gallery_image_urls", ""

            )

            merged = parse_gallery(base)

            merged.extend(gallery_urls)

            data["gallery_image_urls"] = json.dumps(merged, ensure_ascii=False)

        elif "gallery_image_urls" in data:

            normalized = parse_gallery(data["gallery_image_urls"])

            data["gallery_image_urls"] = json.dumps(normalized, ensure_ascii=False)



    async def _save_upload(self, upload: UploadFile | None) -> str | None:

        if not self._is_valid_upload(upload):

            return None

        assert upload is not None

        return await save_upload_file(upload)



    def _iter_uploads(self, uploads: Any | None) -> Iterable[UploadFile]:

        if uploads is None:

            return []

        if isinstance(uploads, (list, tuple)):

            return [item for item in uploads if self._is_valid_upload(item)]

        if self._is_valid_upload(uploads):

            return [uploads]

        return []



    def _is_valid_upload(self, upload: UploadFile | None) -> bool:

        return bool(upload and getattr(upload, "filename", ""))



    def _ensure_placeholder_fields(self, obj: Any | None) -> None:

        if obj is None:

            return

        for attr in (self.main_upload_field, self.gallery_upload_field):

            if not hasattr(obj, attr):

                setattr(obj, attr, None)



    def _ensure_code_field(self, data: dict, model: Any) -> None:

        code = (data.get("code") or getattr(model, "code", "") or "").strip()

        if code:

            data["code"] = code

            return

        base_name = (data.get("name") or getattr(model, "name", "") or "").strip() or "item"

        slug = re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-") or "item"

        data["code"] = f"{slug}-{uuid4().hex[:6]}"







class ExcelImportExportMixin:

    """Mixin adding XLSX export & import capabilities."""

    export_types = ["xlsx"]
    can_import = True

    def _export_columns(self) -> list[str]:
        return [column.name for column in self.model.__table__.columns]

    def export_data(self, data: list[object], export_type: str = "xlsx"):
        columns = self._export_columns()
        rows = ([getattr(row, column, None) for column in columns] for row in data)
        content = build_xlsx(columns, rows)
        filename = secure_filename(self.get_export_name(export_type="xlsx"))
        return StreamingResponse(
            BytesIO(content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment;filename={filename}"},
        )

    async def handle_import_bytes(self, payload: bytes) -> None:
        rows = parse_xlsx(payload)
        if not rows:
            return
        await self._import_rows(rows)

    async def _import_rows(self, rows: list[dict[str, object]]) -> None:
        table_columns = {column.name: column for column in self.model.__table__.columns}
        pk_name = self.pk_columns[0].name if self.pk_columns else "id"
        async with self.session_maker() as session:
            for row in rows:
                cleaned: dict[str, object] = {}
                for key, value in row.items():
                    if key not in table_columns:
                        continue
                    cleaned[key] = self._convert_value(table_columns[key], value)
                if not cleaned:
                    continue
                pk_value = cleaned.pop(pk_name, None)
                obj = None
                if pk_value not in (None, ""):
                    obj = await session.get(self.model, pk_value)
                if obj is None:
                    obj = self.model()
                    session.add(obj)
                for field, value in cleaned.items():
                    setattr(obj, field, value)
            await session.commit()

    def _convert_value(self, column, value: object) -> object:
        if value is None:
            return None
        try:
            python_type = column.type.python_type
        except NotImplementedError:
            return value
        if python_type is bool:
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on", "\u0434\u0430"}
            return bool(value)
        if python_type is int:
            if isinstance(value, str) and not value.strip():
                return None
            if isinstance(value, float):
                return int(value)
            return python_type(value)
        if python_type is float:
            return python_type(value)
        if python_type is str:
            return "" if value is None else str(value)
        if isinstance(value, python_type):
            return value
        return python_type(value)


class CatalogModelView(ExcelImportExportMixin, MediaUploadMixin, ModelView):

    can_delete = True

    can_create = True

    can_edit = True

    column_list = ["id", "name", "price", "active"]

    form_columns = [

        "name",

        "short_title",

        "specs",

        "price",

        "main_image_url",

        "gallery_image_urls",

        "active",

    ]

    form_widget_args = {

        "specs": {"rows": 4},

        "gallery_image_urls": {"rows": 4},

    }

    column_labels = {

        "id": "ID",

        "name": "Название",

        "name": "Название",

        "name": "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435",

        "short_title": "\u041a\u043e\u0440\u043e\u0442\u043a\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435",

        "specs": "\u0425\u0430\u0440\u0430\u043a\u0442\u0435\u0440\u0438\u0441\u0442\u0438\u043a\u0438",

        "price": "\u0426\u0435\u043d\u0430 (\u20bd)",

        "main_image_url": "URL \u0433\u043b\u0430\u0432\u043d\u043e\u0433\u043e \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f",

        "gallery_image_urls": "\u0413\u0430\u043b\u0435\u0440\u0435\u044f (JSON)",

        "active": "\u0410\u043a\u0442\u0438\u0432\u043d\u043e",

    }





class CoffeeMachineAdmin(CatalogModelView, model=CoffeeMachine):

    name = "\u041a\u043e\u0444\u0435\u043c\u0430\u0448\u0438\u043d\u0430"

    name_plural = "\u041a\u043e\u0444\u0435\u043c\u0430\u0448\u0438\u043d\u044b"





class FridgeAdmin(CatalogModelView, model=Fridge):

    name = "\u0425\u043e\u043b\u043e\u0434\u0438\u043b\u044c\u043d\u0438\u043a"

    name_plural = "\u0425\u043e\u043b\u043e\u0434\u0438\u043b\u044c\u043d\u0438\u043a\u0438"

    form_columns = [col for col in CatalogModelView.form_columns if col != "short_title"]





class CarcassAdmin(CatalogModelView, model=Carcass):

    name = "\u041a\u0430\u0440\u043a\u0430\u0441"

    name_plural = "\u041a\u0430\u0440\u043a\u0430\u0441\u044b"

    form_columns = [

        "name",


        "specs",

        "price",

        "active",

    ]

    edit_template = "carcass_edit.html"

    create_template = "carcass_edit.html"



    async def get_object_for_edit(self, value: Any) -> Any:

        obj = await super().get_object_for_edit(value)

        if obj is None:

            return None

        async with self.session_maker() as session:

            stmt = (

                select(CarcassDesignCombination)

                .options(

                    selectinload(CarcassDesignCombination.carcass_color),

                    selectinload(CarcassDesignCombination.design_color),

                )

                .where(CarcassDesignCombination.carcass_id == obj.id)

            )

            result = await session.execute(stmt)

            obj.design_combinations = result.scalars().unique().all()

        return obj





class TerminalAdmin(CatalogModelView, model=Terminal):

    name = "\u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b"

    name_plural = "\u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b\u044b"

    form_columns = [col for col in CatalogModelView.form_columns if col != "short_title"]





class ColorModelView(ExcelImportExportMixin, MediaUploadMixin, ModelView):

    can_delete = True

    can_create = True

    can_edit = True

    column_list = ["id", "name", "price_delta", "active"]

    form_columns = [

        "name",

        "price_delta",

        "active",

    ]

    column_labels = {

        "id": "ID",

        "name": "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435",

        "price_delta": "\u041d\u0430\u0446\u0435\u043d\u043a\u0430",

        "active": "\u0410\u043a\u0442\u0438\u0432\u043d\u043e",

    }





class CarcassColorAdmin(ColorModelView, model=CarcassColor):

    name = "\u0426\u0432\u0435\u0442 \u043a\u0430\u0440\u043a\u0430\u0441\u0430"

    name_plural = "\u0426\u0432\u0435\u0442\u0430 \u043a\u0430\u0440\u043a\u0430\u0441\u043e\u0432"





class DesignColorAdmin(ColorModelView, model=DesignColor):

    name = "\u0426\u0432\u0435\u0442 \u0434\u0438\u0437\u0430\u0439\u043d\u0430"

    name_plural = "\u0426\u0432\u0435\u0442\u0430 \u0434\u0438\u0437\u0430\u0439\u043d\u0430"





class CarcassDesignCombinationAdmin(MediaUploadMixin, ModelView, model=CarcassDesignCombination):

    name = "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u044f \u043a\u0430\u0440\u043a\u0430\u0441\u0430"

    name_plural = "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u0438 \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u044f \u043a\u0430\u0440\u043a\u0430\u0441\u0430"

    column_list = [

        "id",

        "code",

        "name",

        "carcass",

        "carcass_color",

        "design_color",

        "active",

    ]

    form_columns = [

        "name",

        "carcass",

        "carcass_color",

        "design_color",

        "main_image_url",

        "gallery_image_urls",

        "is_default",

        "active",

    ]

    column_labels = {

        "id": "ID",

        "name": "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435",

        "carcass": "\u041a\u0430\u0440\u043a\u0430\u0441",

        "carcass_color": "\u0426\u0432\u0435\u0442 \u043a\u0430\u0440\u043a\u0430\u0441\u0430",

        "design_color": "\u0426\u0432\u0435\u0442 \u0434\u0438\u0437\u0430\u0439\u043d\u0430",

        "main_image_url": "URL \u0433\u043b\u0430\u0432\u043d\u043e\u0433\u043e \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f",

        "gallery_image_urls": "\u0413\u0430\u043b\u0435\u0440\u0435\u044f (JSON)",

        "active": "\u0410\u043a\u0442\u0438\u0432\u043d\u043e",

    }

    form_ajax_refs = {

        "carcass": {"fields": (Carcass.name, Carcass.code)},

        "carcass_color": {"fields": (CarcassColor.name, CarcassColor.code)},

        "design_color": {"fields": (DesignColor.name, DesignColor.code)},

    }





class BundleAdmin(ExcelImportExportMixin, ModelView, model=Bundle):
    name = "\u0413\u043e\u0442\u043e\u0432\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442"
    name_plural = "\u0413\u043e\u0442\u043e\u0432\u044b\u0435 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0442\u044b"
    column_list = [
        "id",
        "name",
        "coffee_machine",
        "fridge",
        "carcass_design_combination",
        "terminal",
        "custom_price",
        "ozon_url",
        "is_available",
        "show_on_site",
    ]
    form_columns = [
        "name",
        "carcass_design_combination",
        "coffee_machine",
        "fridge",
        "terminal",
        "custom_price",
        "ozon_url",
        "is_available",
        "show_on_site",
    ]
    column_labels = {
        "id": "ID",
        "name": "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043d\u0430\u0431\u043e\u0440\u0430",
        "coffee_machine": "\u041a\u043e\u0444\u0435\u043c\u0430\u0448\u0438\u043d\u0430",
        "fridge": "\u0425\u043e\u043b\u043e\u0434\u0438\u043b\u044c\u043d\u0438\u043a",
        "carcass_design_combination": "\u0412\u0430\u0440\u0438\u0430\u0446\u0438\u044f \u043a\u0430\u0440\u043a\u0430\u0441\u0430",
        "terminal": "\u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b",
        "custom_price": "\u0426\u0435\u043d\u0430 (\u043a\u0430\u0441\u0442\u043e\u043c)",
        "ozon_url": "\u0421\u0441\u044b\u043b\u043a\u0430 Ozon",
        "is_available": "\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438",
        "show_on_site": "\u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u043d\u0430 \u0441\u0430\u0439\u0442\u0435",
    }
    form_ajax_refs = {
        "carcass_design_combination": {
            "fields": (CarcassDesignCombination.name,),
            "label_attr": "name",
            "order_by": (CarcassDesignCombination.name,),
            "minimum_input_length": 0,
        },
        "coffee_machine": {
            "fields": (CoffeeMachine.name, CoffeeMachine.code),
            "label_attr": "name",
            "order_by": (CoffeeMachine.name,),
            "minimum_input_length": 0,
        },
        "fridge": {
            "fields": (Fridge.name, Fridge.code),
            "label_attr": "name",
            "order_by": (Fridge.name,),
            "minimum_input_length": 0,
        },
        "terminal": {
            "fields": (Terminal.name, Terminal.code),
            "label_attr": "name",
            "order_by": (Terminal.name,),
            "minimum_input_length": 0,
        },
    }
    column_formatters = {
        "coffee_machine": lambda m, _: m.coffee_machine.name if getattr(m, "coffee_machine", None) else "-",
        "fridge": lambda m, _: m.fridge.name if getattr(m, "fridge", None) else "-",
        "carcass_design_combination": lambda m, _: m.carcass_design_combination.name if getattr(m, "carcass_design_combination", None) else "-",
        "terminal": lambda m, _: m.terminal.name if getattr(m, "terminal", None) else "-",
    }

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request | None = None
    ) -> None:
        combo_obj = data.pop("carcass_design_combination", None)
        combo = None
        if combo_obj:
            if isinstance(combo_obj, CarcassDesignCombination):
                combo = combo_obj
            else:
                async with self.session_maker() as session:
                    combo = await session.get(CarcassDesignCombination, int(combo_obj))
        if combo:
            data["carcass_design_combination_id"] = combo.id
            data["carcass_id"] = combo.carcass_id
            data["carcass_color_id"] = combo.carcass_color_id
            data["design_color_id"] = combo.design_color_id
        relation_fields: tuple[tuple[str, str, type[Any], bool], ...] = (
            ("coffee_machine", "coffee_machine_id", CoffeeMachine, False),
            ("fridge", "fridge_id", Fridge, True),
            ("terminal", "terminal_id", Terminal, True),
        )
        for attr_name, column_name, model_cls, allow_empty in relation_fields:
            value = data.pop(attr_name, None)
            if value in (None, "", "null"):
                if allow_empty:
                    data[column_name] = None
                elif not is_created and getattr(model, column_name, None):
                    data[column_name] = getattr(model, column_name)
                continue
            if isinstance(value, model_cls):
                data[column_name] = value.id
            else:
                data[column_name] = int(value)
        await super().on_model_change(data, model, is_created)


def setup_admin(app: FastAPI) -> Admin:

    """Register admin views and return the Admin instance."""



    templates_dir = Path(__file__).resolve().parent.parent / "templates"

    admin = Admin(

        app,

        engine,

        authentication_backend=AdminAuth(),

        session_maker=AsyncSessionLocal,

        templates_dir=str(templates_dir),

    )

    admin.add_view(CoffeeMachineAdmin)

    admin.add_view(FridgeAdmin)

    admin.add_view(CarcassAdmin)

    admin.add_view(TerminalAdmin)

    admin.add_view(CarcassColorAdmin)

    admin.add_view(DesignColorAdmin)

    admin.add_view(BundleAdmin)

    return admin

