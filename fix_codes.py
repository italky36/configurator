from pathlib import Path
path = Path("app/admin.py")
text = path.read_text()
text = text.replace("        \"code\": \"\\u041a\\u043e\\u0434\",\n", "", 1)
text = text.replace("        \"code\": \"\\u041a\\u043e\\u0434\",\n", "", 1)
path.write_text(text)
