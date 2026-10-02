"""Explainable synthetic scenario analysis, not a calibrated loss forecast."""
import math

DEFAULT_WEIGHTS = {'severity':.45,'sentiment':.2,'relevance':.1,'reliability':.1,'exposure':.15}
SEVERITY = {'GEOPOLITICAL':.85,'MACROECONOMIC':.65,'CREDIT_EVENT':.9,'MERGER_ACQUISITION':.35,'PRODUCT_LAUNCH':.25,'OTHER':.1}

def exposure(signal, portfolio):
    event = signal['event_type']
    broad = event in {'MACROECONOMIC','GEOPOLITICAL'}
    mapped = []
    for asset in portfolio:
        issuer = asset['issuer'] in signal.get('companies',[])
        sector = asset['sector'] in signal.get('affected_sectors',[])
        weight = 1 if issuer else .8 if sector else .35 if broad else 0
        if weight:
            mapped.append({**asset,'mapping_weight':weight,'mapping_reason':'issuer match' if issuer else 'sector match' if sector else 'systemic spillover',
                           'sensitivity':asset['sensitivities'].get(event,.15)})
    total = sum(a['value'] for a in portfolio)
    direct = sum(a['value'] for a in mapped if a['mapping_reason']!='systemic spillover')
    weighted = sum(a['value']*a['mapping_weight'] for a in mapped)
    return {'direct_exposure':direct,'weighted_exposure':round(weighted,2),'exposure_fraction':weighted/total if total else 0,
            'high_sensitivity_exposure':sum(a['value'] for a in mapped if a['sensitivity']>=.7),
            'portfolio_value':total,'assets':mapped,'label':'HIGH PORTFOLIO EXPOSURE' if weighted/total>=.3 else 'MODERATE PORTFOLIO EXPOSURE' if weighted else 'NO MAPPED EXPOSURE'}

def impact(signal, mapped, text, weights=None):
    weights = weights or DEFAULT_WEIGHTS
    if set(weights)!=set(DEFAULT_WEIGHTS) or any(not math.isfinite(v) or v<0 for v in weights.values()) or abs(sum(weights.values())-1)>1e-6:
        raise ValueError('Impact weights must be nonnegative, finite, and sum to one')
    severity = SEVERITY[signal['event_type']]
    evidence = [t for t in ['severe','war','blockade','default','bankruptcy','crisis'] if t in text.lower()]
    if evidence: severity = min(1,severity+.15)
    factors = {'severity':severity,'sentiment':abs(signal['sentiment_score']),
               'relevance':1 if signal.get('companies') else .7 if signal.get('affected_sectors') else .1,
               'reliability':.85 if signal['source_type']=='news' else .55,
               'exposure':min(1,mapped['exposure_fraction']*2)}
    components = {k:round(9*weights[k]*v,4) for k,v in factors.items()}
    score = round(min(10,max(1,1+sum(components.values()))),2)
    return {'impact_score':score,'risk_level':'HIGH' if score>=8 else 'MEDIUM' if score>=5 else 'LOW',
            'impact_components':components,'impact_weights':weights,'impact_factors':factors,
            'impact_method':'configurable business-rule score; not loss probability',
            'impact_reason':[f"{signal['event_type']} severity: {severity:.2f}",f"Sentiment magnitude: {abs(signal['sentiment_score']):.2f}",
                             f"Weighted portfolio exposure: INR {mapped['weighted_exposure']:,.0f}",f"Source reliability assumption: {factors['reliability']:.2f}"]}

def stress(signal, scenario, portfolio, intensity=1):
    mapped = exposure(signal,portfolio)
    by_id = {a['asset_id']:a for a in mapped['assets']}
    result = []
    scale = signal['impact_score']/10 * intensity
    for asset in portfolio:
        match = by_id.get(asset['asset_id'])
        shock = scenario['shocks'].get(asset['asset_type'],0)
        # Duration approximation: delta price / price = -duration * delta yield.
        if scenario.get('rate_change') and asset['asset_type'] in ['Government Bond','Corporate Bond']:
            shock -= asset['duration']*scenario['rate_change']
        applied = max(-1,min(1,shock*scale*match['mapping_weight']*match['sensitivity'])) if match else 0
        loss = round(-asset['value']*applied,2)
        result.append({**asset,'shock':round(applied,6),'loss':loss,'after':round(asset['value']-loss,2),
                       'mapping_reason':match['mapping_reason'] if match else 'no mapped exposure'})
    before = sum(a['value'] for a in portfolio)
    loss = round(sum(a['loss'] for a in result),2)
    sectors = {}
    for a in result: sectors[a['sector']] = round(sectors.get(a['sector'],0)+a['loss'],2)
    return {'signal_id':signal.get('id'),'event_type':signal['event_type'],'scenario_id':scenario['id'],
            'assumption_label':'Synthetic hackathon stress assumptions','intensity':intensity,'scale':round(scale,4),
            'formula':'asset loss = -value × scenario shock × (impact/10) × intensity × mapping weight × event sensitivity',
            'portfolio_before':before,'portfolio_after':round(before-loss,2),'absolute_loss':loss,
            'loss_percentage':round(loss/before*100,4) if before else 0,'assets':result,
            'sector_losses':[{'sector':k,'loss':v} for k,v in sectors.items()],
            'top_contributors':sorted(result,key=lambda a:a['loss'],reverse=True)[:5],
            'exposure':{k:v for k,v in mapped.items() if k!='assets'},'scenario':scenario}
