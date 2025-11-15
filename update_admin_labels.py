from pathlib import Path
path = Path('app/admin.py')
text = path.read_text()
blocks = [
"    column_labels = {\n        \"id\": \"ID\",\n        \"name\": \"Название\",\n        \"short_title\": \"Короткое название\",\n        \"specs\": \"Характеристики\",\n        \"price\": \"Цена (₽)\",\n        \"main_image_url\": \"URL главного изображения\",\n        \"gallery_image_urls\": \"Галерея (JSON)\",\n        \"active\": \"Активно\",\n    }\n",
"    column_labels = {\n        \"id\": \"ID\",\n        \"code\": \"Код\",\n        \"name\": \"Название\",\n        \"price_delta\": \"Наценка\",\n        \"active\": \"Активно\",\n    }\n",
"    column_labels = {\n        \"id\": \"ID\",\n        \"code\": \"Код\",\n        \"name\": \"Название\",\n        \"carcass\": \"Каркас\",\n        \"carcass_color\": \"Цвет каркаса\",\n        \"design_color\": \"Цвет дизайна\",\n        \"main_image_url\": \"URL главного изображения\",\n        \"gallery_image_urls\": \"Галерея (JSON)\",\n        \"is_default\": \"Основной\",\n        \"active\": \"Активно\",\n    }\n",
"    column_labels = {\n        \"id\": \"ID\",\n        \"coffee_machine_id\": \"Кофемашина\",\n        \"fridge_id\": \"Холодильник\",\n        \"carcass_id\": \"Каркас\",\n        \"carcass_color_id\": \"Цвет каркаса\",\n        \"design_color_id\": \"Цвет дизайна\",\n        \"terminal_id\": \"Терминал\",\n        \"custom_price\": \"Цена (кастом)\",\n        \"ozon_url\": \"Ссылка Ozon\",\n        \"is_available\": \"В наличии\",\n        \"show_on_site\": \"Показывать на сайте\",\n        \"carcass_design_combination_id\": \"Вариация каркаса\",\n    }\n",
]

# first block currently has code field, replace to a version without it
text = text.replace('    column_labels = {\n        \"id\": \"ID\",\n        \"code\": \"\\u041a\\u043e\\u0434\",\n', blocks[0], 1)
# second block with colors currently includes main_image, replace entire definition
target = '    column_labels = {\n        \"id\": \"ID\",\n        \"code\": \"\\u041a\\u043e\\043e\\0434\",\n'
text = text.replace(text[text.index(target):text.index(target)+200], blocks[1], 1)

Path('app/admin.py').write_text(text)
