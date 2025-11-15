from pathlib import Path
text = Path('app/admin.py').read_text('utf-8')
start = text.index('    async def on_model_change')
print('\n'.join(text[start:start+400].splitlines()[:60]))
