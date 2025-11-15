"""Custom WTForms fields for sqladmin forms."""

from __future__ import annotations

from typing import List

from sqladmin.fields import FileField as SQLAdminFileField


class ImageUploadField(SQLAdminFileField):
    """Single image upload field with accept filter."""

    def __init__(self, *args, **kwargs):
        render_kw = kwargs.setdefault("render_kw", {})
        render_kw.setdefault("accept", "image/*")
        super().__init__(*args, **kwargs)


class GalleryUploadField(SQLAdminFileField):
    """Multiple upload field for gallery images."""

    def __init__(self, *args, **kwargs):
        render_kw = kwargs.setdefault("render_kw", {})
        render_kw.setdefault("accept", "image/*")
        render_kw["multiple"] = True
        super().__init__(*args, **kwargs)
        self._files: List = []

    def process_formdata(self, valuelist):
        files = [item for item in valuelist if getattr(item, "filename", "")]
        self.data = files or None

