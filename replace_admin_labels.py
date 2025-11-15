from pathlib import Path
path = Path('app/admin.py')
text = path.read_text(encoding='utf-8')
old = "    column_labels = {\n        \"id\": \"ID\",\n        \"code\": \"\uFFFD\uFFFD\",\n        \"name\": \"\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\",\n        \"price_delta\": \"\uFFFD\uFFFD\uFFFD\uFFFD\",\n        \"main_image_url\": \"URL \uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD \uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\",\n        \"gallery_image_urls\": \"\uFFFD\uFFFD\uFFFD\uFFFD (JSON)\",\n        \"active\": \"\uFFFD\uFFFD\uFFFD\uFFFD\uFFFD\",\n    }"
new = "    column_labels = {\n        \"id\": \"ID\",\n        \"code\": \"Код\",\n        \"name\": \"Название\",\n        \"price_delta\": \"Наценка\",\n        \"main_image_url\": \"URL главного изображения\",\n        \"gallery_image_urls\": \"Галерея (JSON)\",\n        \"active\": \"Активно\",\n    }"
if old not in text:
    raise SystemExit('pattern not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
