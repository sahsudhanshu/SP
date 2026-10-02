# V2 upgrade audit

Baseline verification: 25 tests passed in 4.25 s, production Next.js build passed, both servers responded successfully, and reset → next → stress reproduced INR 100,000,000 → 97,182,968.80 (loss 2,817,031.20). Existing measured diagnostics are retained as metrics-v1.json. Audit completed before V2 implementation.

| CURRENT STATE | UPGRADE | REASON | FILES AFFECTED | RISKS | TEST PLAN |
|---|---|---|---|---|---|
| FastAPI, SQLite JSON records, six tables; V1 endpoints | Add versioned API and history table | Preserve contract while exposing fused decisions | backend/main.py, store.py, v2.py | Concurrent replay, duplicate history | Existing 25 tests; replay/history tests |
| FinBERT singleton, per-text LRU, TF-IDF plus rules | Batched unique-text inference and richer classification evidence | CPU inference dominates latency; measure actual benefit | services/nlp.py, scripts/evaluate_v2.py | Batch output shape, cache equivalence | Mock contracts and real local model benchmark |
| 12 news + 12 social records, social copies news | Cluster with constrained TF-IDF; exact-copy groups | Avoid counting correlated copies as independent corroboration | services/intelligence.py | False merges, confidence inflation | Duplicate, conflicting issuer, recency, disagreement tests |
| Rule impact, dictionary exposure, deterministic stress | Credibility, recency, confidence-aware priority; graph; what-if | Trace event → portfolio and distinguish severity from evidence | services/propagation.py, scenario_analysis.py | Double counting; confusing priority with loss probability | Path reconciliation, monotonic scenario, attribution tests |
| One dashboard with local page state | Reuse styles and preserve V1 at /legacy; URL-based V2 workspace | Institutional navigation and explainability | frontend/components, app routes | UI regressions, stale what-if results | Production build; browser desktop/mobile and control checks |
| V1 demo, diagnostics, seven-slide deck | Full-chain demo, quality validator, measured comparison, seven-slide V2 deck | Reproducibility and jury evidence | scripts, docs, screenshots | Synthetic results overinterpreted | Full replay; rendered slide QA; label assumptions |

Architecture remains Next.js → FastAPI → SQLite and local NLP. No external graph service, LLM, or paid API is required. The finance engine and seed portfolio remain the V1 source of truth. New conditional stress outputs are not probability-weighted expected losses. Source assumptions are configurable and uncalibrated. Demo recency uses the latest replay timestamp; mixed/live data uses UTC wall time.

Audit findings: the paired social dataset is correlated; V1 high-impact counts count observations; history is reconstructed rather than snapshotted; the UI has no shareable analysis routes; CPU model calls are serial. V1 UI and finance formulas are retained instead of duplicating them. V2 centralizes fusion and graph functions and uses one aggregate dashboard endpoint. A disk inspection also found the analyze return/automatic-stress tail absent despite the running baseline server retaining it; restore this tail and verify regression tests before release.
