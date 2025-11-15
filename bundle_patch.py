from pathlib import Path
path = Path('app/admin.py')
text = path.read_text()
text = text.replace('    column_list = [\n        "id",\n        "coffee_machine_id",\n        "fridge_id",', '    column_list = [\n        "id",\n        "name",\n        "coffee_machine_id",\n        "fridge_id",', 1)
text = text.replace('    form_columns = [\n        "carcass_design_combination",', '    form_columns = [\n        "name",\n        "carcass_design_combination",', 1)
text = text.replace('    column_labels = {\n        "id": "ID",', '    column_labels = {\n        "id": "ID",\n        "name": "Название",', 1)
path.write_text(text)
