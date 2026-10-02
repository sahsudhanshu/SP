"""Each asset has exactly one accounting path; shared graph nodes never add extra exposure."""
from backend.services.finance import exposure

def propagate(signal, portfolio, result=None):
    mapped = exposure(signal, portfolio)
    total = mapped['portfolio_value']
    nodes = {'event': {'id': 'event', 'type': 'event', 'label': signal['event_type'], 'risk': signal['effective_risk']},
             'portfolio': {'id': 'portfolio', 'type': 'portfolio', 'label': 'Wholesale portfolio', 'value': total}}
    edges, paths = {}, []
    losses = {a['asset_id']: a['loss'] for a in (result or {}).get('assets', [])}
    for asset in mapped['assets']:
        entity = 'entity:' + asset['issuer']
        sector = 'sector:' + asset['sector']
        aid = 'asset:' + asset['asset_id']
        nodes[entity] = {'id': entity, 'type': 'entity', 'label': asset['issuer'], 'reason': asset['mapping_reason']}
        nodes[sector] = {'id': sector, 'type': 'sector', 'label': asset['sector']}
        nodes[aid] = {'id': aid, 'type': 'asset', 'label': asset['asset_id'], **asset,
                      'portfolio_weight': asset['value']/total if total else 0,
                      'event_exposure': asset['value']*asset['mapping_weight'], 'scenario_loss': losses.get(asset['asset_id'], 0)}
        route = ['event', entity, sector, aid, 'portfolio']
        weights = [asset['mapping_weight'], 1, asset['sensitivity'], asset['value']/total if total else 0]
        meanings = ['exposure mapping', 'sector membership', 'event sensitivity', 'portfolio weight']
        for src, dst, w, meaning in zip(route, route[1:], weights, meanings):
            edges[(src, dst)] = {'source': src, 'target': dst, 'weight': w, 'meaning': meaning}
        contribution = signal['effective_risk']
        for w in weights: contribution *= w
        paths.append({'asset_id': asset['asset_id'], 'nodes': route, 'weights': weights,
                      'propagated_risk': round(contribution, 6), 'weighted_exposure': nodes[aid]['event_exposure'],
                      'scenario_loss': losses.get(asset['asset_id'], 0), 'reason': asset['mapping_reason']})
    return {'event': signal['id'], 'nodes': list(nodes.values()), 'edges': list(edges.values()), 'risk_paths': paths,
            'total_propagated_risk': round(sum(p['propagated_risk'] for p in paths), 6),
            'exposure': {k: v for k, v in mapped.items() if k != 'assets'},
            'formula': 'Sum over unique assets: effective risk × mapping weight × sector membership (1) × sensitivity × portfolio weight',
            'units': 'Portfolio risk points (0–10). Not a loss probability or monetary loss.'}

def heatmap(portfolio):
    sectors = sorted({a['sector'] for a in portfolio})
    events = sorted({e for a in portfolio for e in a['sensitivities'] if e != 'OTHER'})
    cells = []
    for sector in sectors:
        assets = [a for a in portfolio if a['sector'] == sector]
        total = sum(a['value'] for a in assets)
        for event in events:
            weighted = sum(a['value'] * a['sensitivities'].get(event, 0) for a in assets)
            cells.append({'sector': sector, 'event': event, 'score': round(10*weighted/total, 2) if total else 0,
                          'sensitivity_weighted_exposure': weighted, 'sector_value': total})
    return {'sectors': sectors, 'events': events, 'cells': cells,
            'method': '10 × value-weighted sector sensitivity. Structural exposure; independent of active event count.'}

def explain(c, graph, result):
    e = graph['exposure']
    lines = [f"{c['event_type']} classification: {c['event_confidence']:.0%} heuristic confidence; evidence: {', '.join(c.get('classification_evidence', [])) or 'TF-IDF similarity only'}.",
             f"{c['source_count']} sources, {c['observation_count']} observations, {c['distinct_evidence_count']} distinct texts; {c['duplicate_count']} normalized copies collapsed.",
             f"Sentiment {c['sentiment_score']:+.3f}; source reliability {c['source_reliability']:.2f}; agreement {c['source_agreement']:.0%}.",
             f"Raw impact {c['raw_impact']:.2f} × recency {c['recency_factor']:.3f} × confidence {c['confidence']:.3f} = {c['effective_risk']:.2f} ({c['risk_level']}).",
             f"Direct exposure INR {e['direct_exposure']:,.0f}; weighted exposure INR {e['weighted_exposure']:,.0f}; {len(graph['risk_paths'])} unique asset paths."]
    if result: lines.append(f"Moderate synthetic scenario loss INR {result['absolute_loss']:,.2f}; largest contributor {result['worst_asset']['asset_id']} at INR {result['worst_asset']['loss']:,.2f}.")
    return lines
