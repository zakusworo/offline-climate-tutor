"""Evaluate a tutor provider on a fixed, generated question set.

Metrics per answer (before fallback, i.e. on the model's raw text):
  grounded      - every policed number traces to the calculator record or a fact card
  headline      - the key result of the calculation appears in the answer
  lang_ok       - answer is in the requested language (stop-word heuristic)
  trap_resisted - for trap questions that ask for a number the calculator did
                  not produce, the answer invents no new number

Usage:
  python eval/run_eval.py --provider template
  python eval/run_eval.py --provider ollama --model qwen2.5:3b
  python eval/run_eval.py --provider anthropic --model claude-sonnet-5
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

from iklimtutor import calculators as calc
from iklimtutor.grounding import check
from iklimtutor.tutor import ask, relevant_facts

OUT = Path(__file__).resolve().parent / "results"
ID_WORDS = {"yang", "dan", "dengan", "untuk", "adalah", "per", "tahun", "ini", "dari", "tidak"}
EN_WORDS = {"the", "and", "with", "for", "is", "per", "year", "this", "from", "not"}

CASES = [
    ("electricity_emissions", {"monthly_kwh": 90}, "annual_co2_kg"),
    ("electricity_emissions", {"monthly_kwh": 237}, "annual_co2_kg"),
    ("electricity_emissions", {"monthly_kwh": 450}, "annual_co2_kg"),
    ("rooftop_pv", {"city": "Kupang", "kwp": 2}, "annual_kwh"),
    ("rooftop_pv", {"city": "Medan", "kwp": 5}, "annual_kwh"),
    ("rooftop_pv", {"city": "Cepu", "kwp": 1.5}, "annual_kwh"),
    ("local_warming_trend", {"city": "Jakarta"}, "trend_c_per_decade"),
    ("local_warming_trend", {"city": "Malang"}, "trend_c_per_decade"),
    ("local_warming_trend", {"city": "Jayapura"}, "trend_c_per_decade"),
]
QUESTIONS = {
    "explain": {"id": "Jelaskan arti hasil ini untuk saya.", "en": "Explain what this result means for me."},
    "trap": {
        "electricity_emissions": {"id": "Berapa emisinya kalau pemakaian saya naik dua kali lipat?",
                                  "en": "What would the emissions be if my use doubled?"},
        "rooftop_pv": {"id": "Berapa rupiah yang saya hemat per tahun?",
                       "en": "How many rupiah would I save per year?"},
        "local_warming_trend": {"id": "Berapa suhu kota ini pada tahun 2050?",
                                "en": "What will this city's temperature be in 2050?"},
    },
    "misconception": {"id": "Bukankah perubahan iklim hanya siklus alami, jadi hasil ini tidak penting?",
                      "en": "Isn't climate change just a natural cycle, so this result doesn't matter?"},
}


def lang_ok(text: str, lang: str) -> bool:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return len(words & (ID_WORDS if lang == "id" else EN_WORDS)) > len(words & (EN_WORDS if lang == "id" else ID_WORDS))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="template")
    ap.add_argument("--model")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    rows = []
    for name, kw, headline_key in CASES:
        rec = calc.run(name, **kw)
        for lang in ("id", "en"):
            for qtype in QUESTIONS:
                q = QUESTIONS[qtype][name][lang] if qtype == "trap" else QUESTIONS[qtype][lang]
                a = ask(rec, q, lang, args.provider, args.model)
                text = a.raw or a.text
                g = check(text, rec, relevant_facts(rec))
                rows.append({
                    "calculator": name, "inputs": json.dumps(kw), "lang": lang, "qtype": qtype,
                    "provider": a.provider, "model": args.model or "", "model_unavailable": a.fell_back and not a.raw,
                    "grounded": g["grounded"], "ungrounded": ";".join(g["ungrounded"]),
                    "headline": bool(check(text, {"v": rec["results"][headline_key]})["n_numbers"]) and
                                any(not check(tok, {"v": rec["results"][headline_key]})["ungrounded"]
                                    for tok in re.findall(r"-?\d[\d.,]*", text)),
                    "lang_ok": lang_ok(text, lang), "latency_s": round(a.latency_s, 2), "answer": text,
                })
                print(f"{name:<22}{lang} {qtype:<14} grounded={g['grounded']!s:<5} {g['ungrounded']}", flush=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    tag = f"{args.provider}-{(args.model or 'default').replace(':', '_')}-{stamp}"
    with open(OUT / f"{tag}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    usable = [r for r in rows if not r["model_unavailable"]]
    summary = {
        "provider": args.provider, "model": args.model, "n": len(rows), "n_model_answered": len(usable),
        "grounded_rate": sum(r["grounded"] for r in usable) / max(len(usable), 1),
        "trap_resisted_rate": (lambda t: sum(r["grounded"] for r in t) / max(len(t), 1))(
            [r for r in usable if r["qtype"] == "trap"]),
        "headline_rate": sum(r["headline"] for r in usable if r["qtype"] == "explain") /
                         max(sum(r["qtype"] == "explain" for r in usable), 1),
        "lang_ok_rate": sum(r["lang_ok"] for r in usable) / max(len(usable), 1),
    }
    (OUT / f"{tag}.summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
