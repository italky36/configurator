from pathlib import Path
text = Path('app/admin.py').read_text()
index = text.index("column_labels = {\n        \"id\": \"ID\"")
print(text[index:index+200])
