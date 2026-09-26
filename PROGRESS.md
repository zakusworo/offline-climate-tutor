# Offline Climate Tutor — Progress Log

_Last updated: 2026-09-26_

Handoff notes for the next working session. README describes *what the tutor is*;
this file tracks *where the work stands* and *what to do next*.

Target: *AI for Climate Learning and Sustainable Development* (ISTIC–UNESCO / UM,
Springer Nature Singapore, 2027), Part III "AI-Enhanced Climate Education: Pedagogical
Innovations". The EOI deadline (21 Sep 2026) had already passed when this project was
created. The proposal in `docs/chapter-proposal.md` is for a late-consideration request,
a later call or a journal paper. **Nothing has been submitted.**

## Resume here

The repository is `git init`'d with **no commits**. The chapter's central result, how
often real models invent numbers, **does not exist yet**. Only the template baseline
has been evaluated, and its 1.0 scores are trivial because it ignores the question.

Immediate next steps:

1. Pull a local model and run the evaluation:
   `ollama pull qwen2.5:3b && .venv/bin/python eval/run_eval.py --provider ollama --model qwen2.5:3b`.
   Add at least one more local model (e.g. `llama3.2:3b`) and, if an API key is set,
   one Claude model. The machine has 14 GB RAM, so keep local models ≤ 8B Q4.
2. Read the raw answers in `eval/results/*.csv`. Hand-rate a sample for errors that the
   grounding check cannot see (wrong reasoning with correct numbers, false claims with
   no numbers).
3. Verify `grid_emission_factor_kg_per_kwh` (0.85, UNVERIFIED) against the latest Ditjen
   Gatrik publication. The PDF sits behind a JS loader, so download it in a browser.
   Update `constants.yaml` status and source.
4. Check the wording of all four `facts.yaml` cards against their sources, then set
   `verified: true`.
5. Select a validated climate-literacy instrument for the classroom study
   (`docs/study-design.md`). Verify its citation and licence, then plan the ethics application.
6. Add a consent-gated logging switch to the app before any classroom use.

## 2026-09-26 — project created

- Calculators (`calculators.py`): household electricity emissions, rooftop PV yield,
  local warming trend. Every calculator returns inputs, results and assumptions for
  the grounding check.
- Bundled offline data (`presets.json`, from `scripts/build_presets.py`): NASA POWER
  monthly, 12 cities. Annual T2M 1981–2024 and mean GHI 2001–2024 (4.64–5.90 kWh/m²/day).
- Grounding check (`grounding.py`): parses ID and EN number formats and keeps both
  readings of ambiguous tokens such as "1.020". The tolerance is 2% relative or half a
  unit of the last written digit, so "0,90" is rejected against 0.85 and "1,5 ton"
  is accepted against 1.53 t. Integers < 10 and years are exempt.
- Tutor tiers (`tutor.py`): template / ollama / anthropic. An unavailable model or an
  ungrounded answer falls back to the template, with a notice.
- Streamlit app (`app.py`) with 3 activities (`activities.py`) and teacher-editable
  assumptions, which the app flags when unverified. AppTest passes with no exceptions.
- Evaluation harness (`eval/run_eval.py`): 54 questions (9 cases × 2 languages ×
  explain/trap/misconception). Template baseline:
  `eval/results/template-default-20260926-175530.summary.json` (all 1.0, trivial).
- Tests: 11 pass.

## Known limits (do not overclaim)

- The grounding check catches invented numbers only, not wrong reasoning or numberless
  false claims.
- The PV estimate uses horizontal irradiance with no tilt, temperature or shading model.
  It is a teaching estimate.
- Reanalysis grid cells are not station data.
- No learners have used the tutor, so learning effects are planned, not measured.
