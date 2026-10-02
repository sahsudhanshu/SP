"""V2 adapters reuse the V1 asset valuation formula without changing its contract."""
from copy import deepcopy
from backend.services.finance import exposure, stress

def calculate(signal, scenario, portfolio, intensity=1, impact=None, exposure_scale=1, rate_shock=None, equity_shock=None):
    scenario = deepcopy(scenario)
    signal = {**signal, 'impact_score': signal['impact_score'] if impact is None else impact}
    if rate_shock is not None: scenario['rate_change'] = rate_shock
    if equity_shock is not None: scenario['shocks']['Equity'] = equity_shock
    # Exposure assumption multiplies mapped stress transmission, not the balance sheet.
    result = stress(signal, scenario, portfolio, intensity * exposure_scale)
    mapped = {a['asset_id']: a for a in exposure(signal, portfolio)['assets']}
    for a in result['assets']:
        m = mapped.get(a['asset_id'], {})
        a.update(sensitivity=m.get('sensitivity', 0), mapping_weight=m.get('mapping_weight', 0),
                 portfolio_weight=a['value']/result['portfolio_before'] if result['portfolio_before'] else 0,
                 event_type=signal['event_type'], cluster_id=signal['id'])
    result['top_contributors'] = sorted(result['assets'], key=lambda a: a['loss'], reverse=True)[:5]
    result['worst_asset'] = result['top_contributors'][0] if result['assets'] else None
    result['worst_sector'] = max(result['sector_losses'], key=lambda a: a['loss'], default=None)
    result['inputs'] = {'impact': signal['impact_score'], 'intensity': intensity, 'exposure_scale': exposure_scale,
                        'rate_shock': scenario.get('rate_change', 0), 'equity_shock': scenario['shocks'].get('Equity', 0)}
    result['interpretation'] = 'Conditional synthetic scenario loss, not an expected loss or probability-weighted prediction.'
    result['formula'] += ' × exposure assumption multiplier; final asset shock capped to [-100%, +100%]'
    return result

def compare(signal, scenario, portfolio):
    return [{'name': name, **calculate(signal, scenario, portfolio, intensity=value)}
            for name, value in [('Base', 0), ('Moderate', 1), ('Severe', 1.75)]]
