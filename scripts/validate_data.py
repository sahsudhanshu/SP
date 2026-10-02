"""Validate source fixtures and financial assumptions without mutating data."""
import csv
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import store
from backend.services.intelligence import canonical, timestamp
from backend.services.nlp import entities, CATEGORIES

def validate(records, assets, scenarios):
    report = {'records_checked': len(records)+len(assets)+len(scenarios), 'source_records': len(records),
              'duplicates': 0, 'missing_fields': 0, 'invalid_records': 0, 'unknown_entity_records': 0, 'issues': []}
    ids, texts = set(), set()
    for r in records:
        reasons = []
        for key in ['id','text','timestamp','source','source_type']:
            if not str(r.get(key,'')).strip(): report['missing_fields'] += 1; reasons.append('missing '+key)
        try: timestamp(r.get('timestamp',''))
        except (ValueError, AttributeError): reasons.append('invalid or timezone-less timestamp')
        if r.get('source_type') not in ['news','social']: reasons.append('invalid source type')
        key = canonical(r.get('text',''))
        if r.get('id') in ids: reasons.append('duplicate identifier')
        if key in texts: report['duplicates'] += 1
        ids.add(r.get('id')); texts.add(key)
        if not entities(r.get('text',''),assets)['companies']: report['unknown_entity_records'] += 1
        if reasons: report['invalid_records'] += 1; report['issues'].append({'id':r.get('id'),'errors':reasons})
    asset_ids=set()
    for a in assets:
        try:
            assert a['asset_id'] not in asset_ids
            assert a['issuer'] and a['sector']
            assert a['asset_type'] in ['Equity','Corporate Loan','Corporate Bond','Government Bond','Derivative']
            assert math.isfinite(a['value']) and a['value']>0
            assert math.isfinite(a['duration']) and a['duration']>=0
            assert set(CATEGORIES).issubset(a['sensitivities'])
            assert all(math.isfinite(v) and 0<=v<=1 for v in a['sensitivities'].values())
            asset_ids.add(a['asset_id'])
        except (KeyError,TypeError,AssertionError):
            report['invalid_records']+=1; report['issues'].append({'id':a.get('asset_id'),'errors':['invalid portfolio position']})
    scenario_ids=set()
    for s in scenarios:
        try:
            assert s['id'] not in scenario_ids and s['event_type'] in CATEGORIES
            assert set(s['shocks']) == {'Equity','Corporate Loan','Corporate Bond','Government Bond','Derivative'}
            assert all(math.isfinite(v) and -1<=v<=1 for v in s['shocks'].values())
            assert math.isfinite(s.get('rate_change',0)) and abs(s.get('rate_change',0))<=.1
            scenario_ids.add(s['id'])
        except (KeyError,TypeError,AssertionError):
            report['invalid_records']+=1; report['issues'].append({'id':s.get('id'),'errors':['invalid scenario']})
    report['notes'] = 'Normalized cross-source copies are expected and collapsed by fusion. Unknown issuer means no portfolio dictionary match, not necessarily a bad record.'
    return report

def read_fixtures():
    records=[]
    for name in ['news.csv','social_posts.csv']:
        with (store.ROOT/'data'/name).open(encoding='utf8') as f: records.extend(csv.DictReader(f))
    with (store.ROOT/'data/portfolio.csv').open(encoding='utf8') as f:
        assets=list(csv.DictReader(f))
    for a in assets:
        a['value']=float(a['value']);a['duration']=float(a['duration']);a['sensitivities']=json.loads(a['sensitivities'])
    return records,assets,json.loads((store.ROOT/'data/scenarios.json').read_text())

if __name__=='__main__':
    report=validate(*read_fixtures());print(json.dumps(report,indent=2))
    (store.ROOT/'docs/data-quality.json').write_text(json.dumps(report,indent=2))
    sys.exit(bool(report['invalid_records']))

