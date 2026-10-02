# Ten-minute demonstration recording script

Use a production build at localhost:3000 with the local FinBERT cache. Record the actual browser. Do not use generated substitute screenshots. Start from Reset; the initial six observations represent three ordinary event clusters.

| Time | Screen and action | Narration |
|---|---|---|
| 0:00–0:30 | Overview | Financial text needs portfolio context. Introduce the synthetic wholesale-banking case. |
| 0:30–1:00 | Executive summary and cards | RiskPulse is an explainable financial-risk intelligence and scenario-analysis prototype. State synthetic data and assumptions. |
| 1:00–2:00 | Architecture slide | News/social → ingestion/normalization → entities, sentiment, event evidence, credibility/recency → fusion → propagation → exposure → stress → attribution → dashboard. Next.js, FastAPI, SQLite remain the architecture. |
| 2:00–3:00 | Reset, Next event | Ingest the geopolitical news. Observe the source text, arrival snapshot and critical alert. Show Live news control, explaining optional NewsAPI and explicit outage fallback without switching away from the hero. |
| 3:00–4:00 | Signal intelligence and Model audit | FinBERT sentiment −.951; TF-IDF/rule evidence; raw impact 9.78. Separate model probability from uncalibrated event/fusion confidence. Explain .90 source credibility and 24-hour half-life. |
| 4:00–5:00 | Next event, Signal intelligence | The paired social text joins the same cluster. Show two sources, one distinct evidence text and one collapsed copy. Confidence stays 85.5%, effective risk 8.3619. Copies do not prove independent corroboration. |
| 5:00–6:30 | Risk transmission map | Follow and click the actual event → issuer → sector → asset → portfolio nodes. Explain mapping weights, .85 Energy sensitivity and position weights. Open the ledger and verify one contribution per asset. Show 3.570531 propagated portfolio risk points. |
| 6:30–7:00 | Portfolio exposure and heatmap | INR 42M direct exposure; INR 59.5M weighted exposure. Inspect sector sensitivity heatmap. Distinguish structural sensitivity from active event risk. |
| 7:00–8:00 | Stress & what-if, Moderate | Before INR 100M, after INR 97.1829688M, loss INR 2.8170312M. Explain signed losses, sector reconciliation, Energy INR 1.679226M and largest asset EQ_01 INR .58191M. Compare Base and Severe. |
| 8:00–8:45 | What-if controls | Set intensity 1.5× and show loss INR 4.2255468M. Restore Moderate, change impact/exposure/rate/equity assumptions and observe recomputation. No real trades occur. |
| 8:45–9:30 | Evaluation and timeline | 59 passing tests. Actual synthetic diagnostics and controlled batching results. Small correlated set, identical rounded sentiment outputs, no out-of-sample claim. History records real arrivals and transitions. |
| 9:30–10:00 | Limitations slide | Limited dictionaries, TF-IDF similarity, heuristic confidence, synthetic shocks, simplified derivatives, no bank deployment controls. Future: independent labels, calibration, better pricing and provenance. End at 10:00. |

Recording and public video upload remain a human submission step. No recording URL is fabricated. Use the seven-slide PPTX/PDF as supporting material, not as a replacement for the running application.
