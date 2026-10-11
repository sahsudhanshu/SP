'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {ArrowRight} from 'lucide-react';
import {ResponsiveContainer,BarChart,Bar,AreaChart,Area,XAxis,YAxis,CartesianGrid,Tooltip} from 'recharts';
import {request} from '@/lib/api';
import type {Detail,Graph,GraphNode,Result} from '@/lib/v2-types';

export type CurrencyMode = 'INR' | 'USD';

export const money = (n: number, currency: CurrencyMode = 'INR') => {
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (currency === 'INR') {
    if (abs >= 1e7) {
      return `${sign}₹${(abs / 1e7).toFixed(2)} Cr`;
    } else if (abs >= 1e5) {
      return `${sign}₹${(abs / 1e5).toFixed(2)} L`;
    } else if (abs >= 1e3) {
      return `${sign}₹${(abs / 1e3).toFixed(1)} K`;
    }
    return `${sign}₹${abs.toFixed(0)}`;
  } else {
    if (abs >= 1e6) {
      return `${sign}$${(abs / 1e6).toFixed(2)}M`;
    } else if (abs >= 1e3) {
      return `${sign}$${(abs / 1e3).toFixed(1)}K`;
    }
    return `${sign}$${abs.toFixed(0)}`;
  }
};

export const label = (s: string) => s.replaceAll('_',' ').toLowerCase().replace(/\b\w/g,c=>c.toUpperCase());

export function Badge({value}:{value:string}){
  return (
    <span className={`badge ${value.toLowerCase()}`}>
      <span className="dot" style={{width: 5, height: 5, marginRight: 5, display: 'inline-block'}} />
      {value}
    </span>
  );
}

export function Panel({title,note,children,action}:{title:string;note?:string;children:React.ReactNode;action?:React.ReactNode}){
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h3>{title}</h3>
          {note&&<p>{note}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function Metric({title,value,note}:{title:string;value:string;note:string}){
  return (
    <div className="metric">
      <span>{title}</span>
      <h2>{value}</h2>
      <small>{note}</small>
    </div>
  );
}

export function Plot({
  data,
  x,
  y,
  bar=false,
  color='#38bdf8',
  currency='INR'
}:{
  data:Record<string,unknown>[];
  x:string;
  y:string;
  bar?:boolean;
  color?:string;
  currency?:CurrencyMode;
}){
  return (
    <div className="chart v2chart">
      <ResponsiveContainer width="100%" height="100%">
        {bar ? (
          <BarChart data={data} margin={{left:8,right:18,bottom:10}}>
            <CartesianGrid vertical={false} stroke="var(--line)" />
            <XAxis dataKey={x} tick={{fontSize:10, fill: 'var(--text-muted)'}} axisLine={false} tickLine={false}/>
            <YAxis tick={{fontSize:10, fill: 'var(--text-muted)'}} width={44} axisLine={false} tickLine={false}/>
            <Tooltip
              cursor={{ fill: 'var(--chart-cursor, rgba(56, 189, 248, 0.08))' }}
              contentStyle={{
                backgroundColor: 'var(--tooltip-bg, rgba(15, 23, 42, 0.95))',
                borderColor: 'var(--tooltip-border, rgba(56, 189, 248, 0.3))',
                borderRadius: '10px',
                color: 'var(--tooltip-text, #f8fafc)',
                fontSize: '12px',
                boxShadow: 'var(--card-shadow)',
                backdropFilter: 'blur(12px)'
              }}
              formatter={(val: unknown) => [
                typeof val === 'number'
                  ? (currency === 'INR' ? `₹${(val / 10).toFixed(2)} Cr` : `$${val.toFixed(2)}M`)
                  : String(val ?? ''),
                'Portfolio Exposure'
              ]}
              labelFormatter={(lbl) => `Sector: ${lbl}`}
            />
            <Bar isAnimationActive={true} animationDuration={700} dataKey={y} fill={color} radius={[6,6,0,0]}/>
          </BarChart>
        ) : (
          <AreaChart data={data} margin={{left:8,right:18,bottom:10}}>
            <defs>
              <linearGradient id={`areaGrad-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.4}/>
                <stop offset="95%" stopColor={color} stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="var(--line)" />
            <XAxis dataKey={x} tick={{fontSize:10, fill: 'var(--text-muted)'}} axisLine={false} tickLine={false}/>
            <YAxis tick={{fontSize:10, fill: 'var(--text-muted)'}} width={44} axisLine={false} tickLine={false}/>
            <Tooltip
              cursor={{ stroke: 'var(--line)' }}
              contentStyle={{
                backgroundColor: 'var(--tooltip-bg, rgba(15, 23, 42, 0.95))',
                borderColor: 'var(--tooltip-border, rgba(56, 189, 248, 0.3))',
                borderRadius: '10px',
                color: 'var(--tooltip-text, #f8fafc)',
                fontSize: '12px',
                boxShadow: 'var(--card-shadow)',
                backdropFilter: 'blur(12px)'
              }}
              formatter={(val: unknown) => [
                typeof val === 'number'
                  ? (currency === 'INR' ? `₹${(val / 10).toFixed(2)} Cr` : `$${val.toFixed(2)}M`)
                  : String(val ?? ''),
                'Value'
              ]}
              labelFormatter={(lbl) => `Point: ${lbl}`}
            />
            <Area isAnimationActive={true} animationDuration={800} dataKey={y} stroke={color} fill={`url(#areaGrad-${color.replace('#','')})`} strokeWidth={2.5} type="monotone"/>
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

export function Explanation({detail}:{detail:Detail}){
  return (
    <Panel title="Why did RiskPulse flag this?" note="Deterministic explanation generated from computed fields">
      <ol className="reasons">
        {detail.explanation.map((line,i)=><li key={i}>{line}</li>)}
      </ol>
    </Panel>
  );
}

export function Transmission({
  graph,
  initialAsset,
  compact=false,
  isDark=true,
  currency='INR'
}:{
  graph:Graph;
  initialAsset?:string;
  compact?:boolean;
  isDark?:boolean;
  currency?:CurrencyMode;
}){
  const [selected,setSelected]=useState<GraphNode|null>(null);
  useEffect(()=>{
    setSelected(old=>graph.nodes.find(n=>n.id===(old?.id||`asset:${initialAsset}`))||null);
  },[graph,initialAsset]);

  const groups=['event','entity','sector','asset','portfolio'],positions=new Map<string,{x:number;y:number}>();
  groups.forEach((type,col)=>{
    const nodes=graph.nodes.filter(n=>n.type===type);
    nodes.forEach((n,i)=>positions.set(n.id,{x:20+col*218,y:55+(i+.5)*500/Math.max(nodes.length,1)}));
  });

  const paths=selected?graph.risk_paths.filter(p=>p.nodes.includes(selected.id)):graph.risk_paths,active=new Set(paths.flatMap(p=>p.nodes));

  return (
    <>
      <div className="map-wrap">
        <svg className={compact?'transmission compact':'transmission'} viewBox="0 0 1100 590" role="group" aria-label="Computed event to portfolio risk transmission graph">
          <defs>
            <linearGradient id="activeBeamDark" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="50%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#f43f5e" />
            </linearGradient>
            <linearGradient id="activeBeamLight" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0284c7" />
              <stop offset="50%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#e11d48" />
            </linearGradient>
            <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Group Headings */}
          {groups.map((t,i)=>(
            <text key={t} x={100+i*218} y={26} textAnchor="middle" className="map-heading">
              {t.toUpperCase()}
            </text>
          ))}

          {/* Static Background Edges */}
          {graph.edges.map((e,i)=>{
            const a=positions.get(e.source)!,b=positions.get(e.target)!,enabled=active.has(e.source)&&active.has(e.target);
            const edgeColor = isDark
              ? (enabled ? 'rgba(56, 189, 248, 0.35)' : 'rgba(255, 255, 255, 0.08)')
              : (enabled ? 'rgba(2, 132, 199, 0.35)' : 'rgba(203, 213, 225, 0.7)');
            return (
              <path
                key={`base-${i}`}
                d={`M${a.x+174},${a.y} C${a.x+203},${a.y} ${b.x-25},${b.y} ${b.x},${b.y}`}
                fill="none"
                stroke={edgeColor}
                strokeWidth={1+e.weight*1.5}
              >
                <title>{e.meaning}: {e.weight.toFixed(3)}</title>
              </path>
            );
          })}

          {/* Glowing Animated Shockwave Beams on Active Paths */}
          {graph.edges.map((e,i)=>{
            const a=positions.get(e.source)!,b=positions.get(e.target)!,enabled=active.has(e.source)&&active.has(e.target);
            if (!enabled) return null;
            return (
              <path
                key={`beam-${i}`}
                d={`M${a.x+174},${a.y} C${a.x+203},${a.y} ${b.x-25},${b.y} ${b.x},${b.y}`}
                fill="none"
                stroke={isDark ? "url(#activeBeamDark)" : "url(#activeBeamLight)"}
                strokeWidth={2+e.weight*1.8}
                className="flow-beam"
                filter="url(#neonGlow)"
              />
            );
          })}

          {/* Interactive Nodes (Theme Aware) */}
          {graph.nodes.map(n=>{
            const p=positions.get(n.id)!;
            const isSel = selected?.id === n.id;
            
            let nodeFill: string;
            let nodeStroke: string;
            let textFill: string;

            if (isDark) {
              nodeFill = isSel ? 'rgba(56, 189, 248, 0.25)' : n.type === 'asset' ? 'rgba(30, 41, 59, 0.75)' : 'rgba(15, 23, 42, 0.85)';
              nodeStroke = isSel ? '#38bdf8' : active.has(n.id) ? 'rgba(56, 189, 248, 0.5)' : 'rgba(255, 255, 255, 0.12)';
              textFill = isSel ? '#ffffff' : active.has(n.id) ? '#38bdf8' : '#cbd5e1';
            } else {
              nodeFill = isSel ? 'rgba(2, 132, 199, 0.12)' : n.type === 'asset' ? '#f8fafc' : '#ffffff';
              nodeStroke = isSel ? '#0284c7' : active.has(n.id) ? '#38bdf8' : '#cbd5e1';
              textFill = isSel ? '#0284c7' : active.has(n.id) ? '#0f172a' : '#334155';
            }

            return (
              <g
                key={n.id}
                role="button"
                tabIndex={0}
                aria-label={`Inspect ${n.label}`}
                onClick={()=>setSelected(n)}
                onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(n);}}}
                className="graph-node"
              >
                <rect
                  x={p.x}
                  y={p.y-17}
                  width={174}
                  height={34}
                  rx={8}
                  fill={nodeFill}
                  stroke={nodeStroke}
                  strokeWidth={isSel ? 2 : 1}
                  filter={isSel ? 'url(#neonGlow)' : undefined}
                />
                <text
                  x={p.x+10}
                  y={p.y+4}
                  fill={textFill}
                  fontSize={11}
                  fontWeight={isSel ? 700 : 600}
                >
                  {n.type==='asset'?`${n.label} · ${money(n.value||0, currency)}`:label(n.label).slice(0,24)}
                </text>
                <title>{n.label} · click to inspect evidence and transmission</title>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="map-footer">
        <span><b>{graph.risk_paths.length}</b> unique asset paths</span>
        <b>{graph.total_propagated_risk.toFixed(3)} portfolio risk points</b>
        <span>Weighted exposure <b>{money(graph.exposure.weighted_exposure, currency)}</b></span>
      </div>

      {selected ? (
        <div className="node-detail">
          <div>
            <span className="eyebrow">SELECTED {selected.type.toUpperCase()}</span>
            <h3 style={{fontSize: 16, marginTop: 4}}>{selected.issuer||selected.label}</h3>
            <p style={{marginTop: 6}}>{selected.mapping_reason||selected.reason||'Connected position in transmission path.'}</p>
          </div>
          {selected.type==='asset' ? (
            <dl className="node-values">
              {[
                ['Asset value',money(selected.value||0, currency)],
                ['Sector',selected.sector],
                ['Sensitivity',(selected.sensitivity||0).toFixed(2)],
                ['Event exposure',money(selected.event_exposure||0, currency)],
                ['Scenario loss',money(selected.scenario_loss||0, currency)],
                ['Portfolio weight',`${((selected.portfolio_weight||0)*100).toFixed(1)}%`]
              ].map(([k,v])=>(
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p style={{alignSelf: 'center', fontFamily: 'var(--font-mono)'}}>
              <b>{paths.length}</b> connected asset paths · <b>{money(paths.reduce((s,p)=>s+p.weighted_exposure,0), currency)}</b> weighted exposure
            </p>
          )}
        </div>
      ) : (
        <p className="formula">
          Click a node to inspect exposure. Flowing light beams highlight active transmission from the event into the portfolio. {graph.units}
        </p>
      )}
    </>
  );
}

export function Attribution({
  result,
  cid,
  currency='INR'
}:{
  result:Result;
  cid:string;
  currency?:CurrencyMode;
}){
  return (
    <>
      <div className="grid-equal">
        <Panel title="Loss attribution by sector" note="Signed conditional loss">
          <Plot data={result.sector_losses.map(x=>({...x,loss_M:x.loss/1e6}))} x="sector" y="loss_M" bar color="#f43f5e" currency={currency}/>
        </Panel>
        <Panel title="Scenario outcome" note="Reconciled from individual positions">
          <div className="outcome">
            <div>
              <span>Portfolio before</span>
              <b>{money(result.portfolio_before, currency)}</b>
            </div>
            <ArrowRight size={22} style={{color: '#38bdf8', filter: 'drop-shadow(0 0 6px rgba(56, 189, 248, 0.5))'}}/>
            <div>
              <span>Portfolio after</span>
              <b>{money(result.portfolio_after, currency)}</b>
            </div>
          </div>
          <div className="loss-callout">
            <span>Conditional {result.absolute_loss<0?'gain':'drawdown loss'}</span>
            <strong>{money(Math.abs(result.absolute_loss), currency)}</strong>
            <small>{result.loss_percentage.toFixed(3)}% signed scenario loss · synthetic wholesale assumptions</small>
          </div>
        </Panel>
      </div>

      <Panel title="Top 5 loss contributors" note="Open a position to trace event → entity → sector → asset">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Position / issuer</th>
                <th>Sector</th>
                <th>Sensitivity</th>
                <th>Exposure weight</th>
                <th>Scenario loss</th>
              </tr>
            </thead>
            <tbody>
              {result.top_contributors.map(a=>(
                <tr key={a.asset_id}>
                  <td>
                    <Link href={`/risk-map?event=${cid}&asset=${a.asset_id}`}>
                      <strong>{a.asset_id} ↗ {a.issuer}</strong>
                      <small>{label(result.event_type)} · {a.asset_type}</small>
                    </Link>
                  </td>
                  <td>{a.sector}</td>
                  <td><span style={{fontFamily: 'var(--font-mono)'}}>{a.sensitivity.toFixed(2)}</span></td>
                  <td><span style={{fontFamily: 'var(--font-mono)'}}>{a.mapping_weight.toFixed(2)}</span></td>
                  <td><b style={{color: '#f43f5e', fontFamily: 'var(--font-mono)'}}>{money(a.loss, currency)}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="formula">{result.formula}</p>
      </Panel>
    </>
  );
}

export function StressLab({
  detail,
  currency='INR'
}:{
  detail:Detail;
  currency?:CurrencyMode;
}){
  const c=detail.cluster,base=detail.result;
  const [scenario,setScenario]=useState('Moderate'),[intensity,setIntensity]=useState(1),[impact,setImpact]=useState(c.raw_impact),[exposure,setExposure]=useState(1),[rate,setRate]=useState(base?.inputs.rate_shock||0),[equity,setEquity]=useState(base?.inputs.equity_shock||0);
  const [result,setResult]=useState(base),[error,setError]=useState(''),[busy,setBusy]=useState(false),[custom,setCustom]=useState(false);

  useEffect(()=>{
    if(!custom)return;
    let current=true;
    setBusy(true);
    const t=setTimeout(()=>{
      request<Result>('/api/v2/what-if',{cluster_id:c.id,impact,intensity,exposure_scale:exposure,rate_shock:rate,equity_shock:equity})
        .then(r=>{if(current){setResult(r);setError('');}})
        .catch(e=>{if(current)setError(e.message);})
        .finally(()=>{if(current)setBusy(false);});
    },250);
    return()=>{current=false;clearTimeout(t);};
  },[c.id,impact,intensity,exposure,rate,equity,custom]);

  if(!base) return <div className="empty">No synthetic scenario is defined for this event type.</div>;

  const sliders=[
    ['Event impact',impact,setImpact,0,10,.01,'/10'],
    ['Shock intensity',intensity,setIntensity,0,3,.05,'×'],
    ['Exposure assumption',exposure,setExposure,0,2,.05,'×'],
    ['Interest rate shock',rate*100,(v:number)=>setRate(v/100),-10,10,.1,'pp'],
    ['Equity shock',equity*100,(v:number)=>setEquity(v/100),-100,100,1,'%']
  ] as const;

  return (
    <>
      <Panel title="Base · Moderate · Severe Scenarios" note="Base: zero shocks. Moderate: original assumptions. Severe: 1.75× shocks.">
        <div className="scenario-buttons">
          {detail.comparison.map(r=>(
            <button
              key={r.name}
              onClick={()=>{
                setScenario(r.name!);
                setResult(r);
                setIntensity(r.inputs.intensity);
                setImpact(r.inputs.impact);
                setExposure(r.inputs.exposure_scale);
                setRate(r.inputs.rate_shock);
                setEquity(r.inputs.equity_shock);
                setCustom(false);
                setBusy(false);
              }}
              className={`scenario-choice ${!custom&&scenario===r.name?'chosen':''}`}
            >
              <span>{r.name} Scenario</span>
              <b>{money(r.portfolio_after, currency)}</b>
              <small>Signed loss {money(r.absolute_loss, currency)}</small>
            </button>
          ))}
        </div>
        <Plot data={detail.comparison.map(r=>({scenario:r.name,loss_M:r.absolute_loss/1e6}))} x="scenario" y="loss_M" bar color="#f59e0b" currency={currency}/>
      </Panel>

      <Panel title="Interactive What-If Scenario Lab" note="Drag any shock assumption to trigger real-time repricing through the asset-level stress engine.">
        <div className="whatif-controls">
          {sliders.map(([name,value,set,min,max,step,unit])=>(
            <label key={name}>
              <span>
                {name}
                <b>{value.toFixed(2)}{unit}</b>
              </span>
              <input
                type="range"
                aria-label={name}
                value={value}
                min={min}
                max={max}
                step={step}
                onChange={e=>{set(Number(e.target.value));setCustom(true);}}
              />
            </label>
          ))}
        </div>
        <div className="lab-status" role="status">
          <span>
            {busy ? '⚡ Recalculating scenario repricing…' : custom ? '✓ Interactive what-if calculation applied' : `${scenario} scenario active`}
          </span>
          {result&&<span>Worst asset: <b style={{color: '#f43f5e'}}>{result.worst_asset.asset_id}</b> · Worst sector: <b style={{color: '#f43f5e'}}>{result.worst_sector.sector}</b></span>}
        </div>
        {error&&<div role="alert" className="alert error">{error}</div>}
      </Panel>

      {result&&(
        <div style={{opacity: busy ? 0.6 : 1, transition: 'opacity 0.2s'}}>
          <Attribution result={result} cid={c.id} currency={currency}/>
        </div>
      )}
    </>
  );
}
