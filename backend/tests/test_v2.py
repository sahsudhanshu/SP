import math
import os
from pathlib import Path
# Keep this module safe when run on its own, without the V1 test module.
os.environ['SENTIMENT_MODE'] = 'fallback'
os.environ['LIVE_NEWS_ON_STARTUP'] = '0'
os.environ['DATABASE_URL'] = str(Path(__file__).resolve().parents[2] / 'work/test.db')
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend import store,v2
from backend.services.intelligence import canonical,cluster_signals,configuration,recency,reliability,risk_level,clock_for,executive_summary
from backend.services.propagation import propagate,heatmap,explain
from backend.services.scenario_analysis import calculate,compare
from backend.services.nlp import SentimentEngine,EventClassifier
from scripts.validate_data import validate,read_fixtures

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as client: yield client

def signal(**kwargs):
    return {'id':'news_a','text':'Severe geopolitical war blockade threatens Helios Energy oil supply','headline':'Oil supply shock',
            'event_type':'GEOPOLITICAL','companies':['Helios Energy'],'affected_sectors':['Energy'],
            'timestamp':'2026-10-01T09:00:00+00:00','source_type':'news','source':'Publisher A',
            'sentiment_score':-.8,'sentiment_confidence':.95,'event_confidence':.95,'impact_score':9.5,**kwargs}

def fused(**kwargs): return cluster_signals([signal(**kwargs)])[0]

def test_canonical_copy(): assert canonical('Investor discussion: War & oil! #markets')==canonical('War & oil!')
def test_duplicate_id_not_double_counted(): assert fused()['observation_count']==cluster_signals([signal(),signal()])[0]['observation_count']==1
def test_copy_no_confidence_boost():
    a=signal();b=signal(id='social_posts_a',source='Social',source_type='social',text='Investor discussion: '+a['text']+' #markets')
    c=cluster_signals([a,b])[0]
    assert c['source_count']==2 and c['duplicate_count']==1 and c['distinct_evidence_count']==1
    assert c['confidence']==fused()['confidence'] and c['raw_impact']==9.5
def test_separate_entities(): assert len(cluster_signals([signal(),signal(id='news_b',companies=['Atlas Industrials'])]))==2
def test_separate_event_types(): assert len(cluster_signals([signal(),signal(id='news_b',event_type='CREDIT_EVENT')]))==2
def test_cluster_time_window(): assert len(cluster_signals([signal(),signal(id='news_b',timestamp='2026-10-05T00:00:00+00:00')]))==2
def test_similar_wording_fuses():
    assert len(cluster_signals([signal(),signal(id='news_b',text='Geopolitical war blockade threatens Helios Energy oil supply amid severe losses')]))==1
def test_source_weights():
    c=configuration(); assert reliability(signal(),c)==.9 and reliability(signal(source_type='social'),c)==.6
    c['source_overrides']['Publisher A']=.95;assert reliability(signal(),c)==.95
def test_recency_half_life(): assert recency('2026-10-01T00:00:00Z','2026-10-02T00:00:00Z',24)==pytest.approx(.5)
def test_recency_future_clamp(): assert recency('2026-10-02T00:00:00Z','2026-10-01T00:00:00Z',24)==1
def test_recency_invalid():
    with pytest.raises(ValueError): recency('2026-10-01T00:00:00Z','2026-10-02T00:00:00Z',0)
def test_demo_clock_deterministic(): assert clock_for([signal()])[0]==signal()['timestamp']
def test_confidence_changes_priority(): assert fused(sentiment_confidence=.3)['effective_risk']<fused()['effective_risk']
@pytest.mark.parametrize('value,expected',[(2.99,'LOW'),(3,'MEDIUM'),(6,'HIGH'),(8,'CRITICAL')])
def test_threshold_boundaries(value,expected): assert risk_level(value,configuration())==expected
def test_disagreement_reduces_confidence():
    b=signal(id='news_b',source='B',text=signal()['text']+' improving outlook',sentiment_score=.8)
    assert cluster_signals([signal(),b])[0]['confidence']<fused()['confidence']
def test_propagation_reconciles(client):
    g=propagate(fused(),store.all_rows('PortfolioAsset'));assert len(g['risk_paths'])==12
    assert len({p['asset_id'] for p in g['risk_paths']})==12
    assert sum(p['weighted_exposure'] for p in g['risk_paths'])==g['exposure']['weighted_exposure']
    for p in g['risk_paths']: assert p['propagated_risk']==pytest.approx(fused()['effective_risk']*math.prod(p['weights']),abs=1e-6)
def test_graph_edges_exist(client):
    g=propagate(fused(),store.all_rows('PortfolioAsset'));ids={n['id'] for n in g['nodes']}
    assert all(e['source'] in ids and e['target'] in ids and 0<=e['weight']<=1 for e in g['edges'])
def test_no_exposure_path(client): assert not propagate(fused(event_type='PRODUCT_LAUNCH',companies=[],affected_sectors=[]),store.all_rows('PortfolioAsset'))['risk_paths']
def test_scenario_comparison(client):
    r=compare(fused(),store.all_rows('StressScenario')[0],store.all_rows('PortfolioAsset'))
    assert r[0]['absolute_loss']==0 and r[0]['portfolio_after']==100000000
    assert 0<r[1]['absolute_loss']<r[2]['absolute_loss']
def test_counterfactual_zero_exposure(client): assert calculate(fused(),store.all_rows('StressScenario')[0],store.all_rows('PortfolioAsset'),exposure_scale=0)['absolute_loss']==0
def test_counterfactual_impact_monotonic(client):
    args=(fused(),store.all_rows('StressScenario')[0],store.all_rows('PortfolioAsset'))
    assert calculate(*args,impact=5)['absolute_loss']<calculate(*args,impact=9)['absolute_loss']
def test_rate_and_equity_counterfactual(client):
    args=(fused(),store.all_rows('StressScenario')[0],store.all_rows('PortfolioAsset'))
    assert calculate(*args,rate_shock=.02)['absolute_loss']>calculate(*args)['absolute_loss']
    assert calculate(*args,equity_shock=-.3)['absolute_loss']>calculate(*args)['absolute_loss']
def test_attribution_sum(client):
    r=calculate(fused(),store.all_rows('StressScenario')[0],store.all_rows('PortfolioAsset'))
    assert r['absolute_loss']==round(sum(a['loss'] for a in r['assets']),2)==round(sum(a['loss'] for a in r['sector_losses']),2)
    assert r['portfolio_after']+r['absolute_loss']==r['portfolio_before']
def test_heatmap_value_weighting(client):
    h=heatmap(store.all_rows('PortfolioAsset'));cell=next(c for c in h['cells'] if c['sector']=='Energy' and c['event']=='GEOPOLITICAL')
    assert cell['score']==8.5 and cell['sensitivity_weighted_exposure']==23800000
def test_executive_summary():
    assert 'No signals' in executive_summary([])
    assert '1 high or critical' in executive_summary([fused()])
def test_batch_contract_and_cache():
    m=SentimentEngine();calls=[]
    def model(texts,**kwargs):
        calls.append(texts);return [[{'label':'positive','score':.8},{'label':'negative','score':.1},{'label':'neutral','score':.1}] for t in texts]
    m.pipeline=model
    out=m.infer_many(['strong profit','strong profit','growth'])
    assert len(calls)==1 and len(calls[0])==2 and out[0]['sentiment_score']==.7
    assert m.infer('strong profit')==out[0] and len(calls)==1
def test_classifier_evidence():
    c=EventClassifier().classify('War blockade sanctions oil supply')
    assert c['semantic_similarity']>0 and c['classification_evidence'] and 'TF-IDF' in c['classification_explanation']
def test_quality_clean_data():
    q=validate(*read_fixtures());assert q['source_records']==24 and q['duplicates']==12 and q['invalid_records']==0
def test_quality_invalid_data():
    records,assets,scenarios=deepcopy(read_fixtures());records[0]['text']='';records[1]['timestamp']='bad';assets[0]['value']=-1;scenarios[0]['shocks']['Equity']=-2
    q=validate(records,assets,scenarios);assert q['missing_fields']==1 and q['invalid_records']==4
def test_v2_api_hero_and_history(client):
    client.post('/api/demo/reset');client.post('/api/demo/next');client.post('/api/demo/next')
    d=client.get('/api/v2/dashboard').json();c=d['priority']['cluster'];cid=c['id']
    assert c['event_type']=='GEOPOLITICAL' and c['observation_count']==2 and c['duplicate_count']==1
    assert d['observation_count']==8 and len(d['history'])==8
    assert 'high-risk threshold crossed' in d['history'][6]['transitions']
    for route in ['clusters','history','alerts','heatmap','evaluation','configuration',f'clusters/{cid}',f'propagation/{cid}',f'scenarios/{cid}',f'audit/{cid}']:
        assert client.get('/api/v2/'+route).status_code==200
    assert client.post('/api/v2/what-if',json={'cluster_id':cid,'intensity':0}).json()['absolute_loss']==0
    assert len(client.get('/api/v2/history').json())==8  # reads never append snapshots
    s=store.all_rows('RiskSignal')[-1];v2.record_observation(s);assert len(store.all_rows('RiskHistory'))==8
def test_v2_invalid_api(client):
    assert client.get('/api/v2/clusters/missing').status_code==404
    assert client.get('/api/v2/alerts?level=INVALID').status_code==422
    assert client.post('/api/v2/what-if',json={'cluster_id':'missing','intensity':4}).status_code==422
    assert client.post('/api/v2/what-if',json={'cluster_id':'missing'}).status_code==404
