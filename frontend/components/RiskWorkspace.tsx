'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {usePathname,useSearchParams} from 'next/navigation';
import {Activity,ArrowRight,Radio,Network,FlaskConical,Layers,History,ShieldAlert,Grid3X3,FileSearch,ChartNoAxesCombined,RotateCcw,Play,Pause,Globe,Zap,Download,Sun,Moon,Coins,ChevronRight} from 'lucide-react';
import {request} from '@/lib/api';
import type {Cluster,Dashboard,Detail} from '@/lib/v2-types';
import {money,label,Badge,Panel,Metric,Plot,Explanation,Transmission,StressLab,type CurrencyMode} from './RiskVisuals';

const nav=[
  ['','Overview',Activity],
  ['risk-feed','Signal intelligence',Radio],
  ['risk-map','Risk transmission',Network],
  ['portfolio','Portfolio exposure',Layers],
  ['stress-testing','Stress & what-if',FlaskConical],
  ['timeline','Event timeline',History],
  ['alerts','Alert center',ShieldAlert],
  ['heatmap','Risk heatmap',Grid3X3],
  ['audit','Model audit',FileSearch],
  ['evaluation','Evaluation',ChartNoAxesCombined]
] as const;

type Evaluation={baseline:Record<string,unknown>|null;current:Record<string,unknown>|null;note:string};

export default function RiskWorkspace(){
  const search=useSearchParams().toString(),path=usePathname().slice(1),title=nav.find(n=>n[0]===path)?.[1]||'Event intelligence';
  const [data,setData]=useState<Dashboard|null>(null),[detail,setDetail]=useState<Detail|null>(null),[selected,setSelected]=useState(''),[initialAsset,setInitialAsset]=useState('');
  const [error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[playing,setPlaying]=useState(false),[mode,setMode]=useState('CONNECTING'),[model,setModel]=useState('Connecting'),[query,setQuery]=useState(''),[level,setLevel]=useState('ALL'),[input,setInput]=useState(''),[source,setSource]=useState('news'),[evaluation,setEvaluation]=useState<Evaluation|null>(null);
  const [theme,setTheme]=useState<'dark'|'light'>('dark');
  const [currency,setCurrency]=useState<CurrencyMode>('INR');
  const selectedRef=useRef(''),detailVersion=useRef(0),operation=useRef(false);

  useEffect(()=>{
    const saved=localStorage.getItem('riskpulse-theme') as 'dark'|'light'|null;
    if(saved){
      setTheme(saved);
      if(saved==='dark') document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
    }else{
      document.documentElement.classList.add('dark');
    }
    const savedCurr=localStorage.getItem('riskpulse-currency') as CurrencyMode|null;
    if(savedCurr) setCurrency(savedCurr);
  },[]);

  const toggleTheme=()=>{
    const next=theme==='dark'?'light':'dark';
    setTheme(next);
    localStorage.setItem('riskpulse-theme',next);
    if(next==='dark') document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  };

  const toggleCurrency=()=>{
    const next: CurrencyMode = currency==='INR'?'USD':'INR';
    setCurrency(next);
    localStorage.setItem('riskpulse-currency',next);
  };

  const refresh=useCallback(async()=>{
    try{
      const [d,h]=await Promise.all([
        request<Dashboard>('/api/v2/dashboard'),
        request<{sentiment_mode:string;data_mode:string;live_provider?:string;demo_observations:number}>('/api/health')
      ]);
      if(path==='evaluation')setEvaluation(await request<Evaluation>('/api/v2/evaluation'));
      setData(d);
      setModel(h.sentiment_mode);
      setMode(h.data_mode==='live_news'?`LIVE NEWS · ${h.live_provider||'Public feed'}`:h.data_mode==='demo_fallback'?'DEMO FALLBACK · LIVE SOURCE ERROR':'DEMO MODE');
      setError('');
      const id=selectedRef.current;
      if(d.clusters.some(c=>c.id===id)){
        const version=++detailVersion.current;
        const next=await request<Detail>(`/api/v2/clusters/${id}`);
        if(version===detailVersion.current)setDetail(next);
      }else{
        setDetail(d.priority);
        setSelected(d.priority?.cluster.id||'');
        selectedRef.current=d.priority?.cluster.id||'';
      }
    }catch(e){
      setError(`Connection unavailable. ${(e as Error).message}`);
    }
  },[path]);

  useEffect(()=>{
    const p=new URLSearchParams(window.location.search);
    selectedRef.current=p.get('event')||'';
    setSelected(selectedRef.current);
    setInitialAsset(p.get('asset')||'');
    refresh();
    const t=setInterval(refresh,7000);
    return()=>clearInterval(t);
  },[refresh,path,search]);

  const select=async(id:string)=>{
    selectedRef.current=id;
    setSelected(id);
    setDetail(null);
    const v=++detailVersion.current;
    try{
      const d=await request<Detail>(`/api/v2/clusters/${id}`);
      if(v===detailVersion.current)setDetail(d);
    }catch(e){
      setError((e as Error).message);
    }
  };

  const perform=useCallback(async(route:string,body:unknown={})=>{
    if(operation.current)return;
    operation.current=true;
    setBusy(true);
    try{
      const r=await request<Record<string,unknown>>(route,body);
      if(r.complete){
        setPlaying(false);
        setNotice('Replay complete. Reset to replay.');
      }else if(route.includes('reset')){
        selectedRef.current='';
        setMode('DEMO MODE');
        setNotice('Reset complete. Next event introduces the geopolitical shock.');
      }else if(route.includes('live')){
        setNotice(r.mode==='live_news'?`${r.provider}: ${r.new_count} new articles processed, ${r.already_seen} already seen. Portfolio and local social fixtures are synthetic.`:`Live sources failed. Demo fallback: ${r.reason}`);
        selectedRef.current='';
      }else{
        selectedRef.current='';
        setNotice('Signal processed. Fusion, exposure and audit history updated.');
      }
      await refresh();
    }catch(e){
      setPlaying(false);
      setError((e as Error).message);
    }finally{
      operation.current=false;
      setBusy(false);
    }
  },[refresh,path,search]);

  useEffect(()=>{
    if(!playing)return;
    const t=setInterval(()=>perform('/api/demo/next'),7000);
    return()=>clearInterval(t);
  },[playing,perform]);

  const c=detail?.cluster,filtered=(data?.clusters||[]).filter(c=>(level==='ALL'||c.risk_level===level)&&`${c.headline} ${c.event_type} ${c.companies.join(' ')}`.toLowerCase().includes(query.toLowerCase()));
  const isLive = mode.includes('LIVE');

  const exportAudit=()=>{
    const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(detail,null,2)],{type:'application/json'}));
    a.href=url;
    a.download='riskpulse-audit.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const eventTable=(rows:Cluster[])=>(
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Event cluster</th>
            <th>Sources</th>
            <th>Impact</th>
            <th>Confidence</th>
            <th>Effective risk</th>
            <th>Exposure</th>
            <th>Inspect</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(c=>(
            <tr key={c.id}>
              <td>
                <strong>{c.headline}</strong>
                <small>{label(c.event_type)} · {c.affected_sectors.join(', ')||'No sector match'}</small>
              </td>
              <td>{c.source_count}<small>{c.observation_count} observations</small></td>
              <td><span style={{fontFamily: 'var(--font-mono)'}}>{c.raw_impact.toFixed(2)}</span></td>
              <td><span style={{fontFamily: 'var(--font-mono)'}}>{(c.confidence*100).toFixed(1)}%</span></td>
              <td><Badge value={c.risk_level}/><small style={{fontFamily: 'var(--font-mono)'}}>{c.effective_risk.toFixed(2)} / 10</small></td>
              <td><span style={{fontFamily: 'var(--font-mono)'}}>{money(c.weighted_exposure||0, currency)}</span></td>
              <td>
                <Link className="text-button" href={`/risk-feed?event=${c.id}`}>Inspect</Link>
                <span style={{color: 'var(--line)', margin: '0 6px'}}>|</span>
                <Link className="text-button" href={`/risk-map?event=${c.id}`}>Trace ↗</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length&&<div className="empty">No matching events. Adjust the filter or ingest a signal.</div>}
    </div>
  );

  return (
    <div className="shell v2">
      <aside className="sidebar">
        <Link className="brand" href="/">
          <div className="brand-icon"><Activity size={23}/></div>
          <div>RiskPulse<span>PORTFOLIO INTELLIGENCE</span></div>
        </Link>
        <div className="workspace">
          <span className="workspace-icon">V2</span>
          <div>Risk analyst workspace<small>Wholesale banking · {currency==='INR'?'₹10 Cr book':'$100M book'}</small></div>
        </div>
        <nav>
          {nav.map(([route,name,Icon])=>(
            <Link key={route} className={path===route?'active':''} href={`/${route}`} title={name}>
              <Icon size={17}/>
              <span>{name}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="mode-card">
            <span className={`dot ${isLive ? 'radar' : ''}`}/>
            <b>{mode}</b>
            <p>Synthetic portfolio<br/>Prototype risk model</p>
          </div>
          <Link className="legacy-link" href="/legacy">Open preserved V1 workspace ↗</Link>
        </div>
      </aside>

      <main>
        <header>
          <div className="breadcrumb">
            Risk operations <ArrowRight size={12}/><strong>{title}</strong>
          </div>
          <div className="header-status">
            <span className={`dot ${error?'offline':isLive?'radar':''}`}/>
            {error?'Connection interrupted':model==='Connecting'?'Connecting':`Local model · ${model}`}
            <button
              id="currency-toggle"
              className="theme-toggle-btn"
              onClick={toggleCurrency}
              aria-label={`Switch to ${currency==='INR'?'USD ($)':'INR (₹)'}`}
              title="Toggle display currency (INR Cr/L vs USD M/K)"
            >
              <Coins size={14} style={{color: currency === 'INR' ? '#10b981' : '#38bdf8'}}/>
              <span>{currency === 'INR' ? '₹ INR (Cr / L)' : '$ USD (M)'}</span>
            </button>
            <button
              id="theme-toggle"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme==='dark'?'light':'dark'} mode`}
            >
              {theme==='dark'?<Sun size={14} style={{color: '#f59e0b'}}/>:<Moon size={14} style={{color: '#38bdf8'}}/>}
              <span>{theme==='dark'?'Light mode':'Dark obsidian'}</span>
            </button>
          </div>
        </header>

        <div className="content">
          <div className="page-head">
            <div>
              <div className="workflow-stepper">
                <span className="step-pill active">SIGNAL</span>
                <ChevronRight size={11} className="step-sep"/>
                <span className="step-pill">INTELLIGENCE</span>
                <ChevronRight size={11} className="step-sep"/>
                <span className="step-pill">EXPOSURE</span>
                <ChevronRight size={11} className="step-sep"/>
                <span className="step-pill">STRESS</span>
                <ChevronRight size={11} className="step-sep"/>
                <span className="step-pill">IMPACT</span>
              </div>
              <h1>{path==='risk-map'?'Risk transmission map':path===''?'Portfolio risk command center':title}</h1>
              <p>Trace every decision from its source to the portfolio.</p>
            </div>
            <div className="actions">
              <button className="button secondary" disabled={busy} onClick={()=>{setPlaying(false);perform('/api/demo/reset');}}>
                <RotateCcw size={14}/>Reset
              </button>
              <button className="button primary" disabled={busy} onClick={()=>perform('/api/demo/next')}>
                <Zap size={14}/>{busy?'Processing…':'Next event'}
              </button>
            </div>
          </div>

          <div className="control-strip">
            <div>
              <span className={`dot ${isLive ? 'radar' : ''}`}/>
              <b>{mode}</b>
              <span>{data?.observation_count||0} observations → {data?.clusters.length||0} unique events</span>
              <span className="model-chip">{data?.clock||'Awaiting clock'}</span>
            </div>
            <div>
              <button className="icon-button" aria-label={playing?'Pause replay':'Start replay'} disabled={busy||!!error} onClick={()=>setPlaying(!playing)}>
                {playing?<Pause size={15}/>:<Play size={15}/>}
              </button>
              <button className="button secondary" disabled={busy} onClick={()=>{setPlaying(false);perform('/api/ingest/live');}}>
                <Globe size={13}/>Fetch live news
              </button>
            </div>
          </div>

          {error&&<div className="alert error" role="alert">{error}<button onClick={refresh}>Retry connection</button></div>}
          {notice&&<div className="alert" role="status">{notice}<button onClick={()=>setNotice('')}>Dismiss</button></div>}

          {!data ? (
            <div className="empty" role="status">{error?'Start the backend, then retry.':'Loading portfolio intelligence…'}</div>
          ) : (
            <>
              {path==='' && (
                <>
                  <div className="executive">
                    <div>
                      <span className="eyebrow">PRIORITY EVENT BRIEF</span>
                      <h2>{data.summary}</h2>
                      <p>Priority event: <b>{data.priority?.cluster.headline||'Awaiting signals'}</b></p>
                    </div>
                    <Link className="button secondary" href="/alerts">
                      Review alerts <ArrowRight size={14}/>
                    </Link>
                  </div>

                  <div className="metrics">
                    <Metric title="Portfolio value" value={money(data.portfolio_value, currency)} note={`${data.assets.length} synthetic positions`}/>
                    <Metric title="Current risk" value={`${data.current_risk.toFixed(2)} / 10`} note="Highest confidence-adjusted event risk"/>
                    <Metric title="High-impact events" value={`${data.high_impact_events}`} note="Unique clusters with raw impact ≥ 8"/>
                    <Metric title="Estimated stress loss" value={money(data.priority?.result?.absolute_loss||0, currency)} note="Priority event · moderate conditional scenario"/>
                  </div>

                  <Panel title="Live signal feed" note="Copied observations are collapsed before prioritization" action={<Link className="text-button" href="/risk-feed">All events →</Link>}>
                    {eventTable(data.clusters.slice(0,4))}
                  </Panel>

                  {detail && (
                    <Panel title="Where the risk goes" note={`${label(detail.cluster.event_type)} · actual portfolio transmission paths`} action={<Link className="text-button" href={`/risk-map?event=${detail.cluster.id}`}>Inspect risk map →</Link>}>
                      <Transmission graph={detail.graph} compact isDark={theme==='dark'} currency={currency}/>
                    </Panel>
                  )}

                  <div className="grid-equal">
                    <Panel title="Portfolio exposure" note={`Position value by sector · ${currency === 'INR' ? '₹ Crores' : 'USD Millions'}`}>
                      <Plot data={data.heatmap.sectors.map(sector=>({sector,value_M:data.assets.filter(a=>a.sector===sector).reduce((s,a)=>s+a.value,0)/1e6}))} x="sector" y="value_M" bar color="#38bdf8" currency={currency}/>
                    </Panel>
                    <Panel title="Recent stress tests" note="Saved V1 calculations retain the original demo contract">
                      {data.recent_tests.length ? (
                        <div className="recent-tests">
                          {data.recent_tests.map((r,i)=>(
                            <div key={i} style={{padding: '14px 0', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                              <span><b>{label(r.event_type)}</b><small style={{display: 'block', color: 'var(--text-muted)'}}>{r.signal_id}</small></span>
                              <b style={{color: '#f43f5e', fontFamily: 'var(--font-mono)'}}>{money(r.absolute_loss, currency)}</b>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="empty">No tests saved. Process a high-impact event.</div>
                      )}
                    </Panel>
                  </div>
                </>
              )}

              {['risk-map','risk-feed','stress-testing','audit','portfolio'].includes(path) && (
                <div className="event-select" style={{display: 'flex', alignItems: 'center', gap: 14, marginBottom: 22}}>
                  <label htmlFor="event-choice" style={{fontWeight: 600, color: 'var(--text-secondary)'}}>Active event</label>
                  <select id="event-choice" value={selected} onChange={e=>select(e.target.value)} style={{flex: 1, maxWidth: 850}}>
                    {data.clusters.map(c=><option key={c.id} value={c.id}>{c.headline}</option>)}
                  </select>
                  {c&&<Badge value={c.risk_level}/>}
                </div>
              )}

              {['risk-feed','alerts'].includes(path) && (
                <>
                  <div className="filter-bar">
                    <input aria-label="Search events" className="search" placeholder="Search event, issuer or classification…" value={query} onChange={e=>setQuery(e.target.value)}/>
                    <select aria-label="Filter risk level" value={level} onChange={e=>setLevel(e.target.value)}>
                      {['ALL','CRITICAL','HIGH','MEDIUM','LOW'].map(x=><option key={x}>{x}</option>)}
                    </select>
                  </div>
                  <Panel title={path==='alerts'?'Current risk alerts':'Fused event intelligence'} note="Internal thresholds: Low < 3 · Medium ≥ 3 · High ≥ 6 · Critical ≥ 8">
                    {eventTable(filtered)}
                  </Panel>
                </>
              )}

              {['risk-map','risk-feed','audit','portfolio','stress-testing'].includes(path) && !detail && (
                <div className="empty" role="status">{data.clusters.length?'Loading selected event…':'No events available. Process the next event.'}</div>
              )}

              {path==='risk-feed' && (
                <>
                  <Panel title="Analyze a source observation" note="Manual input uses current time; recency switches to wall time.">
                    <textarea aria-label="Source text" placeholder="Paste financial news or a social observation…" value={input} onChange={e=>setInput(e.target.value)}/>
                    <div className="form-actions">
                      <select aria-label="Source type" value={source} onChange={e=>setSource(e.target.value)}>
                        <option value="news">Financial news</option>
                        <option value="social">Social post</option>
                      </select>
                      <button className="button primary" disabled={busy||input.trim().length<3} onClick={()=>perform('/api/analyze',{text:input,source_type:source,source:'Manual analyst input'})}>
                        Analyze observation
                      </button>
                    </div>
                  </Panel>
                  {detail && (
                    <>
                      <Panel title="Why this event matters" note={detail.cluster.headline}>
                        <div className="metrics inner-metrics" style={{display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, padding: '16px 20px', marginBottom: 10}}>
                          <Metric title="Raw impact" value={detail.cluster.raw_impact.toFixed(2)} note="Severity business score / 10"/>
                          <Metric title="Evidence confidence" value={`${(detail.cluster.confidence*100).toFixed(1)}%`} note="Heuristic; not probability"/>
                          <Metric title="Recency factor" value={detail.cluster.recency_factor.toFixed(3)} note={`${data.config.half_life_hours} hour half-life`}/>
                          <Metric title="Adjusted impact" value={detail.cluster.adjusted_impact.toFixed(2)} note="Raw impact × recency"/>
                        </div>
                        <dl className="intelligence-grid" style={{display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16, padding: '12px 24px 20px', margin: 0}}>
                          <div><dt style={{color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase'}}>Source reliability</dt><dd style={{fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)', margin: '4px 0 0'}}>{detail.cluster.source_reliability.toFixed(2)}</dd></div>
                          <div><dt style={{color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase'}}>Source agreement</dt><dd style={{fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)', margin: '4px 0 0'}}>{(detail.cluster.source_agreement*100).toFixed(1)}%</dd></div>
                          <div><dt style={{color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase'}}>Sources / distinct texts / copies</dt><dd style={{fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)', margin: '4px 0 0'}}>{detail.cluster.source_count} / {detail.cluster.distinct_evidence_count} / {detail.cluster.duplicate_count}</dd></div>
                          <div><dt style={{color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase'}}>Who is affected</dt><dd style={{fontSize: 14, fontWeight: 600, margin: '4px 0 0'}}>{detail.cluster.companies.join(', ')||detail.cluster.affected_sectors.join(', ')||'No direct match'}</dd></div>
                          <div><dt style={{color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase'}}>Weighted portfolio exposure</dt><dd style={{fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', margin: '4px 0 0'}}>{money(detail.graph.exposure.weighted_exposure, currency)}</dd></div>
                          <div><dt style={{color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase'}}>Conditional scenario loss</dt><dd style={{fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#f43f5e', margin: '4px 0 0'}}>{money(detail.result?.absolute_loss||0, currency)}</dd></div>
                        </dl>
                        <p className="formula">{detail.cluster.independence_note}</p>
                      </Panel>
                      <Explanation detail={detail}/>
                    </>
                  )}
                </>
              )}

              {path==='risk-map' && detail && (
                <>
                  <div className="metrics">
                    <Metric title="Direct exposure" value={money(detail.graph.exposure.direct_exposure, currency)} note="Issuer and sector matches"/>
                    <Metric title="Weighted exposure" value={money(detail.graph.exposure.weighted_exposure, currency)} note="Includes systemic spillover"/>
                    <Metric title="Propagated risk" value={detail.graph.total_propagated_risk.toFixed(3)} note="Portfolio risk points"/>
                    <Metric title="Moderate scenario loss" value={money(detail.result?.absolute_loss||0, currency)} note="Conditional synthetic result"/>
                  </div>
                  <Panel title={label(detail.cluster.event_type)} note={detail.cluster.headline}>
                    <Transmission graph={detail.graph} initialAsset={initialAsset} isDark={theme==='dark'} currency={currency}/>
                  </Panel>
                  <Explanation detail={detail}/>
                  <Panel title="Transmission ledger" note="Exactly one path per position">
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Asset</th>
                            <th>Mapping reason</th>
                            <th>Edge weights</th>
                            <th>Risk points</th>
                            <th>Weighted exposure</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.graph.risk_paths.map(p=>(
                            <tr key={p.asset_id}>
                              <td><b style={{fontFamily: 'var(--font-mono)'}}>{p.asset_id}</b></td>
                              <td>{p.reason}</td>
                              <td><span style={{fontFamily: 'var(--font-mono)'}}>{p.weights.map(w=>w.toFixed(2)).join(' × ')}</span></td>
                              <td><span style={{fontFamily: 'var(--font-mono)'}}>{p.propagated_risk.toFixed(4)}</span></td>
                              <td><b style={{fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)'}}>{money(p.weighted_exposure, currency)}</b></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <p className="formula">{detail.graph.formula}</p>
                  </Panel>
                </>
              )}

              {path==='stress-testing' && detail && (
                <StressLab key={`${detail.cluster.id}:${detail.cluster.observation_count}`} detail={detail} currency={currency}/>
              )}

              {path==='portfolio' && detail && (
                <>
                  <Panel title="Portfolio positions & event exposure" note="Synthetic wholesale-banking assets · sensitivity depends on selected event">
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Position / issuer</th>
                            <th>Asset class</th>
                            <th>Sector</th>
                            <th>Value</th>
                            <th>Event sensitivity</th>
                            <th>Portfolio weight</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.assets.map(a=>(
                            <tr key={a.asset_id}>
                              <td>
                                <Link href={`/risk-map?event=${detail.cluster.id}&asset=${a.asset_id}`}>
                                  <strong>{a.asset_id} · {a.issuer}</strong>
                                </Link>
                              </td>
                              <td>{a.asset_type}</td>
                              <td>{a.sector}</td>
                              <td><span style={{fontFamily: 'var(--font-mono)'}}>{money(a.value, currency)}</span></td>
                              <td><span style={{fontFamily: 'var(--font-mono)'}}>{a.sensitivities[detail.cluster.event_type]||0}</span></td>
                              <td><span style={{fontFamily: 'var(--font-mono)'}}>{(100*a.value/data.portfolio_value).toFixed(1)}%</span></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Panel>
                  <Explanation detail={detail}/>
                </>
              )}

              {path==='timeline' && (
                <>
                  <div className="grid-equal">
                    {[
                      ['risk_score','Risk score over time'],
                      ['sentiment','Event sentiment over time'],
                      ['high_impact_events','Unique high-impact events'],
                      ['loss_M','Arrival-event scenario loss · INR M']
                    ].map(([key,name])=>(
                      <Panel key={key} title={name} note="Persisted arrival snapshots · observation sequence">
                        <Plot data={data.history.map(h=>({...h,loss_M:h.portfolio_loss/1e6}))} x="sequence" y={key} currency={currency}/>
                      </Panel>
                    ))}
                  </div>
                  <Panel title="Event timeline" note="Actual observations and computed threshold crossings">
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Sequence / replay time</th>
                            <th>Event / transition</th>
                            <th>Sentiment</th>
                            <th>Impact</th>
                            <th>Sources / sector</th>
                            <th>Scenario loss</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[...data.history].reverse().map(h=>(
                            <tr key={h.id}>
                              <td><b style={{fontFamily: 'var(--font-mono)'}}>#{h.sequence}</b><small>{new Date(h.timestamp).toLocaleTimeString()}</small></td>
                              <td>
                                <Link href={`/risk-map?event=${h.cluster_id}`}>
                                  <strong>{h.headline}</strong>
                                </Link>
                                <small>{h.transitions.join(' → ')}</small>
                              </td>
                              <td><span style={{fontFamily: 'var(--font-mono)'}}>{h.sentiment.toFixed(3)}</span></td>
                              <td><span style={{fontFamily: 'var(--font-mono)'}}>{h.impact.toFixed(2)}</span></td>
                              <td>{h.source_count}<small>{h.sectors.join(', ')}</small></td>
                              <td><b style={{color: '#f43f5e', fontFamily: 'var(--font-mono)'}}>{money(h.portfolio_loss, currency)}</b></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {!data.history.length&&<div className="empty">No V2 history yet. Reset and replay.</div>}
                    </div>
                  </Panel>
                </>
              )}

              {path==='heatmap' && (
                <Panel title="Sector × event sensitivity" note={data.heatmap.method}>
                  <div className="table-wrap">
                    <table className="heatmap">
                      <thead>
                        <tr>
                          <th>Sector</th>
                          {data.heatmap.events.map(e=><th key={e}>{label(e)}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {data.heatmap.sectors.map(s=>(
                          <tr key={s}>
                            <th>{s}</th>
                            {data.heatmap.events.map(e=>{
                              const cell=data.heatmap.cells.find(c=>c.sector===s&&c.event===e)!;
                              return (
                                <td key={e}>
                                  <div style={{background:`rgba(56,189,248,${0.06+cell.score*0.06})`, border: '1px solid rgba(56,189,248,0.15)'}}>
                                    <b>{cell.score.toFixed(1)}</b>
                                    <small>{money(cell.sensitivity_weighted_exposure, currency)}</small>
                                  </div>
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="formula">Scale 0–10. Configured structural sensitivities, not predictions of market moves.</p>
                </Panel>
              )}

              {path==='audit' && detail && (
                <>
                  <Panel title="Signal-to-decision audit" note="Model evidence, assumptions and reconciled valuation" action={<button className="button secondary" onClick={exportAudit}><Download size={14}/>Export JSON</button>}>
                    <div className="audit-body" style={{padding: '12px 24px 24px'}}>
                      {detail.cluster.members?.map((m,i)=>(
                        <details key={i} open={i===0} style={{borderBottom: '1px solid var(--line)', padding: '14px 0'}}>
                          <summary style={{cursor: 'pointer', fontWeight: 600, color: 'var(--text-primary)'}}>Observation {i+1} · {String(m.source_type)} · {String(m.source)}</summary>
                          <p style={{margin: '10px 0'}}>{String(m.text)}</p>
                          <pre style={{whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto', padding: 14, background: 'rgba(0,0,0,0.2)', border: '1px solid var(--line)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 11}}>{JSON.stringify(m,null,2)}</pre>
                        </details>
                      ))}
                      <details open style={{borderBottom: '1px solid var(--line)', padding: '14px 0'}}>
                        <summary style={{cursor: 'pointer', fontWeight: 600, color: 'var(--text-primary)'}}>Fusion, credibility and recency</summary>
                        <pre style={{whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto', padding: 14, background: 'rgba(0,0,0,0.2)', border: '1px solid var(--line)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 11}}>{JSON.stringify(Object.fromEntries(Object.entries(detail.cluster).filter(([k])=>!['members','text'].includes(k))),null,2)}</pre>
                      </details>
                      <details style={{borderBottom: '1px solid var(--line)', padding: '14px 0'}}>
                        <summary style={{cursor: 'pointer', fontWeight: 600, color: 'var(--text-primary)'}}>Risk paths and exposure</summary>
                        <pre style={{whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto', padding: 14, background: 'rgba(0,0,0,0.2)', border: '1px solid var(--line)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 11}}>{JSON.stringify(detail.graph,null,2)}</pre>
                      </details>
                      <details style={{padding: '14px 0'}}>
                        <summary style={{cursor: 'pointer', fontWeight: 600, color: 'var(--text-primary)'}}>Stress scenario and final result</summary>
                        <pre style={{whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto', padding: 14, background: 'rgba(0,0,0,0.2)', border: '1px solid var(--line)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 11}}>{JSON.stringify(detail.result,null,2)}</pre>
                      </details>
                    </div>
                  </Panel>
                  <Explanation detail={detail}/>
                </>
              )}

              {path==='evaluation' && (
                <Panel title="Measured diagnostics: V1 → V2" note={evaluation?.note||'Loading measured results…'}>
                  {evaluation ? (
                    <div className="audit-body" style={{padding: '14px 24px 24px'}}>
                      <div className="alert">24 synthetic author-labelled records, including paired copies. No claim of real-world predictive accuracy.</div>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Metric</th>
                              <th>V1 saved baseline</th>
                              <th>V2 measured</th>
                            </tr>
                          </thead>
                          <tbody>
                            {[
                              ['records_processed','Records'],
                              ['event_classification_accuracy','Event-label agreement'],
                              ['sentiment_label_agreement','Sentiment-label agreement'],
                              ['average_pipeline_latency_ms','Mean NLP pipeline (ms)'],
                              ['average_stress_ms_100_runs','Mean stress calculation (ms)']
                            ].map(([key,name])=>(
                              <tr key={key}>
                                <td>{name}</td>
                                <td><span style={{fontFamily: 'var(--font-mono)'}}>{formatMetric(evaluation.baseline?.[key],key)}</span></td>
                                <td><b style={{fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)'}}>{formatMetric(evaluation.current?.[key],key)}</b></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <h3 style={{marginTop: 24, marginBottom: 12}}>Controlled sequential vs batched inference</h3>
                      <pre style={{whiteSpace: 'pre-wrap', padding: 14, background: 'rgba(0,0,0,0.2)', border: '1px solid var(--line)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 11}}>
                        {evaluation.current?JSON.stringify(evaluation.current.benchmark,null,2):'Not measured yet. Run scripts/evaluate_v2.py.'}
                      </pre>
                      <p>{String(evaluation.current?.caveats||'')}</p>
                    </div>
                  ) : (
                    <div className="empty">{error?'Evaluation unavailable. Retry connection.':'Loading measured diagnostics…'}</div>
                  )}
                </Panel>
              )}
            </>
          )}

          <footer>
            <span>SYNTHETIC PORTFOLIO · SYNTHETIC STRESS ASSUMPTIONS · PROTOTYPE RISK MODEL</span>
            <span>RiskPulse AI · v2.0 Obsidian Edition</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function formatMetric(v:unknown,key:string){
  if(typeof v!=='number')return 'Not measured';
  return key.includes('agreement')||key.includes('accuracy')?`${(v*100).toFixed(2)}%`:v.toFixed(key==='records_processed'?0:3);
}
