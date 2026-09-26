# Study design (planned, not yet run)

## Questions

- **RQ1 (system).** How often does each tutor tier (local 3B model, cloud model) produce
  answers with invented numbers, and how often does the grounding check intercept them?
  *Measured by `eval/run_eval.py`; no learners needed.*
- **RQ2 (learning).** Do students who use the tutor for the three activities improve
  more on a climate-literacy and quantitative-reasoning test than students who complete
  the same worksheets without the tutor?
- **RQ3 (critical AI use).** After the activities, can students identify an AI answer that
  contains an invented number or an unstated assumption?

## Design

Quasi-experimental pre/post with two intact classes (tutor vs. worksheet-only) at one
vocational energy institution. There are three 50-minute sessions, one per activity.

| Instrument | Content | Status |
|---|---|---|
| Climate-literacy items | Adapt items from a published, validated climate-literacy instrument | **Instrument not yet selected. Verify its citation and licence before use.** |
| Quantitative items | 6 items: kWh→CO₂, kWh/kWp, reading a trend line | To write; pilot with 5 students |
| AI-critique items (RQ3) | 4 tutor answers, 2 with a planted invented number | To write from real eval outputs |
| Logs | Questions asked, tier, grounded/fallback flags | Needs a consent-gated logging switch in the app |

**Analysis.** ANCOVA on post-test with pre-test as covariate. Report effect sizes with
confidence intervals. With two intact classes, report clustering as a limitation and
make no causal claim.

## Ethics and data

- Institutional ethics approval and informed consent come before any data collection.
- Logs must hold no names. Store questions and answers only with consent.
- Students under 18 need guardian consent.

## Feasibility

| Item | Need | Have |
|---|---|---|
| Hardware | One laptop with 8 GB+ RAM for a 3B model, or template tier only | Yes (author's laptop) |
| Connectivity | None for template/ollama tiers | n/a |
| Cost | No API cost unless the anthropic tier is compared | — |
| Time | 3 sessions + 2 test sessions per class | Needs an institutional partner |
