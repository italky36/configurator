from pathlib import Path
path = Path('app/admin.py')
text = path.read_text('utf-8')
old = '''    column_labels = {
        "id": "ID",
        "code": "\u041a\u043e\u0434",
        "name": "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435",
        "price_delta": "\u041d\u0430\u0446\u0435\u043d\u043a\u0430",
        "main_image_url": "URL \u0433\u043b\u0430\u0432\u043d\u043e\u0433\u043e \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f",
        "gallery_image_urls": "\u0413\u0430\u043b\u0435\u0440\u0435\u044f (JSON)",
        "active": "\u0410\u043a\u0442\u0438\u0432\u043d\u043e",
    }'''
new = '''    column_labels = {
        "id": "ID",
        "name": "Название",
        "price_delta": "Наценка",
        "active": "Активно",
    }'''
if old not in text:
    raise SystemExit('pattern not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
