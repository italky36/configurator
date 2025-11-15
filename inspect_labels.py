from pathlib import Path
text = Path('app/admin.py').read_text()
start = text.index("column_labels = {\n        \"id\": \"ID\"")
print(text[start:start+220])
