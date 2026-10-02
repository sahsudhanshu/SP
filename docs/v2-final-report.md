# RiskPulse AI V2 final report

## 1. Already present
Next.js/React/TypeScript/Tailwind/Recharts frontend; FastAPI/SQLite backend; local FinBERT sentiment, TF-IDF/rule event classification, entity dictionaries, impact scoring, exposure mapping, synthetic wholesale portfolio stress calculations, deterministic replay/reset, optional news ingestion, 25 tests and a seven-slide V1 deck.

## 2. Upgrades
Added an intelligence layer around the existing finance engine. Preserved V1 APIs, seed data and formulas, original tests, and V1 interface at `/legacy`. New homepage and shareable V2 routes use the existing design system. Restored the analyze return/automatic-stress tail found missing on disk during the audit and verified its regression behavior.

## 3. Architecture
News/social → normalization and ingestion → entities, FinBERT, explainable event classification → credibility/recency-aware fusion → structured event cluster → weighted transmission graph → sector/portfolio exposure → synthetic scenario repricing → loss attribution → deterministic explanation. Next.js, FastAPI and SQLite remain in place. RiskHistory adds durable arrival snapshots.

## 4. Features
Interactive risk map with asset details and transmission ledger; constrained TF-IDF clustering and copy collapse; source weights; exponential recency; separate impact/confidence/effective-risk fields; four risk levels; Base/Moderate/Severe comparison; five immediate what-if controls; sector/asset attribution with graph links; analyst explanations; executive summary; timeline and four history charts; alert filtering; sensitivity heatmap; audit/export; actual measured evaluation; clear demo/live/fallback/loading/error/empty states. Runtime checks covered desktop and 390px mobile layouts without whole-page horizontal overflow.

## 5. APIs
Added GET `/api/v2/dashboard`, `/clusters`, `/clusters/{id}`, `/propagation/{id}`, `/scenarios/{id}`, `/history`, `/alerts`, `/heatmap`, `/audit/{id}`, `/evaluation`, `/configuration`; POST `/api/v2/what-if`. All original endpoints remain. Inputs enforce ranges and finite numbers, missing identifiers return 404, unsupported scenarios return 422.

## 6. New files
Core: `backend/v2.py`, `backend/services/intelligence.py`, `propagation.py`, `scenario_analysis.py`, `backend/tests/test_v2.py`, `data/risk_config.json`, `frontend/components/RiskWorkspace.tsx`, `RiskVisuals.tsx`, `LegacyDashboard.tsx`, `frontend/lib/v2-types.ts`, route wrappers. Reproducibility: `scripts/validate_data.py`, `evaluate_v2.py`, upgraded `run_demo.py`. Documents: audit plan, model specification, technical differentiators, jury Q&A, updated pitch/recording scripts, V1/V2 metrics, data-quality and demo-result JSON, updated presentation/architecture, final report, and V2 screenshots.

## 7. Tests before
25 passing tests, successful production build, active backend/frontend, original FinBERT hero confirmed before V2 implementation.

## 8. Tests after
59 passing tests (34 new cases, all original 25 retained), latest run 9.42 seconds. Next.js production build passed with static V2 routes and preserved `/legacy`. Additional browser checks verified asset-node details, deep links, all routes, mobile widths, scenario controls, what-if recalculation, alert empty states, missing-key live fallback, reset and hero replay, visible backend outage and recovery. All seven deck slides and rendered PDF pages were inspected. Data validation checked 41 records: 24 source records, 12 positions, 5 scenarios; 12 expected text copies, no missing fields or invalid records, 6 source records without named portfolio issuer matches.

## 9. Actual measured metrics
| Metric | V1 saved baseline | V2 measured |
|---|---:|---:|
| Synthetic observations | 24 | 24 |
| Event-label agreement | 100% | 100% |
| Sentiment-label agreement | 91.67% | 91.67% |
| Mean NLP/entity/impact pipeline ms per record | 27.438 | 22.073 |
| Mean stress calculation ms | 0.645 (includes SQLite scenario read) | 0.070 (pure calculation) |

V2 clustering yields 12 events. Fusion plus propagation over the evaluation set took 14.589 ms total. Historical pipeline timings are not a controlled comparison. In a separate controlled local CPU benchmark (three alternating-order rounds, caches cleared, batch size 8), median sequential sentiment inference was 24.833 ms/record versus 20.713 ms/record batched. Labels and rounded scores were identical. Warm cache measured .00734 ms/record and is not compared with cold inference as a claimed gain. Model loading, HTTP and SQLite are excluded from that controlled comparison. These small synthetic, correlated, author-labelled examples do not establish generalization or market prediction.

## 10. Demonstration
Reset → next news → next social → one geopolitical cluster → intelligence → risk map → asset details → exposure → Moderate stress → sector/top-five attribution → intensity 1.5× → audit and final summary. Original V1 loss remains INR 2,817,031.20, with portfolio INR 100,000,000 → 97,182,968.80. Hero source count 2; distinct texts 1; impact 9.78; confidence .855; effective risk 8.3619 Critical. Direct exposure INR 42M, weighted INR 59.5M, 12 paths, 3.570531 portfolio risk points. Intensity 1.5× loss INR 4,225,546.80. Energy loss at Moderate is INR 1,679,226; largest asset EQ_01 is INR 581,910.00.

## 11. Presentation
Exactly seven slides in editable PPTX and a seven-page PDF: RiskPulse AI; The Problem; From Signals to Portfolio Risk; Risk Propagation Architecture; Live Event → Exposure → Stress Test; Results + Explainability + Domain Impact; Limitations + Future Work. Slide 5 contains actual production risk-map and attribution screenshots. Architecture PNG updated. Five-minute pitch and ten-minute recording scripts cover the entire causal chain.

## 12. Remaining limitations
Synthetic positions and correlated source fixtures; limited dictionaries; lexical clustering; heuristic, uncalibrated confidence and source assumptions; no empirically fitted shocks or loss probability; simplified derivatives, no netting/hedging; local single-worker storage and ingestion. NewsAPI success requires credentials and was not verified; missing-key and simulated-outage fallbacks were verified. Social feed remains synthetic. Cached FinBERT is required for the exact hero numbers; labelled lexicon fallback has different scores. Model weights and local dependencies are excluded from source archives/Git. Candidate name, college email/campus and the human-recorded video URL remain submission inputs. No market-prediction, production-bank or regulatory claim.

## Top 5 differentiators to tell the jury
1. **Multi-source fusion that respects evidence:** collapse copied reports and disclose unverified independence.
2. **Calculated risk transmission paths:** trace actual portfolio positions with measurable edges and one contribution per asset.
3. **Confidence-aware prioritization:** distinguish severity, evidence strength and age without turning confidence into loss probability.
4. **Exposure-aware scenario analysis:** compare explicit assumptions and recalculate five counterfactual controls using the same valuation engine.
5. **Reconciled, explainable attribution:** connect every loss to its asset, sector, event, source evidence and assumptions.
