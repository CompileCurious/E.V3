import os
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]

def mtime(path):
    try:
        return time.ctime(os.path.getmtime(path))
    except Exception:
        return 'MISSING'

items = {
    'src_shell': root / 'ui' / 'window' / 'shell_window.py',
    'src_main_ui': root / 'main_ui.py',
    'spec_shell': root / 'Shell.spec',
    'spec_kernel': root / 'Kernel.spec',
    'dist_shell': root / 'dist' / 'Shell.exe',
    'dist_kernel': root / 'dist' / 'Kernel.exe',
    'models_character': root / 'models' / 'character',
    'models_llm': root / 'models' / 'llm',
}

print('\nBuild state check:')
for k,p in items.items():
    print(f'{k}: {p} -> {mtime(p)}')

# Check for model files presence
char = items['models_character']
if char.exists():
    files = list(char.glob('*'))
    print('\nCharacter model files present in repo:', len(files))
    for f in files[:10]:
        print(' -', f.name)
else:
    print('\nNo character model folder present')

llm = items['models_llm']
if llm.exists():
    files = list(llm.glob('*'))
    print('\nLLM model files present in repo:', len(files))
    for f in files[:10]:
        print(' -', f.name)
else:
    print('\nNo llm model folder present')

print('\nShell.spec contents (first 200 lines):')
spec = items['spec_shell']
if spec.exists():
    print(spec.read_text(encoding='utf-8')[:4000])
else:
    print('Shell.spec missing')
