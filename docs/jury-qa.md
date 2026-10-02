# Jury questions and defensible answers

**Why FinBERT?** It provides an existing financial-language sentiment model that runs locally on CPU. We retain its signed score P(positive) minus P(negative), model label and confidence. This choice supports offline repeatability; it is not proof that FinBERT is optimal for all financial text.

**Why not GPT for everything?** The required tasks are narrow and auditable. A local sentiment model plus explicit classification, mapping and repricing rules keeps the hero independent of remote APIs and makes every financial number reproducible. No generative model writes our analyst explanations.

**How is impact calculated?** V1 uses 1 + 9 times a weighted sum: severity 45%, sentiment magnitude 20%, entity relevance 10%, source assumption 10%, exposure 15%. Components are bounded and the result is 1–10. V2 fuses representative scores and separately discounts priority for evidence confidence and age. Legacy source assumptions (.85 news/.55 social) stay inside the preserved V1 score; V2 configurable credibility (.90/.60) weights fusion and confidence. These are separate, explicitly disclosed stages, not fitted probabilities.

**How do you avoid duplicate news?** Normalize copy prefixes, URLs, tags, punctuation and whitespace. Copies supply one evidence representative. Related wording must satisfy TF-IDF similarity and event/time/entity constraints. We show observations, publishers, distinct texts and collapsed copies separately. Distinct wording alone is not proof of independent reporting.

**How is severity determined?** Explicit event-category base values plus severe-event keywords. The model does not learn market impact from returns. Audit fields expose the severity factors and contribution weights.

**How does risk reach the portfolio?** Match a named issuer at weight 1, affected sectors at .8, or broad geopolitical/macro spillover at .35. Multiply by event sensitivity and portfolio weight. Every position appears once in the transmission ledger.

**Why synthetic stress assumptions?** No calibrated institutional exposure/loss dataset was supplied. Synthetic positions and shocks make the demo transparent and reproducible. They illustrate a method without claiming real-bank expected losses.

**What happens when APIs fail?** Demo mode uses local CSVs and locally cached model weights. Missing NewsAPI credentials, outage or unusable articles triggers a visibly labelled demo fallback. If FinBERT is unavailable, a labelled financial lexicon fallback runs. Its scores can differ, so the exact INR 2.817M hero requires the cached FinBERT model. Social data remains synthetic even with live news.

**How would this scale?** Current clustering recomputes pairwise candidates and SQLite uses simple JSON rows. For larger workloads, index candidates by time/entity, persist cluster membership, queue inference, use a relational store with transactions and instrument adapters, and benchmark throughput/backpressure. We have not measured production-scale performance.

**How would a bank validate it?** Use licensed timestamped text, independently adjudicated event/entity labels, held-out issuers and time periods, source-provenance checks, confidence calibration, and instrument-specific pricing. Backtest scenarios against observed moves and compare exposure mapping with risk teams. Add access control, immutable model/config versions, monitoring, review and approval before operational use.

**How do you prevent hallucinated signals?** The UI quotes input records. Entity links come from a finite dictionary. Classifications include cosine similarity and keyword evidence. Financial outputs come from visible formulas and position data. Explanations interpolate computed fields. Errors and false classifications remain possible; we make them inspectable rather than claim to eliminate them.

**What are the limitations?** 24 small correlated synthetic examples, limited entities and languages, lexical similarity, heuristic confidence, fixed source credibility, no hedge/netting logic, no nonlinear derivatives repricing, no calibrated loss model, no authentication or production deployment controls. Recency only changes when the replay clock advances in demo mode. Positive scenario returns appear as negative signed losses.

**What differs from sentiment analysis?** The output includes event grouping, source evidence, exposure paths, position-level conditional repricing, reconciled attribution and counterfactual assumptions. Sentiment is one input to the risk workflow.

**What is AI/ML versus deterministic logic?** FinBERT sentiment is transformer inference. Event classification and clustering use TF-IDF cosine similarity supplemented by explicit rules. Entity dictionaries, credibility, recency, fusion weights, risk thresholds, graph construction, valuation and explanations are deterministic. No new model was trained for this upgrade.

**What performance gain is supported?** On this local CPU, three alternating-order rounds measured median sequential sentiment inference at 24.833 ms/record and batch-of-eight inference at 20.713 ms/record, with identical rounded scores and labels. Model load is excluded. Historical V1 total pipeline timing is not a controlled comparator. Results may change with hardware, sequence length, load or batch size.

**Why does a copied social signal not raise confidence?** The demo intentionally contains a news copy. Showing no corroboration gain demonstrates evidence discipline. To demonstrate strengthening, ingest a genuinely distinct related observation; the history records strengthening only if its computed effective risk actually rises.
