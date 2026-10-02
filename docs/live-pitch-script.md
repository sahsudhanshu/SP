# Five-minute live pitch

Preflight: start the cached FinBERT backend and production frontend. Run `scripts/run_demo.py` once, check local health, then use Reset in the UI. Keep `/risk-map`, `/stress-testing` and `/audit` ready. Everything shown uses synthetic data and assumptions.

**0:00–0:30 — Problem.** “We don't stop at detecting risk. We trace how that risk propagates into a portfolio. A headline is useful only when an analyst can connect it to the positions they own.” State that this is a decision-support prototype for a synthetic INR 100M wholesale-banking portfolio.

**0:30–1:10 — Event detection.** On Overview, click Next event. The geopolitical energy/shipping shock becomes Critical. Click Next event again for the related social observation. Open Signal intelligence: 2 sources, 2 observations, 1 distinct text. “This social post repeats the news. We collapse it and do not invent independent corroboration.” Show raw impact 9.78, confidence 85.5%, effective risk 8.36.

**1:10–2:10 — Propagation and exposure.** Open Risk transmission. Follow event → Helios Energy → Energy → LOAN_01 → portfolio. Click LOAN_01: INR 12M value, .85 sensitivity, 12% portfolio weight and INR .499M moderate conditional loss. Explain direct INR 42M versus weighted INR 59.5M, including sector mapping and systemic spillover. The transmission ledger counts each of 12 positions once.

**2:10–3:05 — Stress and attribution.** Open Stress & what-if. Compare Base INR 100M, Moderate INR 97.183M, Severe INR 95.070M. Moderate retains the original INR 2.817M loss. Scroll to sector attribution: Energy contributes INR 1.679M, and EQ_01 contributes INR .582M. Open its link to demonstrate traceability, then return.

**3:05–3:45 — What-if.** Set shock intensity to 1.50×. Show INR 4.226M conditional loss. Restore Moderate and change event impact or equity shock. “We change assumptions, not the underlying portfolio. Confidence controls priority; it is not a probability used to claim expected loss.”

**3:45–4:20 — Evidence.** Open Model audit and expand an observation plus the scenario result. Show the deterministic explanation. Briefly show Event timeline and real arrival history; polling creates no invented chart points.

**4:20–5:00 — Results and limits.** “All 59 tests pass, including the original 25. Our small synthetic set retains 100% event-label agreement and 91.67% sentiment agreement. Controlled local CPU sentiment inference measured 24.833 ms sequential versus 20.713 ms batched per record.” Close with the need for independently labelled real data, source validation and instrument-specific calibrated repricing. No real-market predictive accuracy or regulatory claim.
