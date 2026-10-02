# RiskPulse synthetic demonstration data

All data was authored specifically for this prototype. No S&P Global, Crisil, client, proprietary, or real issuer records are used. Company names are fictional.

| File | Purpose | Records | Fields |
|---|---|---:|---|
| news.csv | Financial-news input | 12 | id, timestamp, source, source_type, headline, text, sector, expected_event, expected_sentiment |
| social_posts.csv | X-style investor discussion input | 12 | Same fields, with social source designation |
| portfolio.csv | Wholesale-banking positions | 12 | asset_id, asset_type, issuer, sector, value, currency, duration, risk_factors, sensitivities |
| scenarios.json | Stress assumptions | 5 | id, event_type, name, shocks by asset class, rate_change, assumptions |

Dates: synthetic records on 1 October 2026 between 09:00 and 09:44 IST. These are demonstration timestamps, not publication dates for actual events. The replay runs in fixed news/social pairs and does not claim to be a live market stream.

The portfolio totals INR 100,000,000 across five asset classes and six sectors. The derivative value is a synthetic carrying value, not notional. Event sensitivities in [0,1], source reliability, scenario shocks, duration, and spillover weights are synthetic business assumptions. Government bonds also receive systemic macro/geopolitical spillover. Issuer mapping takes precedence over sector mapping, avoiding double counting. Social examples intentionally paraphrase the news to demonstrate two ingestion source types; they are correlated and must not be treated as independent corroboration.

Expected event and sentiment labels are author labels used only by the evaluation script. The inference engine never reads these labels or the CSV sector annotation when analyzing text. Evaluation on these 24 examples is a small diagnostic, not a benchmark. No classifier training uses the test records.

Regenerate: `python scripts/seed_data.py`. Startup imports the CSV/JSON into SQLite idempotently. Reset clears signals and stress results and replays six ordinary records. Restart resumes processed demo records; the frontend must be open with replay enabled to advance automatically.

Optional live news comes from NewsAPI using a user-provided API key. NewsAPI failure returns local demo data; social ingestion remains synthetic in live mode. Live records are runtime SQLite content, not part of the submitted synthetic dataset.
