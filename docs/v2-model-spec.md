# V2 reproducibility and model specification

The unchanged V1 finance service is authoritative for the original stress result. New code wraps it rather than rewriting it. `/legacy` preserves the V1 workspace, and `/api/*` legacy routes retain their behavior. V2 routes use `/api/v2`.

## Data and time
The demo consists of 12 news and 12 explicitly correlated social texts, 12 positions worth INR 100M and five synthetic event scenarios. Initial reset processes six observations. Next news and next social produce the hero. Sources are fixtures, not actual current news. Source timestamps include timezone offsets.

All-demo priority calculations use the maximum replay timestamp. Once a manual/live observation is present, the model uses UTC wall time, so old demo observations decay. Copies cannot refresh recency unless selected as the stronger evidence representative. `RiskHistory` persists arrival-time score snapshots with both event/replay time and wall-clock recorded time. It does not retroactively overwrite history when time passes. Reset clears observations, tests and arrival history together under the local process locks. Use one backend worker for the prototype; multi-process ingestion needs a transactional queue.

## Evidence and accounting
Clustering uses event/issuer/sector/time constraints, domain synonym expansion, word/bigram TF-IDF cosine >= .42, and exact-copy collapse. Membership is recomputed in insertion order, so cluster identifiers derive from the first observation. This is lexical semantic similarity, not a learned embedding classifier. False merges and misses remain possible.

Source credibility values in `data/risk_config.json` are assumptions. Default news=.90, verified=.95, social=.60, unverified=.45. Existing ingestion accepts news/social; use exact publisher-name `source_overrides` to assign verified/unverified credibility. No publisher is automatically certified. Edit config locally, then read `/api/v2/configuration` to inspect the active values. The JSON is validated when loaded.

Effective risk is distinct from monetary stress. The moderate scenario uses fused raw impact, preserving the hero's strongest exact-copy representative. The formula and clipping rules are returned with every result. Positive shocks create negative signed losses. There is no hedging, netting, PD/LGD model, historical calibration, stochastic dependence model or nonlinear derivatives pricing.

## API additions
GET `/api/v2/dashboard`, `/clusters`, `/clusters/{id}`, `/propagation/{id}`, `/scenarios/{id}`, `/history`, `/alerts?level=ALL`, `/heatmap`, `/audit/{id}`, `/evaluation`, `/configuration`.

POST `/api/v2/what-if`: `cluster_id`, optional impact [0,10], intensity [0,3], exposure_scale [0,2], rate_shock [-.1,.1], equity_shock [-1,1]. Fields reject non-finite values. Zero intensity or exposure means zero stress. Unknown cluster returns 404; OTHER without a scenario returns 422. GET comparisons never persist artificial history points.

## Reproduce
Start backend and frontend using the README. Run `python scripts/validate_data.py`, `python scripts/run_demo.py`, `python scripts/evaluate_v2.py`, and `python -m pytest backend/tests -q -p no:cacheprovider`. V2 evaluation writes metrics-v2.json without changing metrics-v1.json. Exact FinBERT hero values require locally cached ProsusAI/finbert weights; fallback mode remains operational and clearly labelled with different scores.

The benchmark alternates sequential/batched arm order for three rounds with result caches cleared. Model loading and one warmup call are excluded. Separate warm-cache timing is not compared to cold inference as an optimization claim. Pipeline timing excludes HTTP/SQLite and fusion; fusion plus graph construction has its own measured total. The original V1 stress timing included a scenario lookup whereas V2 pure stress timing does not, so that row is descriptive rather than a controlled speedup comparison.
