# RiskPulse synthetic demonstration data

All data was authored specifically for this prototype. No S&P Global, Crisil, client, proprietary, or real issuer records are used. Company names are fictional.

| File | Purpose | Records | Fields |
|---|---|---:|---|
| news.csv | Financial-news input | 12 | id, timestamp, source, source_type, headline, text, sector, expected_event, expected_sentiment |
| social_posts.csv | X-style investor discussion input | 12 | Same fields, with social source designation |
| portfolio.csv | Wholesale-banking positions | 12 | asset_id, asset_type, issuer, sector, value, currency, duration, risk_factors, sensitivities |
| scenarios.json | Stress assumptions | 5 | id, event_type, name, shocks by asset class, rate_change, assumptions |
| risk_config.json | Fusion and priority settings | 1 | half-life, cluster window, similarity threshold, source reliability, risk-level thresholds |

Dates: synthetic records on 1 October 2026 between 09:00 and 09:44 IST. These are demonstration timestamps, not publication dates for actual events. The replay runs in fixed news/social pairs and does not claim to be a live market stream.

The portfolio totals INR 100,000,000 across five asset classes and six sectors. The derivative value is a synthetic carrying value, not notional. Event sensitivities in [0,1], source reliability, scenario shocks, duration, and spillover weights are synthetic business assumptions. Government bonds also receive systemic macro/geopolitical spillover. Issuer mapping takes precedence over sector mapping, avoiding double counting. Each social row is the matching news sentence with the prefix `Investor discussion:` and the suffix `#markets`. After those markers are removed, the twelve pairs are exact copies, not independent reports. They must not be treated as corroboration.

Expected event and sentiment labels are author labels used only by the evaluation script. The inference engine never reads these labels or the CSV sector annotation when analyzing text. Evaluation on these 24 examples is a small diagnostic, not a benchmark. No classifier training uses the test records.

Regenerate: `python scripts/seed_data.py`. Startup imports the CSV/JSON into SQLite idempotently. Reset clears signals and stress results and replays six ordinary records. Restart resumes processed demo records; the frontend must be open with replay enabled to advance automatically.

Optional live headlines are fetched at runtime: NewsAPI when a key is set, otherwise public RSS. Demo rows are used only if every live source fails. Social posts stay in this synthetic file. Live headlines are stored in SQLite and are not part of the submitted dataset.
