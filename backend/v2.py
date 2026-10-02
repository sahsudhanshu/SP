"""Additive API: V1 observation contracts remain unchanged."""
import json
import threading
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend import store
from backend.services.intelligence import cluster_signals, clock_for, configuration, executive_summary
from backend.services.propagation import propagate, heatmap, explain
from backend.services.scenario_analysis import calculate, compare
from backend.services.finance import exposure

router = APIRouter(prefix='/api/v2', tags=['V2 intelligence'])
lock = threading.RLock()

def state():
    with lock:
        signals = store.all_rows('RiskSignal')
        as_of, clock = clock_for(signals)
        return cluster_signals(signals, as_of=as_of), store.all_rows('PortfolioAsset'), as_of, clock

def find(cid):
    clusters, assets, _, _ = state()
    c = next((c for c in clusters if c['id'] == cid), None)
    if c is None: raise HTTPException(404, 'Event cluster not found; it may have been cleared by reset')
    return c, assets

def scenario_for(c):
    return next((s for s in store.all_rows('StressScenario') if s['event_type'] == c['event_type']), None)

def detail(c, assets):
    scenario = scenario_for(c)
    result = calculate(c, scenario, assets) if scenario else None
    graph = propagate(c, assets, result)
    return {'cluster': c, 'graph': graph, 'result': result, 'explanation': explain(c, graph, result),
            'comparison': compare(c, scenario, assets) if scenario else [], 'configuration': configuration()}

def record_observation(signal):
    """Persist arrival snapshots, not chart points invented at read time."""
    with lock:
        history = store.all_rows('RiskHistory')
        if any(h['signal_id'] == signal['id'] for h in history): return
        clusters, assets, as_of, clock = state()
        c = next(c for c in clusters if signal['id'] in c['member_ids'])
        previous = next((h for h in reversed(history) if h['cluster_id'] == c['id']), None)
        d = detail(c, assets)
        transitions = ['signal appears' if previous is None else 'related observation received']
        if previous and c['effective_risk'] > previous['event_risk'] + .001: transitions.append('signal strengthens')
        if c['effective_risk'] >= 6 and (previous is None or previous['event_risk'] < 6): transitions.append('high-risk threshold crossed')
        if signal.get('automatic_stress_id'): transitions.append('V1 raw-impact stress triggered')
        row = {'id': 'history_' + signal['id'], 'signal_id': signal['id'], 'cluster_id': c['id'],
               'sequence': len(history)+1, 'timestamp': as_of, 'recorded_at': datetime.now(timezone.utc).isoformat(),
               'clock': clock, 'headline': signal['headline'], 'event_type': c['event_type'],
               'sentiment': c['sentiment_score'], 'impact': c['raw_impact'], 'event_risk': c['effective_risk'],
               'risk_level': c['risk_level'], 'source_count': c['source_count'], 'sectors': c['affected_sectors'],
               'risk_score': max((x['effective_risk'] for x in clusters), default=0),
               'high_impact_events': sum(x['raw_impact'] >= 8 for x in clusters),
               'portfolio_loss': d['result']['absolute_loss'] if d['result'] else 0,
               'transitions': transitions}
        store.save('RiskHistory', row['id'], row)

@router.get('/dashboard')
def dashboard():
    clusters, assets, as_of, clock = state()
    summary = [{k:v for k,v in c.items() if k != 'members'} | {'weighted_exposure': exposure(c,assets)['weighted_exposure']} for c in clusters]
    selected = detail(clusters[0], assets) if clusters else None
    return {'clusters': summary, 'portfolio_value': sum(a['value'] for a in assets), 'assets': assets,
            'current_risk': max((c['effective_risk'] for c in clusters), default=0),
            'high_impact_events': sum(c['raw_impact'] >= 8 for c in clusters),
            'observation_count': sum(c['observation_count'] for c in clusters),
            'summary': executive_summary(clusters), 'priority': selected, 'as_of': as_of, 'clock': clock,
            'heatmap': heatmap(assets), 'history': store.all_rows('RiskHistory'),
            'recent_tests': store.all_rows('StressTestResult')[-6:][::-1], 'config': configuration()}

@router.get('/clusters')
def clusters_api(): return state()[0]

@router.get('/clusters/{cid}')
def cluster_api(cid: str): return detail(*find(cid))

@router.get('/propagation/{cid}')
def graph_api(cid: str): return detail(*find(cid))['graph']

@router.get('/scenarios/{cid}')
def comparison_api(cid: str): return detail(*find(cid))['comparison']

class WhatIf(BaseModel):
    cluster_id: str
    impact: float | None = Field(default=None, ge=0, le=10, allow_inf_nan=False)
    intensity: float = Field(default=1, ge=0, le=3, allow_inf_nan=False)
    exposure_scale: float = Field(default=1, ge=0, le=2, allow_inf_nan=False)
    rate_shock: float | None = Field(default=None, ge=-.1, le=.1, allow_inf_nan=False)
    equity_shock: float | None = Field(default=None, ge=-1, le=1, allow_inf_nan=False)

@router.post('/what-if')
def what_if(req: WhatIf):
    c, assets = find(req.cluster_id)
    scenario = scenario_for(c)
    if not scenario: raise HTTPException(422, 'No scenario for OTHER events')
    return calculate(c, scenario, assets, req.intensity, req.impact, req.exposure_scale, req.rate_shock, req.equity_shock)

@router.get('/history')
def history_api(): return store.all_rows('RiskHistory')

@router.get('/alerts')
def alerts_api(level: str = 'ALL'):
    if level not in ['ALL','LOW','MEDIUM','HIGH','CRITICAL']: raise HTTPException(422, 'Unknown alert level')
    cs, assets, _, _ = state()
    return [{k:c[k] for k in ['id','headline','risk_level','effective_risk','raw_impact','confidence','source_count','affected_sectors','timestamp']} |
            {'weighted_exposure': propagate(c,assets)['exposure']['weighted_exposure']} for c in cs if level == 'ALL' or c['risk_level'] == level]

@router.get('/heatmap')
def heatmap_api(): return heatmap(store.all_rows('PortfolioAsset'))

@router.get('/audit/{cid}')
def audit_api(cid: str): return {**detail(*find(cid)), 'configuration': configuration()}

@router.get('/evaluation')
def evaluation_api():
    def read(name):
        p = store.ROOT/'docs'/name
        return json.loads(p.read_text()) if p.exists() else None
    return {'baseline': read('metrics-v1.json'), 'current': read('metrics-v2.json'),
            'note': 'Small synthetic author-labelled dataset. Agreement is not independent validation. Latencies exclude model load.'}

@router.get('/configuration')
def config_api(): return configuration()
