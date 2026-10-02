"""Transparent clustering and evidence fusion. Confidence is not a probability of loss."""
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.services.nlp import clean

CONFIG = Path(__file__).resolve().parents[2] / 'data/risk_config.json'

def configuration():
    c = json.loads(CONFIG.read_text())
    if c['half_life_hours'] <= 0 or c['cluster_window_hours'] <= 0:
        raise ValueError('Recency and cluster windows must be positive')
    if not 0 < c['similarity_threshold'] <= 1:
        raise ValueError('Similarity threshold must be in (0, 1]')
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in [*c['source_reliability'].values(), *c['source_overrides'].values()]):
        raise ValueError('Reliability values must be finite and in [0, 1]')
    if not 0 <= c['thresholds']['MEDIUM'] < c['thresholds']['HIGH'] < c['thresholds']['CRITICAL'] <= 10:
        raise ValueError('Risk thresholds must increase within [0, 10]')
    return c

def timestamp(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None: raise ValueError('Timestamp must include a timezone')
    return d.astimezone(timezone.utc)

def canonical(text):
    text = re.sub(r'^investor discussion:\s*', '', clean(text).lower())
    text = re.sub(r'#\w+', '', text)
    return ' '.join(re.findall(r'[a-z0-9]+', text))

def reliability(signal, config):
    return config['source_overrides'].get(signal.get('source'), config['source_reliability'].get(signal.get('source_type'), .45))

def recency(value, as_of, half_life):
    if not math.isfinite(half_life) or half_life <= 0: raise ValueError('Invalid half-life')
    age = max(0, (timestamp(as_of) - timestamp(value)).total_seconds() / 3600)
    return math.exp(-math.log(2) * age / half_life)

def risk_level(value, config):
    return next((k for k in ['CRITICAL', 'HIGH', 'MEDIUM'] if value >= config['thresholds'][k]), 'LOW')

def clock_for(signals):
    demo = all(s['id'].startswith(('news_', 'social_posts_')) for s in signals)
    return (max((s['timestamp'] for s in signals), key=timestamp) if signals and demo else datetime.now(timezone.utc).isoformat()), ('replay clock' if demo else 'UTC wall clock')

def similarity(a, b):
    if canonical(a) == canonical(b): return 1.0
    # Domain synonyms supplement lexical TF-IDF; this is not an embedding model.
    def expand(t):
        t = canonical(t)
        for words in [('oil', 'energy'), ('tensions', 'conflict'), ('escalating', 'renewed'), ('markets', 'prices')]:
            for w in words: t = re.sub(r'\b' + w + r'\b', words[0], t)
        return t
    try:
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words='english').fit_transform([expand(a), expand(b)])
        return float(cosine_similarity(matrix[0], matrix[1])[0, 0])
    except ValueError: return 0.0

def cluster_signals(signals, config=None, as_of=None):
    config = config or configuration()
    as_of = as_of or clock_for(signals)[0]
    groups = []
    seen = set()
    for s in signals:
        if s['id'] in seen: continue
        seen.add(s['id'])
        target = None
        best = 0
        for g in groups:
            anchor = g[0]
            if s['event_type'] != anchor['event_type']: continue
            if abs((timestamp(s['timestamp']) - timestamp(anchor['timestamp'])).total_seconds()) > config['cluster_window_hours'] * 3600: continue
            left, right = set(s.get('companies', [])), set(anchor.get('companies', []))
            if left and right and not left.intersection(right): continue
            sectors_a, sectors_b = set(s.get('affected_sectors', [])), set(anchor.get('affected_sectors', []))
            if sectors_a and sectors_b and not sectors_a.intersection(sectors_b): continue
            # Compare to anchor, avoiding transitive chains that merge unrelated events.
            score = similarity(s['text'], anchor['text'])
            if score >= config['similarity_threshold'] and score > best: target, best = g, score
        if target is None: groups.append([s])
        else: target.append(s)
    output = []
    for group in groups:
        # Exact/normalized copies provide no additional independent evidence.
        unique = {}
        for s in group:
            key = canonical(s['text'])
            if key not in unique or reliability(s, config) > reliability(unique[key], config): unique[key] = s
        representatives = list(unique.values())
        weights = [max(.001, reliability(s, config) * recency(s['timestamp'], as_of, config['half_life_hours'])) for s in representatives]
        def average(key): return sum(s[key] * w for s, w in zip(representatives, weights)) / sum(weights)
        sentiment = average('sentiment_score')
        agreement = max(0, 1 - sum(w * abs(s['sentiment_score'] - sentiment) for s, w in zip(representatives, weights)) / sum(weights))
        quality = sum(w * min(s['sentiment_confidence'], s['event_confidence']) * reliability(s, config) for s, w in zip(representatives, weights)) / sum(weights)
        # Bounded diversity bonus only for distinct wording AND distinct publishers; independence remains unproven.
        support = min(len(representatives), len({s['source'] for s in representatives}))
        confidence = min(.95, quality + min(.08, max(0, support - 1) * .04)) * agreement
        latest = max((s['timestamp'] for s in representatives), key=timestamp)
        decay = recency(latest, as_of, config['half_life_hours'])
        raw = average('impact_score')
        effective = raw * decay * confidence
        anchor = group[0]
        c = {**anchor, 'id': 'cluster_' + hashlib.sha256(anchor['id'].encode()).hexdigest()[:12],
             'member_ids': [s['id'] for s in group], 'members': group, 'observation_count': len(group),
             'source_count': len({(s['source_type'], s['source']) for s in group}),
             'source_types': sorted({s['source_type'] for s in group}), 'distinct_evidence_count': len(representatives),
             'duplicate_count': len(group) - len(representatives), 'source_agreement': round(agreement, 4),
             'independence_note': 'Distinct wording is not verified independence. Normalized copies do not increase confidence.',
             'source_reliability': round(sum(w * reliability(s, config) for s, w in zip(representatives, weights)) / sum(weights), 4),
             'raw_impact': round(raw, 4), 'impact_score': round(raw, 4), 'recency_factor': round(decay, 6),
             'adjusted_impact': round(raw * decay, 4), 'confidence': round(confidence, 4),
             'sentiment_score': round(sentiment, 4), 'effective_risk': round(effective, 4),
             'risk_level': risk_level(effective, config), 'as_of': as_of, 'timestamp': latest,
             'companies': sorted({x for s in group for x in s.get('companies', [])}),
             'affected_sectors': sorted({x for s in group for x in s.get('affected_sectors', [])}),
             'fusion_method': 'Constrained TF-IDF + exact-copy collapse; credibility/recency weighted evidence',
             'risk_formula': 'effective risk = raw impact × recency factor × evidence confidence'}
        output.append(c)
    return sorted(output, key=lambda c: c['effective_risk'], reverse=True)

def executive_summary(clusters):
    high = [c for c in clusters if c['risk_level'] in ['HIGH', 'CRITICAL']]
    if not clusters: return 'No signals processed. Replay or ingest a signal to assess portfolio exposure.'
    if not high: return f'{len(clusters)} unique events monitored. No event crosses the internal high-risk threshold.'
    sectors = sorted({s for c in high for s in c['affected_sectors']})
    return f'Portfolio attention is elevated: {len(high)} high or critical event clusters affect {", ".join(sectors) or "systemic exposures"}. Highest effective risk is {high[0]["effective_risk"]:.2f}/10.'
