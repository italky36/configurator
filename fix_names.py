from pathlib import Path
path = Path('app/admin.py')
text = path.read_text(encoding='utf-8')
replacements = {
    'class CarcassAdmin(CatalogModelView, model=Carcass):\n    name = "\ufffd\ufffd\u0abf\u0a8f?"?': ''}
