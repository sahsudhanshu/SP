# RiskPulse AI V2: five technical differentiators

## 1. Multi-source signal fusion
**Problem:** Repeated headlines can look like multiple independent events. The demo's social posts deliberately repeat the news texts.

**Approach:** Collapse normalized copies. Group related distinct texts using event-type, issuer, sector and 48-hour constraints plus domain-expanded TF-IDF similarity. Compare with a cluster anchor to limit transitive over-merging.

**Implementation:** `backend/services/intelligence.py`. Exact copies contribute one representative, selected by configurable source credibility. Distinct evidence is weighted by credibility and recency. Agreement measures sentiment dispersion. A bounded diversity bonus requires distinct wording and publishers, but does not establish independence. The 24 fixtures form 12 clusters.

**Why it matters:** Portfolio prioritization counts events instead of headline volume. The hero has two sources but only one distinct text, so it receives no extra corroboration bonus.

## 2. Risk propagation graph
**Problem:** A negative headline alone does not identify the affected balance-sheet positions.

**Approach:** Trace event → issuer → sector → asset → portfolio using the actual position inventory. Show direct matches and systemic spillover separately.

**Implementation:** `backend/services/propagation.py`. Each asset has one accounting path. Edge weights are exposure mapping (1 issuer / 0.8 sector / 0.35 systemic), sector membership (1), event sensitivity, and portfolio weight. Sum `effective risk × product(edge weights)` over unique assets. The hero produces 12 paths and 3.570531 portfolio risk points. The graph is a visualization of the enumerated paths, not an unrestricted graph traversal.

**Why it matters:** An analyst can inspect the exact inputs behind every exposure. Shared nodes cannot duplicate a position's contribution. Risk points are neither currency nor probability.

## 3. Confidence-aware impact scoring
**Problem:** Severe but weakly supported reports should not receive the same priority as well-supported evidence.

**Approach:** Keep V1 severity/impact and conditional financial loss intact. Introduce an independent prioritization score: `raw impact × recency × evidence confidence`.

**Implementation:** Raw impact is the credibility/recency weighted mean of representative V1 scores. Evidence quality averages `min(sentiment confidence, event confidence) × source reliability`. Distinct-publisher/text support adds at most 0.08, total capped at 0.95, then multiplied by agreement. Recency is `exp(-ln(2) × age_hours / half_life_hours)`. Defaults and source overrides live in `data/risk_config.json`. Low <3, Medium ≥3, High ≥6, Critical ≥8. The hero is 9.78 × 1 × 0.855 = 8.3619, Critical.

**Why it matters:** Priority reflects uncertainty and age without misrepresenting confidence as a calibrated loss probability. Demo time follows replay timestamps and remains deterministic offline.

## 4. Exposure-aware stress testing
**Problem:** Applying the same market shock to every position ignores event relevance and financial structure.

**Approach:** Preserve the V1 finance engine and apply the selected scenario through position mapping and event sensitivity. Approximate bond response to interest rates using duration.

**Implementation:** `backend/services/scenario_analysis.py` wraps `finance.py`. Loss is `-value × shock × impact/10 × intensity × mapping × sensitivity × exposure multiplier`, with final asset return capped to [-1,1]. Bond shock also includes `-duration × rate_change`. Base intensity 0, Moderate 1, Severe 1.75. What-if controls vary impact, intensity, exposure scale, rates and equities without changing balance-sheet values.

**Why it matters:** Analysts can compare assumptions while retaining a reproducible original hero result: INR 100M → 97.1829688M. The 1.5× scenario loses INR 4.2255468M. These are conditional synthetic repricings, not expected losses.

## 5. Explainable loss attribution
**Problem:** A portfolio loss total is difficult to challenge without its contributors.

**Approach:** Reconcile every total to positions and sectors. Link contributors back to the graph and expose source/model/scoring evidence.

**Implementation:** Sector sums and top-five contributors use the same computed asset losses. Hero Energy loss is INR 1.679226M; largest position is EQ_01 at INR 0.581910M. `/audit` and JSON exports expose the evidence. Explanations use deterministic templates, never generated financial claims. SQLite `RiskHistory` records actual arrivals and transitions; polling does not create history.

**Why it matters:** A jury or analyst can trace and reproduce a number, change an assumption, and observe the resulting change. No assertion of bank deployment, regulatory compliance, real-market prediction, or validated source credibility is made.
