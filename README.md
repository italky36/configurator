# CoffeeZone Configurator Backend

Mini-backend that stores the configurator catalog, exposes a read-only public API for Tilda, and provides an admin area to manage catalog data, uploads, carcass color variations, and ready-made bundles.

## Features
- FastAPI + SQLAlchemy + SQLite (async)
- sqladmin CRUD panel with Russian-localized UI and upload previews
- Origin/Referer middleware + CORS restricted to domains from `.env`
- Public GET endpoints only: `/api/meta`, `/api/bundles`, `/api/preview`
- Local media storage (`/uploads`) with single/multiple upload fields and live previews
- Carcasses embed color variations (carcass color + design color) with their own images/galleries and “set as default” flag
- Bundles have their own names, link to a specific carcass variation, and store an Ozon URL

## Installation
```bash
git clone <repo>
cd project
pip install -r requirements.txt
```

## Configuration
```bash
cp .env.example .env
```

`.env` example:
```
DATABASE_URL=sqlite+aiosqlite:///./db.sqlite3
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password
SESSION_SECRET_KEY=super-secret
ALLOWED_ORIGINS=https://coffeezone.ru,https://*.tilda.cc
UPLOADS_DIR=uploads
UPLOADS_URL_PREFIX=/uploads
```

## Initialize DB
```bash
python -m app.main --init-db
```

## Run
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Endpoints:
- Admin: http://localhost:8000/admin
- Catalog meta: http://localhost:8000/api/meta
- Bundles: http://localhost:8000/api/bundles

## Public API
```bash
curl http://localhost:8000/api/meta
```

`/api/meta` returns catalog dictionaries. Each carcass item contains:
- base fields (`id`, `code`, `name`, price, gallery, specs, active)
- `variations`: list of objects `{ id, carcass_color, design_color, main_image_url, gallery_image_urls, active, is_default }`

`/api/bundles` → list of bundles with `carcass_id` / `carcass_color_id` / `design_color_id` and `carcass_design_combination_id`.

`/api/preview` query params:
```
coffee_machine_id, fridge_id, carcass_id, carcass_color_id, design_color_id,
terminal_id (optional), carcass_design_combination_id (optional)
```
If an exact bundle exists, the response contains `is_exact_bundle=true`, `bundle_id`, `custom_price`, and `ozon_url`.

## Uploads & Admin Notes
- Files are saved to `UPLOADS_DIR` and served at `UPLOADS_URL_PREFIX`.
- Forms include “Загрузить главную картинку” and “Загрузить изображения галереи”; uploads auto-fill URL fields and show previews.
- Russian labels are applied to menu items, columns, modals, etc.
- “Цвета корпуса” и “Цветы дизайна” — простые справочники (название + цена/дельта + активность).
- Откройте карточку каркаса и прокрутите до блока “Цветовые вариации”, чтобы добавить сочетания цветов: выберите цвет корпуса, цвет дизайна, загрузите изображения, при необходимости отметьте “Сделать основным”. Система не даст создать дубликат.
- Вариации попадают в `carcasses[i].variations` в `/api/meta`, поэтому фронтенд получает и цвета, и картинки.
- В разделе “Готовые комплекты” можно выбрать созданную вариацию (поле “Вариация каркаса”). При сохранении `carcass_id`, `carcass_color_id` и `design_color_id` подставляются автоматически, остаётся указать ссылку Ozon и статус наличия.
