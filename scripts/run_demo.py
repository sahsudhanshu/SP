"""Reproducible V2 hero: seed fixtures, ingest, fuse, propagate, stress, what-if."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from scripts.seed_data import seed
from scripts.validate_data import read_fixtures,validate
seed()
assert validate(*read_fixtures())['invalid_records']==0
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=60) as client:
    def call(path,body=None):
        r=client.get(path) if body is None else client.post(path,json=body)
        r.raise_for_status();return r.json()
    call('/api/demo/reset',{})
    news=call('/api/demo/next',{})
    call('/api/demo/next',{})
    dashboard=call('/api/v2/dashboard')
    detail=dashboard['priority'];c=detail['cluster'];g=detail['graph']
    original=call('/api/stress-test',{'signal_id':news['id']})
    whatif=call('/api/v2/what-if',{'cluster_id':c['id'],'intensity':1.5})
    assert c['observation_count']==2 and c['distinct_evidence_count']==1
    assert abs(original['absolute_loss']-2817031.2)<.01 if call('/api/health')['sentiment_mode']=='finbert' else original['absolute_loss']>0
    assert len(g['risk_paths'])==12
    summary={'model':call('/api/health')['sentiment_mode'],'event':c['event_type'],'cluster_id':c['id'],
      'sources':c['source_count'],'distinct_texts':c['distinct_evidence_count'],'collapsed_copies':c['duplicate_count'],
      'impact':c['raw_impact'],'confidence':c['confidence'],'effective_risk':c['effective_risk'],'risk_level':c['risk_level'],
      'direct_exposure':g['exposure']['direct_exposure'],'weighted_exposure':g['exposure']['weighted_exposure'],
      'risk_paths':len(g['risk_paths']),'propagated_risk':g['total_propagated_risk'],
      'before':original['portfolio_before'],'after':original['portfolio_after'],'loss':original['absolute_loss'],
      'sector_losses':detail['result']['sector_losses'],'what_if_1_5x_loss':whatif['absolute_loss'],
      'summary':dashboard['summary'],'note':c['independence_note']}
    print(json.dumps(summary,indent=2))
    (Path(__file__).resolve().parents[1]/'docs/demo-results-v2.json').write_text(json.dumps(summary,indent=2))
