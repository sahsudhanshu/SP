"""Actual cold-result-cache and batched CPU measurements; same model, texts, three rounds."""
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('HF_HOME',str(ROOT/'.models'))
from backend.services.nlp import SentimentEngine,EventClassifier,entities,clean
from backend.services.finance import exposure,impact,stress
from backend.services.intelligence import cluster_signals,clock_for
from backend.services.propagation import propagate
from scripts.validate_data import read_fixtures

def evaluate():
    records,assets,scenarios=read_fixtures();model=SentimentEngine();classifier=EventClassifier()
    texts=[clean(r['text']) for r in records]
    model.infer(texts[0])  # exclude initial kernel setup and model loading in both arms
    sequential=[];batched=[];seq_output=[];batch_output=[]
    for round in range(3):
        for kind in (['sequential','batch'] if round%2==0 else ['batch','sequential']):
            model.infer.cache_clear();model.batch_cache.clear();t=time.perf_counter()
            if kind=='sequential': seq_output=[model.infer(t) for t in texts]; sequential.append((time.perf_counter()-t)*1000/len(texts))
            else: batch_output=model.infer_many(texts,8);batched.append((time.perf_counter()-t)*1000/len(texts))
    model.infer.cache_clear();model.batch_cache.clear()
    started=time.perf_counter();outputs=model.infer_many(texts,8);signals=[]
    for r,o in zip(records,outputs):
        s={**r,**o,**classifier.classify(r['text']),**entities(r['text'],assets)}
        s.update(impact(s,exposure(s,assets),s['text']));signals.append(s)
    pipeline_ms=(time.perf_counter()-started)*1000/len(records)
    t=time.perf_counter();model.infer_many(texts,8);warm=(time.perf_counter()-t)*1000/len(texts)
    as_of,_=clock_for(signals);t=time.perf_counter();clusters=cluster_signals(signals,as_of=as_of)
    for c in clusters: propagate(c,assets)
    fusion_ms=(time.perf_counter()-t)*1000
    hero=next(s for s in signals if s['id']=='news_03');scenario=next(s for s in scenarios if s['event_type']==hero['event_type'])
    result=stress(hero,scenario,assets);t=time.perf_counter()
    for _ in range(100): stress(hero,scenario,assets)
    stress_ms=(time.perf_counter()-t)*10
    out={'dataset':'24 synthetic author-labelled records; 12 correlated news/social pairs', 'records_processed':len(records),
         'sentiment_mode':model.mode,'event_classification_accuracy':sum(s['event_type']==r['expected_event'] for s,r in zip(signals,records))/len(records),
         'sentiment_label_agreement':sum(s['sentiment_label']==r['expected_sentiment'] for s,r in zip(signals,records))/len(records),
         'average_pipeline_latency_ms':pipeline_ms,'average_stress_ms_100_runs':stress_ms,
         'fusion_and_propagation_total_ms':fusion_ms,'clusters':len(clusters),
         'hero_loss':result['absolute_loss'],'hero_portfolio_after':result['portfolio_after'],
         'benchmark':{'environment':platform.platform(),'python':platform.python_version(),'model':model.mode,'device':'CPU','rounds':3,'batch_size':8,
                      'sequential_ms_per_record':sequential,'batched_ms_per_record':batched,
                      'sequential_median_ms':statistics.median(sequential),'batched_median_ms':statistics.median(batched),
                      'warm_cache_ms_per_record':warm,'labels_identical':all(a['sentiment_label']==b['sentiment_label'] for a,b in zip(seq_output,batch_output)),
                      'max_score_difference':max(abs(a['sentiment_score']-b['sentiment_score']) for a,b in zip(seq_output,batch_output))},
         'caveats':'Small synthetic examples share rule vocabulary; no independent validation. Historical V1 timing is not a controlled comparison. Controlled arms alternate order, clear result caches and exclude model loading; batching may be slower on this CPU. Current pipeline includes batched NLP/entity/impact, excludes SQLite, HTTP and V2 fusion. Stress timing excludes SQLite; V1 stress timing included a scenario read. Fusion/graph total reported separately.'}
    (ROOT/'docs/metrics-v2.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__': evaluate()
