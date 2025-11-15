from pathlib import Path
path = Path('app/admin.py')
text = path.read_text()
old = "    column_labels = {\n        \"id\": \"ID\",\n        \"code\": \"\\u041a\\u043e\\u0434\",\n        \"name\": \"\\u041d\\u0430\\u0437\\0432\\0430\\u043d\\0438\\0435\",\n        \"price_delta\": \"\\u041d\\u0446\\u0435\\043d\\043a\\0430\",\n        \"main_image_url\": \"URL \\u0433\\u043b\\u0430\\u0432\\043d\\044f\\043c\\043e\\0433\\043e \\u0438\\u0437\\u043e\\0431\\0440\\0430\\0436\\0435\\043d\\0438\\044f\",\n        \"gallery_image_urls\": \"\\u0413\\u0430\\043b\\0435\\0440\\0435\\044f (JSON)\",\n        \"active\": \"\\u0410\\u043a\\u0442\\0438\\0432\\043d\\043e\",\n    }"
new = "    column_labels = {\n        \"id\": \"ID\",\n        \"name\": \"Название\",\n        \"price_delta\": \"Наценка\",\n        \"active\": \"Активно\",\n    }"
if old not in text:
    raise SystemExit('pattern not found')
text = text.replace(old, new, 1)
path.write_text(text)
