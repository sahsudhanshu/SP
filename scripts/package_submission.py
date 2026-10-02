"""Package source and submission artifacts without secrets, caches or model weights."""
import argparse
import os
import shutil
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=ROOT/'work/submission')
args=parser.parse_args()
destination=args.output.resolve(); destination.mkdir(parents=True,exist_ok=True)
skip_dirs={'.git','.venv','.models','.next','node_modules','__pycache__','.pytest_cache','work'}
files=[]
for current,dirs,names in os.walk(ROOT):
    dirs[:]=[d for d in dirs if d not in skip_dirs]
    for name in names:
        file=Path(current)/name
        if (name.startswith('.env') and name!='.env.example') or file.suffix in {'.db','.pyc','.tsbuildinfo','.log'} or name.endswith(('.db-wal','.db-shm')): continue
        files.append(file)
with zipfile.ZipFile(destination/'riskpulse-ai-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(files): archive.write(file,Path('riskpulse-ai')/file.relative_to(ROOT))
for name in ['presentation.pdf','presentation.pptx','architecture.png','submission-audit.md','metrics-v1.json','metrics-v2.json','v2-final-report.md','technical-differentiators.md','jury-qa.md','live-pitch-script.md','demo-script.md']:
    shutil.copy2(ROOT/'docs'/name,destination/name)
shutil.copy2(ROOT/'README.md',destination/'README.md')
shutil.copy2(ROOT/'screenshots/v2-overview.png',destination/'dashboard.png')
with zipfile.ZipFile(destination/'riskpulse-ai-source.zip') as archive:
    assert not any('/node_modules/' in x or '/.models/' in x or '/.venv/' in x or x.endswith('/.env') for x in archive.namelist())
print(f'Packaged {len(files)} files. Source archive: {destination / "riskpulse-ai-source.zip"}')
