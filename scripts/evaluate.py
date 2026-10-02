"""Small synthetic holdout: descriptive diagnostics, not generalization claims."""
import json
import time
import sys
import os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('HF_HOME',str(Path(__file__).resolve().parents[1]/'.models'))
from backend.services.nlp import SentimentEngine,EventClassifier,entities,clean
from backend.services.finance import exposure,impact,stress
from backend import store

def evaluate():
    store.initialize(); model=SentimentEngine(); classifier=EventClassifier(); assets=store.all_rows('PortfolioAsset')
    records=store.all_rows('NewsItem')+store.all_rows('SocialPost')
    correct_event=correct_sentiment=0; latency=[]
    for r in records:
        t=time.perf_counter(); text=clean(r['text'])
        result={**r,**model.infer(text),**classifier.classify(text),**entities(text,assets)}
        mapped=exposure(result,assets); result.update(impact(result,mapped,text)); latency.append((time.perf_counter()-t)*1000)
        correct_event+=result['event_type']==r['expected_event']; correct_sentiment+=result['sentiment_label']==r['expected_sentiment']
    t=time.perf_counter()
    hero=records[3]; s={**hero,**model.infer(hero['text']),**classifier.classify(hero['text']),**entities(hero['text'],assets)}
    s.update(impact(s,exposure(s,assets),hero['text']))
    stress_result=stress(s,store.all_rows('StressScenario')[0],assets)
    elapsed=(time.perf_counter()-t)*1000
    out={'dataset':'24 synthetic records (12 paired news/social texts); not an independent benchmark','records_processed':len(records),
         'sentiment_mode':model.mode,'event_classification_accuracy':correct_event/len(records),'sentiment_label_agreement':correct_sentiment/len(records),
         'average_pipeline_latency_ms':sum(latency)/len(latency),'hero_analysis_and_stress_ms':elapsed,
         'hero_impact':s['impact_score'],'hero_portfolio_before':stress_result['portfolio_before'],
         'hero_portfolio_after':stress_result['portfolio_after'],'hero_loss':stress_result['absolute_loss'],
         'hero_loss_percentage':stress_result['loss_percentage'],'caveats':'Synthetic author-labelled examples share vocabulary with rules. Accuracy does not establish out-of-sample performance. Latency excludes model startup and includes repeated-text cache effects.'}
    t=time.perf_counter()
    for _ in range(100): stress(s,store.all_rows('StressScenario')[0],assets)
    out['average_stress_ms_100_runs']=(time.perf_counter()-t)*10
    (store.ROOT/'docs/metrics.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__': evaluate()
