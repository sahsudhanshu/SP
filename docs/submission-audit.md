# V2 final audit (supersedes historical V1 status below)

Application, APIs, demo, model evaluation, 59 tests and production build passed. Every major page was checked in a desktop browser and at a 390px mobile viewport. Risk map nodes, deep links, scenario choices, what-if recomputation, alerts/empty state, timeline, heatmap, audit, evaluation, reset/replay and live-news fallback were exercised. Backend outage/recovery was checked. The final seven-slide PPTX and seven-page PDF were rendered and inspected, with the architecture and actual application screenshots updated. See v2-final-report.md for all 12 report sections, measured results and limitations.

Repository staging access was restored for this upgrade. Publication verification is recorded separately in repository-publish-status.md. The previous V1 Git blocker described below is historical.

The candidate metadata and recorded video remain human submission inputs. Successful authenticated live-news ingestion is unverified because no NewsAPI key is supplied. No external application or official hackathon submission has been made.

---
# Final submission audit

Local implementation directory: `C:\Users\Sudhanshu\Desktop\Projects\SP`.
Audit date: 2 October 2026 (IST).

| Requirement | Status | Evidence |
|---|---|---|
| Frontend starts | PASS | Next.js local server and browser walkthrough |
| Backend starts / health responds | PASS | FastAPI running on port 8000; health reports finbert |
| Two source types | PASS | 12 news and 12 social rows; source filtering verified |
| Offline demo | PASS | Local datasets; model cache; forced fallback tests use no network |
| Financial sentiment | PASS | Actual FinBERT inference and evaluation; labelled lexicon fallback tested |
| Event classification | PASS | Five required categories plus OTHER, automated tests |
| Impact scoring / explainability | PASS | Configurable weights, factors, evidence and decomposition |
| Entity extraction | PASS | Issuer, sector, country/instrument dictionary extraction |
| Structured signals / API | PASS | All required endpoints, Pydantic input validation |
| Portfolio / exposure | PASS | INR 100M, 12 positions, calculated mapping |
| High-impact automatic stress | PASS | Threshold ≥8; persisted automatic result |
| Before/after, asset and sector losses | PASS | Hand-calculated tests and end-to-end reconciliation |
| Dashboard charts and event details | PASS | Overview, intelligence, portfolio, stress and scenario views verified |
| Automated tests | PASS | 25 tests passed; regression for both transformer output formats |
| Production frontend build | PASS | Compilation, type checks and static page generation completed |
| Dataset documentation | PASS | data/README.md documents synthetic source, fields and assumptions |
| README, environment example, MIT licence | PASS | Root files exist; exact local commands documented |
| Architecture image | PASS | docs/architecture.png, 2560 × 1440, editable source diagram in PPTX |
| Seven-slide deck | PASS | PDF and editable PPTX, screenshot evidence and measured diagnostics |
| Pitch and recording scripts | PASS | Five-minute live pitch and ten-minute recording script |
| No core TODOs / placeholder APIs | PASS | Analysis and stress outputs computed; runtime failures shown to user |
| No hardcoded secrets / confidential data | PASS | Source uses environment key; all submitted data synthetic |
| FinBERT weights excluded from Git | PASS | .models is ignored; one-time download script provided |
| Live-source success | NOT VERIFIED | No user NewsAPI key; missing-key and simulated-outage paths pass |
| Candidate metadata | PENDING | Full name, college email and campus must be supplied |
| Public repository / code push | BLOCKED | User selected sahsudhanshu/SP. GitHub browser confirms public, empty repository. Sandbox denied .git/config and index.lock writes despite permission grant. Browser is signed out, so authenticated UI upload is also unavailable. No commit or push was completed. scripts/publish.ps1 prepares a normal-terminal push without force. |
| Video recorded and hosted | PENDING | Ten-minute walkthrough must be recorded and uploaded as YouTube Unlisted |
| Repository/video incognito verification | PENDING | Perform after push/upload |
| Official submission form / deadline | PENDING | Submit final links through the official form before communicated deadline |

## Measured result

FinBERT hero signal: GEOPOLITICAL, impact 9.78. Direct exposure INR 42M (Energy and Industrials), weighted exposure INR 59.5M, high-sensitivity exposure INR 28M. Baseline INR 100M, after INR 97,182,968.80, computed loss INR 2,817,031.20 (2.817%). These are synthetic scenario values, not market forecasts.

24 synthetic examples: 100% event-label agreement, 91.67% sentiment-label agreement, mean pipeline latency about 27.4 ms, mean stress execution about 0.645 ms across 100 runs. See metrics.json for exact measured values and caveats. Startup excluded; repeated text caching and shared vocabulary make this a diagnostic, not an independent benchmark.

The official attachment is a requirements reference. It is not included in the repository and does not independently authorize account actions or publication. The user separately requested pushing to the named GitHub repository.

