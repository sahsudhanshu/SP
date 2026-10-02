"""Reproducible synthetic data generation. No external or client information."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS = [
 ('Aurora Tech launches enterprise platform','Aurora Tech launches a new software platform with strong demand and improved profit growth.','Technology','PRODUCT_LAUNCH','positive'),
 ('Routine policy update','The central bank published its monetary policy schedule. Interest rate levels remain unchanged.','Financials','MACROECONOMIC','neutral'),
 ('Healthcare consolidation approved','Meridian Health merger acquisition deal approved by regulators after successful review.','Healthcare','MERGER_ACQUISITION','positive'),
 ('Energy supply under severe pressure','Severe geopolitical war and shipping blockade threatens oil supply. Sanctions cause a crisis and disruption for Helios Energy in India.','Energy','GEOPOLITICAL','negative'),
 ('Issuer misses debt payment','Atlas Industrials default after missed payment on corporate bonds. Credit downgrade and bankruptcy risk deepen losses.','Industrials','CREDIT_EVENT','negative'),
 ('Central bank raises rates','Central bank interest rate hike follows inflation surge and weak economic growth. Recession risk increases for banks.','Financials','MACROECONOMIC','negative'),
 ('Retail product rollout','Cedar Consumer launches a new product with record sales and profit growth.','Consumer','PRODUCT_LAUNCH','positive'),
 ('Technology takeover review','Aurora Tech acquisition takeover review proceeds with neutral regulatory timetable.','Technology','MERGER_ACQUISITION','neutral'),
 ('Regional shipping disruption','War and sanctions create severe geopolitical disruption in industrial shipping and energy markets.','Industrials','GEOPOLITICAL','negative'),
 ('Bank credit stabilizes','Northstar Bank credit downgrade risk declined after strong profit growth and improved liquidity.','Financials','CREDIT_EVENT','positive'),
 ('Health product introduced','Meridian Health introduces a new medicine product launch with successful clinical results.','Healthcare','PRODUCT_LAUNCH','positive'),
 ('Bond default warning','Helios Energy faces default and severe losses after missed debt payment and credit downgrade.','Energy','CREDIT_EVENT','negative'),
]

def seed():
    (ROOT/'data').mkdir(exist_ok=True)
    for source in ['news','social_posts']:
        with (ROOT/'data'/f'{source}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=['id','timestamp','source','source_type','headline','text','sector','expected_event','expected_sentiment'])
            writer.writeheader()
            for i,(headline,text,sector,event,sentiment) in enumerate(EVENTS):
                writer.writerow({'id':f'{source}_{i:02d}','timestamp':f'2026-10-01T09:{i*4:02d}:00+05:30',
                                 'source':'Synthetic Financial Wire' if source=='news' else 'Synthetic Social Stream',
                                 'source_type':'news' if source=='news' else 'social','headline':headline,
                                 'text':text if source=='news' else f'Investor discussion: {text} #markets',
                                 'sector':sector,'expected_event':event,'expected_sentiment':sentiment})
    assets=[
        ('LOAN_01','Corporate Loan','Helios Energy','Energy',12000000,0),
        ('BOND_01','Corporate Bond','Helios Energy','Energy',6000000,4),
        ('EQ_01','Equity','Helios Energy','Energy',7000000,0),
        ('LOAN_02','Corporate Loan','Aurora Tech','Technology',10000000,0),
        ('EQ_02','Equity','Aurora Tech','Technology',8000000,0),
        ('GOV_01','Government Bond','Synthetic India Treasury','Financials',15000000,6),
        ('BOND_02','Corporate Bond','Northstar Bank','Financials',10000000,3),
        ('LOAN_03','Corporate Loan','Meridian Health','Healthcare',8000000,0),
        ('EQ_03','Equity','Cedar Consumer','Consumer',7000000,0),
        ('LOAN_04','Corporate Loan','Atlas Industrials','Industrials',10000000,0),
        ('DER_01','Derivative','Atlas Industrials','Industrials',4000000,0),
        ('DER_02','Derivative','Helios Energy','Energy',3000000,0),
    ]
    with (ROOT/'data/portfolio.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=['asset_id','asset_type','issuer','sector','value','currency','duration','risk_factors','sensitivities'])
        w.writeheader()
        for aid,kind,issuer,sector,value,duration in assets:
            s={'GEOPOLITICAL':.85 if sector=='Energy' else .6,'MACROECONOMIC':.8 if kind.endswith('Bond') else .55,
               'CREDIT_EVENT':.95 if kind in ['Corporate Loan','Corporate Bond'] else .7,
               'MERGER_ACQUISITION':.5,'PRODUCT_LAUNCH':.45,'OTHER':.1}
            w.writerow(dict(asset_id=aid,asset_type=kind,issuer=issuer,sector=sector,value=value,currency='INR',duration=duration,
                            risk_factors='credit;rates;market',sensitivities=json.dumps(s)))
    scenarios=[]
    configs=[('GEOPOLITICAL',{'Equity':-.10,'Corporate Bond':-.06,'Corporate Loan':-.05,'Government Bond':-.02,'Derivative':-.12},0),
             ('MACROECONOMIC',{'Equity':-.08,'Corporate Bond':-.02,'Corporate Loan':-.03,'Government Bond':0,'Derivative':-.07},.02),
             ('CREDIT_EVENT',{'Equity':-.18,'Corporate Bond':-.16,'Corporate Loan':-.20,'Government Bond':0,'Derivative':-.10},0),
             ('MERGER_ACQUISITION',{'Equity':.04,'Corporate Bond':-.01,'Corporate Loan':-.015,'Government Bond':0,'Derivative':.02},0),
             ('PRODUCT_LAUNCH',{'Equity':.06,'Corporate Bond':.01,'Corporate Loan':.005,'Government Bond':0,'Derivative':.02},0)]
    for event,shocks,rate in configs:
        scenarios.append({'id':event.lower(),'event_type':event,'name':event.replace('_',' ').title()+' scenario',
                          'shocks':shocks,'rate_change':rate,'assumptions':'Synthetic hackathon stress assumptions. Fixed proportional shocks and duration approximation, no hedging/netting or calibrated default model.'})
    (ROOT/'data/scenarios.json').write_text(json.dumps(scenarios,indent=2))
    print('Created 24 source records, 12 assets worth INR 100M, 5 scenarios.')

if __name__=='__main__': seed()
