import os
os.environ['SENTIMENT_MODE']='fallback'
from pathlib import Path
os.environ['DATABASE_URL']=str(Path(__file__).resolve().parents[2]/'work/test.db')
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.nlp import clean,SentimentEngine,EventClassifier,entities
from backend.services.finance import exposure,impact,stress
from backend import store

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c: yield c

def test_sentiment():
    engine=SentimentEngine()
    assert engine.infer('Strong profit growth and record gains')['sentiment_score']>0
    assert engine.infer('Default crisis and severe losses')['sentiment_score']<0
    assert engine.infer('The report was published today')['sentiment_label']=='neutral'
    assert engine.infer('not strong')['sentiment_score']<0
    assert engine.infer('no losses')['sentiment_score']>0

def test_transformer_output_contract():
    engine=SentimentEngine()
    engine.pipeline=lambda *args,**kwargs:[{'label':'positive','score':.1},{'label':'negative','score':.8},{'label':'neutral','score':.1}]
    assert engine.infer('Transformer contract test')['sentiment_score']==-.7
    engine.pipeline=lambda *args,**kwargs:[ [{'label':'positive','score':.9},{'label':'negative','score':.05},{'label':'neutral','score':.05}] ]
    assert engine.infer('Nested output contract test')['sentiment_score']==.85

@pytest.mark.parametrize('text,event',[
 ('Sanctions and war cause a geopolitical shipping blockade','GEOPOLITICAL'),
 ('Central bank interest rate hike amid inflation','MACROECONOMIC'),
 ('Credit downgrade default after missed payment bankruptcy','CREDIT_EVENT'),
 ('The acquisition merger takeover is approved','MERGER_ACQUISITION'),
 ('New product launch introduces software platform','PRODUCT_LAUNCH'),
 ('A routine staff meeting takes place','OTHER')])
def test_event(text,event): assert EventClassifier().classify(text)['event_type']==event

def test_normalization(): assert clean('<p> news </p> https://example.com \n update')=='news update'

def test_entities(client):
    e=entities('Helios Energy oil supply in India',store.all_rows('PortfolioAsset'))
    assert 'Helios Energy' in e['companies'] and 'Energy' in e['affected_sectors'] and 'India' in e['countries']

def test_portfolio(client):
    p=client.get('/api/portfolio').json()
    assert p['total_value']==100000000
    assert len(p['assets'])==12
    assert len(set(a['asset_type'] for a in p['assets']))==5

def test_exposure(client):
    p=store.all_rows('PortfolioAsset')
    e=exposure({'event_type':'CREDIT_EVENT','companies':['Helios Energy'],'affected_sectors':['Energy']},p)
    assert e['direct_exposure']==28000000
    assert len(e['assets'])==4
    assert e['weighted_exposure']==28000000
    assert exposure({'event_type':'PRODUCT_LAUNCH'},p)['direct_exposure']==0

def test_impact(client):
    s={'event_type':'GEOPOLITICAL','sentiment_score':-.9,'companies':['Helios Energy'],'source_type':'news'}
    high=impact(s,{'weighted_exposure':50000000,'exposure_fraction':.5},'severe war')
    low=impact({**s,'sentiment_score':0,'companies':[]}, {'weighted_exposure':0,'exposure_fraction':0},'ordinary report')
    assert 8<=high['impact_score']<=10
    assert low['impact_score']<high['impact_score']
    assert high['impact_score']==round(1+sum(high['impact_components'].values()),2)
    with pytest.raises(ValueError): impact(s,{'weighted_exposure':0,'exposure_fraction':0},'',{'severity':1})

def test_stress_arithmetic():
    p=[{'asset_id':'test','issuer':'Test','sector':'Energy','asset_type':'Equity','value':1000,'duration':0,'sensitivities':{'GEOPOLITICAL':1}}]
    s={'event_type':'GEOPOLITICAL','impact_score':10,'companies':['Test']}
    r=stress(s,{'id':'test','shocks':{'Equity':-.1}},p)
    assert r['absolute_loss']==100 and r['portfolio_after']==900 and r['loss_percentage']==10
    assert stress(s,{'id':'test','shocks':{'Equity':.1}},p)['absolute_loss']==-100
    assert stress(s,{'id':'test','shocks':{'Equity':-.1}},p,2)['absolute_loss']==200

def test_bond_duration():
    p=[{'asset_id':'bond','issuer':'Test','sector':'Financials','asset_type':'Government Bond','value':1000,'duration':5,'sensitivities':{'MACROECONOMIC':1}}]
    r=stress({'event_type':'MACROECONOMIC','impact_score':10,'companies':['Test']},{'id':'macro','shocks':{},'rate_change':.02},p)
    assert r['absolute_loss']==100

def test_end_to_end(client):
    response=client.post('/api/analyze',json={'text':'Severe geopolitical war and sanctions blockade threatens Helios Energy oil supply. Crisis disruption losses in India.'})
    assert response.status_code==200
    signal=response.json()
    assert signal['event_type']=='GEOPOLITICAL' and signal['sentiment_score']<0
    assert signal['impact_score']>=8 and signal['automatic_stress_id']
    exp=client.get('/api/portfolio/exposure',params={'signal_id':signal['id']}).json()
    assert exp['direct_exposure']==28000000
    r=client.post('/api/stress-test',json={'signal_id':signal['id']}).json()
    assert r['portfolio_before']==100000000 and r['portfolio_after']<r['portfolio_before']
    assert r['absolute_loss']==round(sum(a['loss'] for a in r['assets']),2)
    assert r['absolute_loss']==round(sum(a['loss'] for a in r['sector_losses']),2)
    assert r['portfolio_after']+r['absolute_loss']==r['portfolio_before']
    assert client.get('/api/stress-tests').json()

@pytest.mark.parametrize('path',['health','risk-feed','portfolio','portfolio/exposure','scenarios','statistics'])
def test_get_endpoints(client,path): assert client.get('/api/'+path).status_code==200

def test_invalid_input(client):
    for text in ['','  ','<p></p>']:
        assert client.post('/api/analyze',json={'text':text}).status_code==422
    assert client.post('/api/analyze',json={'text':'some valid text','source_type':'invalid'}).status_code==422
    assert client.post('/api/stress-test',json={'signal_id':'missing'}).status_code==404
    assert client.post('/api/stress-test',json={'signal_id':'missing','intensity':3}).status_code==422
    s=client.post('/api/analyze',json={'text':'Strong new product launch software'}).json()
    assert client.post('/api/stress-test',json={'signal_id':s['id'],'scenario_id':'missing'}).status_code==404
    assert client.post('/api/stress-test',json={'signal_id':s['id'],'scenario_id':'geopolitical'}).status_code==422

def test_live_fallback(client,monkeypatch):
    monkeypatch.delenv('NEWS_API_KEY',raising=False)
    assert client.post('/api/ingest/live').json()['mode']=='demo_fallback'
    monkeypatch.setenv('NEWS_API_KEY','test-key')
    def fail(*args,**kwargs): raise RuntimeError('simulated outage')
    monkeypatch.setattr('backend.main.httpx.get',fail)
    assert client.post('/api/ingest/live').json()['mode']=='demo_fallback'

def test_demo_replay(client):
    client.post('/api/demo/reset')
    seen=[]
    for _ in range(18): seen.append(client.post('/api/demo/next').json())
    assert len(set(s['id'] for s in seen))==18
    assert {'news','social'}=={s['source_type'] for s in seen}
    assert client.post('/api/demo/next').json()['complete'] is True
    assert client.post('/api/demo/reset').status_code==200
