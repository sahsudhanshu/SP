"""Local, reusable NLP components. Every score records its provenance."""
import os
import re
import math
import threading
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CATEGORIES = {
    'GEOPOLITICAL': 'war conflict sanctions invasion military blockade geopolitical tensions oil supply disruption missile shipping border',
    'MACROECONOMIC': 'inflation central bank interest rate recession monetary policy GDP unemployment rate hike economic growth',
    'CREDIT_EVENT': 'default downgrade debt bankruptcy insolvency missed payment credit liquidity covenant restructuring',
    'MERGER_ACQUISITION': 'merger acquisition takeover acquire buyout consolidation combined company regulatory approval deal',
    'PRODUCT_LAUNCH': 'product launch launches release introduces platform innovation software new service device rollout',
}
KEYWORDS = {k: v.split() for k, v in CATEGORIES.items()}
PHRASES = {'GEOPOLITICAL': ['geopolitical','sanctions','blockade','war','missile','invasion'],
           'MACROECONOMIC': ['interest rate','inflation','central bank','recession','gdp','rate hike'],
           'CREDIT_EVENT': ['default','downgrade','bankruptcy','missed payment','insolvency'],
           'MERGER_ACQUISITION': ['merger','acquisition','takeover','buyout','acquire'],
           'PRODUCT_LAUNCH': ['launch','introduces','rollout','new product','release']}
SECTOR_TERMS = {'Energy':['oil','energy','gas','petroleum','fuel'],
                'Technology':['technology','software','chip','platform','device'],
                'Financials':['bank','banking','credit','insurance','financial'],
                'Healthcare':['healthcare','hospital','pharma','medicine','drug'],
                'Consumer':['retail','consumer','sales','stores'],
                'Industrials':['industrial','manufacturing','shipping','factory']}
POS = {'profit':1,'profits':1,'growth':.8,'gain':1,'gains':1,'surged':.9,'record':.7,'strong':.7,'approved':.6,'improved':.9,'increase':.5,'successful':.9,'beat':.9,'rally':1,'positive':.8,'expands':.6}
NEG = {'loss':-1,'losses':-1,'default':-1.8,'downgrade':-1.2,'war':-1.5,'blockade':-1.5,'crisis':-1.3,'collapse':-1.4,'disruption':-1,'sanctions':-1.1,'negative':-.8,'decline':-1,'fell':-.9,'recession':-1.2,'bankruptcy':-1.8,'missed':-.6,'severe':-.8,'threatens':-.9,'risk':-.4,'cuts':-.6,'weak':-.8,'inflation':-.5}

def clean(text):
    return re.sub(r'\s+', ' ', re.sub(r'https?://\S+|<[^>]+>', ' ', text)).strip()

class SentimentEngine:
    def __init__(self):
        self.pipeline = None
        self.error = None
        self.lock = threading.Lock()
        self.batch_cache = {}
        self.mode = 'lexicon_fallback'
        if os.getenv('SENTIMENT_MODE', 'auto') != 'fallback':
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
                name = os.getenv('MODEL_NAME', 'ProsusAI/finbert')
                local = os.getenv('ALLOW_MODEL_DOWNLOAD', '0') != '1'
                tokenizer = AutoTokenizer.from_pretrained(name, local_files_only=local)
                model = AutoModelForSequenceClassification.from_pretrained(name, local_files_only=local)
                self.pipeline = pipeline('text-classification', model=model, tokenizer=tokenizer, device=-1)
                self.mode = 'finbert'
            except Exception as exc:
                self.error = str(exc)[:400]

    @lru_cache(maxsize=512)
    def infer(self, text):
        text = clean(text)
        if text in self.batch_cache: return dict(self.batch_cache[text])
        if self.pipeline:
            with self.lock:
                probabilities = self.pipeline(text, truncation=True, max_length=512, top_k=None)
            if probabilities and isinstance(probabilities[0],list): probabilities=probabilities[0]
            scores = {x['label'].lower():x['score'] for x in probabilities}
            label = max(scores, key=scores.get)
            return {'sentiment_label':label, 'sentiment_score':round(scores.get('positive',0)-scores.get('negative',0),4),
                    'sentiment_confidence':round(scores[label],4), 'sentiment_method':'FinBERT transformer', 'sentiment_confidence_kind':'model probability'}
        tokens = re.findall(r'[a-z]+', text.lower())
        total = 0
        hits = 0
        for i, token in enumerate(tokens):
            value = POS.get(token, NEG.get(token,0))
            if value:
                if any(t in {'not','no','never','without'} for t in tokens[max(0,i-3):i]): value *= -1
                total += value
                hits += 1
        score = math.tanh(total/2.5)
        return {'sentiment_label':'positive' if score>.15 else 'negative' if score<-.15 else 'neutral',
                'sentiment_score':round(score,4), 'sentiment_confidence':round(min(.8,.45+.06*hits),4),
                'sentiment_method':'weighted financial lexicon fallback', 'sentiment_confidence_kind':'heuristic evidence strength; not probability'}

    def infer_many(self, texts, batch_size=8):
        """Unique normalized texts in bounded batches; warm cache reused by ingestion."""
        texts = [clean(t) for t in texts]
        missing = list(dict.fromkeys(t for t in texts if t not in self.batch_cache))
        if self.pipeline and missing:
            with self.lock:
                outputs = self.pipeline(missing, truncation=True, max_length=512, top_k=None, batch_size=batch_size)
            for text, probabilities in zip(missing, outputs):
                scores = {x['label'].lower():x['score'] for x in probabilities}
                label = max(scores,key=scores.get)
                self.batch_cache[text] = {'sentiment_label':label,'sentiment_score':round(scores.get('positive',0)-scores.get('negative',0),4),
                    'sentiment_confidence':round(scores[label],4),'sentiment_method':'FinBERT transformer','sentiment_confidence_kind':'model probability'}
        else:
            for text in missing: self.batch_cache[text] = self.infer(text)
        result = [dict(self.batch_cache[t]) for t in texts]
        while len(self.batch_cache)>512: self.batch_cache.pop(next(iter(self.batch_cache)))
        return result

class EventClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)
        self.labels = list(CATEGORIES)
        self.reference = self.vectorizer.fit_transform(CATEGORIES.values())

    def classify(self, text):
        text = text.lower()
        sims = cosine_similarity(self.vectorizer.transform([text]), self.reference)[0]
        rules = [sum(bool(re.search(r'\b'+re.escape(p)+r'\w*\b',text)) for p in PHRASES[k]) for k in self.labels]
        scores = [float(s)+min(.8,.22*r) for s,r in zip(sims,rules)]
        i = max(range(len(scores)), key=scores.__getitem__)
        diagnostics = {'semantic_similarity':round(float(sims[i]),4),
                       'similarity_scores':{label:round(float(s),4) for label,s in zip(self.labels,sims)},
                       'classification_explanation':f'TF-IDF cosine {sims[i]:.3f}; {rules[i]} phrase matches; combined evidence {scores[i]:.3f}. Confidence is heuristic, not calibrated.'}
        if scores[i] < .08: return {'event_type':'OTHER','event_confidence':.25,'event_method':'TF-IDF similarity + weighted rules','classification_evidence':[],**diagnostics}
        return {'event_type':self.labels[i],'event_confidence':round(min(.95,.4+scores[i]*.5),4),
                'event_method':'TF-IDF similarity + weighted rules',
                'classification_evidence':[p for p in PHRASES[self.labels[i]] if p in text],**diagnostics}

def entities(text, portfolio):
    low = text.lower()
    issuers = sorted({a['issuer'] for a in portfolio if a['issuer'].lower() in low})
    sectors = sorted({s for s,terms in SECTOR_TERMS.items() if any(re.search(r'\b'+re.escape(t)+r'\w*\b',low) for t in terms)} | {a['sector'] for a in portfolio if a['issuer'] in issuers})
    countries = [c for c in ['India','China','United States','Russia','Ukraine','Iran'] if c.lower() in low]
    instruments = [t for t in ['bonds','loans','equities','derivatives'] if t in low]
    return {'entities':issuers+countries+instruments,'companies':issuers,'countries':countries,'affected_sectors':sectors,'entity_method':'portfolio issuer dictionary + sector/instrument/country rules'}
