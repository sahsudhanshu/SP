import csv
import json
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.getenv('DATABASE_URL',str(ROOT/'backend/database/riskpulse.db')))
if not DB.is_absolute(): DB=ROOT/DB

@contextmanager
def connection():
    DB.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB,timeout=30)
    con.row_factory=sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally: con.close()

def initialize():
    with connection() as db:
        for name in ['NewsItem','SocialPost','RiskSignal','PortfolioAsset','StressScenario','StressTestResult','RiskHistory']:
            db.execute(f'CREATE TABLE IF NOT EXISTS {name} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    for file,table in [('news.csv','NewsItem'),('social_posts.csv','SocialPost')]:
        with (ROOT/'data'/file).open(encoding='utf8') as f:
            for row in csv.DictReader(f): save(table,row['id'],row)
    with (ROOT/'data/portfolio.csv').open(encoding='utf8') as f:
        for row in csv.DictReader(f):
            row['value']=float(row['value']); row['duration']=float(row['duration']); row['sensitivities']=json.loads(row['sensitivities'])
            save('PortfolioAsset',row['asset_id'],row)
    for row in json.loads((ROOT/'data/scenarios.json').read_text()): save('StressScenario',row['id'],row)

TABLES={'NewsItem','SocialPost','RiskSignal','PortfolioAsset','StressScenario','StressTestResult','RiskHistory'}
def save(table,id,payload):
    assert table in TABLES
    with connection() as db: db.execute(f'INSERT OR REPLACE INTO {table} VALUES (?,?)',(id,json.dumps(payload)))

def all_rows(table):
    assert table in TABLES
    with connection() as db: return [json.loads(r['payload']) for r in db.execute(f'SELECT payload FROM {table} ORDER BY rowid')]

def clear_demo():
    with connection() as db:
        db.execute('DELETE FROM RiskSignal'); db.execute('DELETE FROM StressTestResult')
        db.execute('DELETE FROM RiskHistory')
