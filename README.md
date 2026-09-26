# Offline Climate Tutor (Iklim Tutor)

A bilingual (Indonesian/English) climate-literacy tutor for vocational energy
students. It is built on one rule: **calculators compute; the language model only
explains.** A grounding check compares every number in a model answer against the
calculator record and the fact cards. An answer that contains a number from
neither source is withheld, and the student sees a deterministic explanation.

The app works with no model and no internet. Its tiers are:

| Tier | Needs | Use |
|---|---|---|
| `template` | nothing | Deterministic bilingual explanation that always runs |
| `ollama` | a small local model on the teacher's laptop | Offline conversational tutor |
| `anthropic` | internet + `ANTHROPIC_API_KEY` | Stronger model for comparison |

Climate data for 12 Indonesian cities, from NASA POWER monthly data for 1981–2024, is
bundled in `src/iklimtutor/presets.json`, so a classroom without connectivity still
gets real local numbers.

Target chapter: *AI for Climate Learning and Sustainable Development* (ISTIC–UNESCO /
UM, Springer 2027), Part III "AI-Enhanced Climate Education: Pedagogical
Innovations". See [docs/chapter-proposal.md](docs/chapter-proposal.md).

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q                                   # 11 tests
.venv/bin/streamlit run src/iklimtutor/app.py          # classroom app
.venv/bin/python eval/run_eval.py --provider template  # baseline evaluation
ollama pull qwen2.5:3b && .venv/bin/python eval/run_eval.py --provider ollama --model qwen2.5:3b
.venv/bin/python scripts/build_presets.py              # refresh bundled data (needs internet)
```

## Activities (one 50-minute session each)

1. **My city's temperature trend.** Annual mean temperature for 1981–2024, the OLS trend per decade, and the first-decade vs last-decade mean.
2. **Household electricity footprint.** Monthly kWh × grid emission factor → annual CO₂.
3. **Rooftop solar in my city.** Irradiance × 365 × performance ratio → kWh/kWp, total kWh and avoided CO₂.

## Evaluation harness

`eval/run_eval.py` asks 54 questions: 9 calculator cases × 2 languages × 3 question types.
The types are *explain*, *trap* (asks for a number the calculator did not produce,
such as the temperature in 2050 or rupiah saved) and *misconception* ("isn't it just
a natural cycle?"). The harness scores the model's **raw** answer before fallback on:
grounded rate, trap-resisted rate, headline-number rate and language match.

The template baseline scores 1.0 on every metric. That score is **trivial**: the template
ignores the question and restates the calculation. It is the floor that a model tier
must beat in usefulness without falling below it in accuracy. No model tier has been
evaluated yet: no Ollama model was installed and no API key was set when this was built.

## Honest limits

- `grid_emission_factor_kg_per_kwh = 0.85` and `pv_performance_ratio = 0.80` are
  **unverified defaults**, flagged in the app sidebar. Replace the emission factor with
  the current Ditjen Gatrik publication before classroom use.
- All four fact cards are marked `verified: false` until their wording is checked
  against the cited sources.
- NASA POWER is a ~50 km reanalysis grid, not station data. Coastal cells (Kupang,
  Makassar) show sea-damped temperature ranges.
- The PV estimate uses horizontal irradiance as plane-of-array and has no temperature
  or shading model. It is a teaching estimate, not a design yield.
- The grounding check catches **invented numbers**. It does not catch wrong
  reasoning that uses correct numbers, or false statements with no numbers. The
  study design treats these as a separate, human-rated category.
- No students have used this yet. Learning effects are a planned study
  ([docs/study-design.md](docs/study-design.md)), not a result.

## Layout

```
src/iklimtutor/  calculators.py  grounding.py  tutor.py  activities.py  app.py
                 constants.yaml (sourced assumptions)  facts.yaml  presets.json
eval/run_eval.py   tests/test_core.py   scripts/build_presets.py   docs/
```
