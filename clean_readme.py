from pathlib import Path
text = Path('README.md').read_text()
old_block = '''- Files are saved to `UPLOADS_DIR` and served at `UPLOADS_URL_PREFIX`.
- Forms include "\u0421\u042b\u0447...'''  # ??? can't encode different
