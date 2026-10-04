import os
import time
import uuid
import threading
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Literal
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
os.environ.setdefault('HF_HOME',str(Path(__file__).resolve().parents[1]/'.models'))
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from backend import store
from backend.services.nlp import clean, SentimentEngine, EventClassifier, entities
from backend.services.finance import exposure, impact, stress, DEFAULT_WEIGHTS
from backend import v2
from backend.services.live_news import fetch_articles, status as live_status

sentiment = None
classifier = EventClassifier()
demo_lock=threading.RLock()
demo_cursor=0

class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3,max_length=12000)
    source_type: Literal['news','social'] = 'news'
    source: str = Field(default='Manual analyst input',max_length=200)
    headline: str = Field(default='',max_length=400)
    @field_validator('text')
    @classmethod
    def meaningful(cls,v):
        if len(clean(v))<3: raise ValueError('Text must contain at least three visible characters')
        return v

class StressRequest(BaseModel):
    signal_id: str
    scenario_id: str | None = None
    intensity: float = Field(default=1,ge=.1,le=2,allow_inf_nan=False)

def get_weights():
    custom=os.getenv('IMPACT_WEIGHTS')
    if custom:
        import json
        return json.loads(custom)
    return DEFAULT_WEIGHTS

def analyze(req, item_id=None, timestamp=None, source_url=None):
    with v2.lock:
        return _analyze(req,item_id,timestamp,source_url)

def _analyze(req, item_id=None, timestamp=None, source_url=None):
    started=time.perf_counter()
    text=clean(req.text)
    assets=store.all_rows('PortfolioAsset')
    signal={'id':item_id or str(uuid.uuid4()),'text':text,'headline':req.headline or text[:120],
            'source':req.source,'source_type':req.source_type,'timestamp':timestamp or datetime.now(timezone.utc).isoformat(),
            **sentiment.infer(text),**classifier.classify(text),**entities(text,assets)}
    if source_url:
        signal['source_url']=source_url
        signal['ingested_at']=datetime.now(timezone.utc).isoformat()
    mapped=exposure(signal,assets)
    signal.update(impact(signal,mapped,text,get_weights()))
    signal['exposure']={k:v for k,v in mapped.items() if k!='assets'}
    signal['confidence']=min(signal['sentiment_confidence'],signal['event_confidence'])
    signal['confidence_kind']='combined evidence strength, not calibrated probability'
    signal['stress_recommended']=signal['impact_score']>=8
    signal['inference_ms']=round((time.perf_counter()-started)*1000,3)
    store.save('RiskSignal',signal['id'],signal)
    if signal['stress_recommended']:
        scenario=next((s for s in store.all_rows('StressScenario') if s['event_type']==signal['event_type']),None)
        if scenario:
            result=stress(signal,scenario,assets)
            result.update(id='auto_'+signal['id'],automatic=True)
            store.save('StressTestResult',result['id'],result)
            signal['automatic_stress_id']=result['id']
            store.save('RiskSignal',signal['id'],signal)
    v2.record_observation(signal)
    return signal

def demo_items():
    return [item for pair in zip(store.all_rows('NewsItem'),store.all_rows('SocialPost')) for item in pair]
    if signal['stress_recommended']:
        scenario=next((s for s in store.all_rows('StressScenario') if s['event_type']==signal['event_type']),None)
        if scenario:
            result=stress(signal,scenario,assets)
            result['id']='auto_'+signal['id']; result['automatic']=True
            store.save('StressTestResult',result['id'],result)
            signal['automatic_stress_id']=result['id']
            store.save('RiskSignal',signal['id'],signal)
    return signal

def demo_items():
    news=store.all_rows('NewsItem'); social=store.all_rows('SocialPost')
    return [item for pair in zip(news,social) for item in pair]

def next_demo():
    global demo_cursor
    with demo_lock:
        items=demo_items()
        if demo_cursor>=len(items): return {'complete':True,'message':'Replay complete. Reset to replay.'}
        if live_status.get('mode') != 'demo_fallback':
            live_status.update(mode='synthetic demo',provider=None,reason=None)
        item=items[demo_cursor]; demo_cursor+=1
        return analyze(AnalyzeRequest(**{k:item[k] for k in ['text','source_type','source','headline']}),item['id'],item['timestamp'])

@asynccontextmanager
async def lifespan(app):
    global sentiment,demo_cursor
    if not (store.ROOT/'data/news.csv').exists():
        from scripts.seed_data import seed
        seed()
    store.initialize()
    sentiment=SentimentEngine()
    # Warm the deterministic feed in bounded batches. Model load stays offline by default.
    sentiment.infer_many([item['text'] for item in demo_items()])
    with demo_lock:
        known={x['id'] for x in store.all_rows('RiskSignal')}
        demo_cursor=0
        for item in demo_items():
            if item['id'] not in known: break
            demo_cursor+=1
    if os.getenv('LIVE_NEWS_ON_STARTUP','1') == '1':
        live()
    elif not store.all_rows('RiskSignal'):
        for _ in range(6): next_demo()
    yield

app=FastAPI(title='RiskPulse AI',version='1.0.0',lifespan=lifespan)
app.include_router(v2.router)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://127.0.0.1:3000'],allow_methods=['GET','POST'],allow_headers=['Content-Type'])

@app.get('/api/health')
def health():
    signals=store.all_rows('RiskSignal')
    live_count=sum(s['id'].startswith('live_') for s in signals)
    demo_count=sum(s['id'].startswith(('news_','social_posts_')) for s in signals)
    return {'status':'ok','sentiment_mode':sentiment.mode,'model_error':sentiment.error,
            'data_mode':live_status.get('mode') or ('live_news' if live_count else 'synthetic demo'),
            'live_provider':live_status.get('provider'), 'live_error':live_status.get('reason'),
            'live_observations':live_count,'demo_observations':demo_count,'offline_ready':True}

@app.post('/api/analyze')
def analyze_api(req:AnalyzeRequest): return analyze(req)

@app.get('/api/risk-feed')
def risk_feed(): return sorted(store.all_rows('RiskSignal'),key=lambda r:r['timestamp'],reverse=True)

@app.get('/api/portfolio')
def portfolio():
    assets=store.all_rows('PortfolioAsset')
    return {'total_value':sum(a['value'] for a in assets),'currency':'INR','assets':assets,'designation':'Entirely synthetic wholesale-banking portfolio'}

@app.get('/api/portfolio/exposure')
def portfolio_exposure(signal_id:str|None=None):
    signals=store.all_rows('RiskSignal')
    if signal_id:
        signal=next((s for s in signals if s['id']==signal_id),None)
        if not signal: raise HTTPException(404,'Signal not found')
        return exposure(signal,store.all_rows('PortfolioAsset'))
    return [{'event_type':s['event_type'],**{k:v for k,v in exposure({'event_type':s['event_type'],'affected_sectors':sorted({a['sector'] for a in store.all_rows('PortfolioAsset')})},store.all_rows('PortfolioAsset')).items() if k!='assets'}} for s in store.all_rows('StressScenario')]

@app.get('/api/scenarios')
def scenarios(): return store.all_rows('StressScenario')

@app.post('/api/stress-test')
def stress_api(req:StressRequest):
    signal=next((s for s in store.all_rows('RiskSignal') if s['id']==req.signal_id),None)
    if not signal: raise HTTPException(404,'Signal not found')
    scenario=next((s for s in scenarios() if s['id']==(req.scenario_id or signal['event_type'].lower())),None)
    if not scenario: raise HTTPException(404,'Scenario not found; OTHER events have no scenario')
    if scenario['event_type']!=signal['event_type']: raise HTTPException(422,'Scenario must match signal event type')
    result=stress(signal,scenario,store.all_rows('PortfolioAsset'),req.intensity)
    result['id']=str(uuid.uuid4()); result['automatic']=False
    store.save('StressTestResult',result['id'],result)
    return result

@app.get('/api/stress-tests')
def results(): return store.all_rows('StressTestResult')

@app.get('/api/statistics')
def statistics():
    feed=risk_feed()
    return {'records_processed':len(feed),'high_impact_events':sum(s['impact_score']>=8 for s in feed),
            'negative_sentiment':sum(s['sentiment_score']<-.15 for s in feed),
            'average_impact':round(sum(s['impact_score'] for s in feed)/len(feed),2) if feed else 0,
            'average_inference_ms':round(sum(s['inference_ms'] for s in feed)/len(feed),3) if feed else 0,
            'trend':list(reversed(feed)),'model_mode':sentiment.mode,'demo_cursor':demo_cursor,'demo_total':len(demo_items())}

@app.post('/api/demo/next')
def advance(): return next_demo()

@app.post('/api/demo/reset')
def reset():
    global demo_cursor
    with demo_lock, v2.lock:
        live_status.clear()
        store.clear_demo(); demo_cursor=0
        for _ in range(6): next_demo()
    return {'status':'reset','records':6}

@app.post('/api/ingest/live')
def live():
    try:
        articles,provider=fetch_articles()
    except RuntimeError as exc:
        live_status.update(mode='demo_fallback',reason=str(exc),provider=None)
        return {'mode':'demo_fallback','reason':str(exc),'signal':next_demo()}
    with demo_lock, v2.lock:
        known={s['id'] for s in store.all_rows('RiskSignal')}
        unseen=[a for a in articles if a['id'] not in known]
        signals=[]
        live_status.update(mode='live_news',provider=provider,reason=None)
        sentiment.infer_many([a['text'] for a in unseen])
        for a in unseen:
            signals.append(analyze(AnalyzeRequest(text=a['text'],headline=a['headline'],source=a['source']),
                                   item_id=a['id'],timestamp=a['timestamp'],source_url=a['url']))
        return {'mode':'live_news','provider':provider,'social_mode':'synthetic local social posts',
                'signals':signals,'new_count':len(signals),'already_seen':len(articles)-len(unseen)}
