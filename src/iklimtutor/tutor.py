"""Tutor: explain a calculator record in Indonesian or English.

Three providers, in the order a low-connectivity classroom would reach them:
  template  - no model at all; deterministic bilingual explanation (always works)
  ollama    - a small local model on the teacher's laptop (offline)
  anthropic - Claude via API (needs internet and ANTHROPIC_API_KEY)

Whatever a model writes passes through grounding.check. An answer containing a
number that no calculator or fact card produced is not shown as-is; the student
sees the template explanation and a notice instead.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

import httpx
import yaml

from .calculators import CONSTANTS, HERE
from .grounding import check

FACTS = yaml.safe_load((HERE / "facts.yaml").read_text())

SYSTEM = {
    "id": (
        "Anda tutor literasi iklim untuk mahasiswa vokasi energi di Indonesia. "
        "Jawab dalam Bahasa Indonesia, paling banyak 150 kata. Gunakan HANYA angka yang ada "
        "di HASIL_KALKULATOR atau FAKTA. Jangan menghitung angka baru. Jika data tidak cukup, "
        "katakan terus terang. Sebutkan asumsi utama. Akhiri dengan satu pertanyaan refleksi."
    ),
    "en": (
        "You are a climate-literacy tutor for vocational energy students in Indonesia. "
        "Answer in English, at most 150 words. Use ONLY numbers present in CALCULATOR_RESULT "
        "or FACTS. Do not compute new numbers. If the data are insufficient, say so. "
        "State the main assumption. End with one reflection question."
    ),
}


def fmt(x: float, lang: str) -> str:
    s = f"{x:,.2f}".rstrip("0").rstrip(".") if not float(x).is_integer() else f"{int(x):,}"
    return s.translate(str.maketrans(",.", ".,")) if lang == "id" else s


def template_explain(record: dict, lang: str = "id") -> str:
    r, i = record["results"], record["inputs"]
    f = lambda x: fmt(x, lang)  # noqa: E731
    c = record["calculator"]
    if c == "electricity_emissions":
        return (
            f"Pemakaian {f(i['monthly_kwh'])} kWh per bulan berarti {f(r['annual_kwh'])} kWh per tahun. "
            f"Dengan faktor emisi jaringan {f(i['emission_factor_kg_per_kwh'])} kg CO2/kWh, emisinya "
            f"sekitar {f(r['annual_co2_kg'])} kg CO2 ({f(r['annual_co2_t'])} ton) per tahun. "
            "Asumsi utama: faktor emisi jaringan Jawa-Madura-Bali; nilainya berubah tiap tahun. "
            "Pertanyaan refleksi: peralatan mana di rumah Anda yang paling banyak memakai listrik?"
            if lang == "id" else
            f"Using {f(i['monthly_kwh'])} kWh per month means {f(r['annual_kwh'])} kWh per year. "
            f"With a grid emission factor of {f(i['emission_factor_kg_per_kwh'])} kg CO2/kWh, that is "
            f"about {f(r['annual_co2_kg'])} kg CO2 ({f(r['annual_co2_t'])} t) per year. "
            "Main assumption: the Java-Madura-Bali grid factor, which changes every year. "
            "Reflection: which appliance in your home uses the most electricity?"
        )
    if c == "rooftop_pv":
        return (
            f"Di {i['city']}, radiasi rata-rata {f(i['ghi_kwh_m2_day'])} kWh/m² per hari. Dengan rasio kinerja "
            f"{f(i['performance_ratio'])}, setiap kWp menghasilkan sekitar {f(r['specific_yield_kwh_per_kwp'])} kWh "
            f"per tahun, jadi sistem {f(i['kwp'])} kWp menghasilkan {f(r['annual_kwh'])} kWh dan menghindari "
            f"sekitar {f(r['annual_co2_avoided_kg'])} kg CO2 per tahun. Asumsi utama: panel datar tanpa "
            "peneduhan. Pertanyaan refleksi: apa yang terjadi pada hasil ini jika atap sering teduh?"
            if lang == "id" else
            f"In {i['city']}, mean irradiance is {f(i['ghi_kwh_m2_day'])} kWh/m² per day. With a performance ratio "
            f"of {f(i['performance_ratio'])}, each kWp yields about {f(r['specific_yield_kwh_per_kwp'])} kWh per "
            f"year, so a {f(i['kwp'])} kWp system gives {f(r['annual_kwh'])} kWh and avoids about "
            f"{f(r['annual_co2_avoided_kg'])} kg CO2 per year. Main assumption: flat panels with no shading. "
            "Reflection: how would frequent shading change this result?"
        )
    if c == "local_warming_trend":
        return (
            f"Data reanalisis untuk {i['city']} ({i['start']}-{i['end']}) menunjukkan tren "
            f"{f(r['trend_c_per_decade'])} °C per dekade. Rata-rata sepuluh tahun terakhir "
            f"{f(r['last_decade_mean_c'])} °C, sepuluh tahun pertama {f(r['first_decade_mean_c'])} °C "
            f"(selisih {f(r['decade_difference_c'])} °C). Asumsi utama: satu sel grid ~50 km, bukan stasiun. "
            "Pertanyaan refleksi: tahun mana yang menyimpang dari tren, dan apakah itu tahun El Niño?"
            if lang == "id" else
            f"Reanalysis data for {i['city']} ({i['start']}-{i['end']}) show a trend of "
            f"{f(r['trend_c_per_decade'])} °C per decade. The last ten years averaged "
            f"{f(r['last_decade_mean_c'])} °C against {f(r['first_decade_mean_c'])} °C for the first ten "
            f"(difference {f(r['decade_difference_c'])} °C). Main assumption: one ~50 km grid cell, not a station. "
            "Reflection: which years depart from the trend, and were they El Niño years?"
        )
    raise ValueError(c)


def relevant_facts(record: dict) -> list[dict]:
    return [fc for fc in FACTS if record["calculator"] in fc.get("topics", [])]


@dataclass
class Answer:
    text: str
    provider: str
    grounded: bool
    ungrounded: list[str] = field(default_factory=list)
    fell_back: bool = False
    latency_s: float = 0.0
    raw: str = ""


def _user_prompt(record: dict, question: str, lang: str) -> str:
    facts = [{"id": fc["id"], "text": fc[f"text_{lang}"], "source": fc["source"]} for fc in relevant_facts(record)]
    assumptions = {k: CONSTANTS[k] for k in record.get("assumptions", []) if k in CONSTANTS}
    tag = ("HASIL_KALKULATOR", "FAKTA", "ASUMSI", "PERTANYAAN") if lang == "id" else \
          ("CALCULATOR_RESULT", "FACTS", "ASSUMPTIONS", "QUESTION")
    return (f"{tag[0]}:\n{json.dumps(record, ensure_ascii=False)}\n\n{tag[1]}:\n"
            f"{json.dumps(facts, ensure_ascii=False)}\n\n{tag[2]}:\n{json.dumps(assumptions, ensure_ascii=False)}\n\n"
            f"{tag[3]}: {question}")


def _ollama(system: str, user: str, model: str) -> str:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    r = httpx.post(f"{host}/api/chat", timeout=300, json={
        "model": model, "stream": False, "options": {"temperature": 0.2},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    })
    r.raise_for_status()
    return r.json()["message"]["content"]


def _anthropic(system: str, user: str, model: str) -> str:
    key = os.environ["ANTHROPIC_API_KEY"]
    r = httpx.post("https://api.anthropic.com/v1/messages", timeout=120, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json",
    }, json={"model": model, "max_tokens": 600, "system": system,
             "messages": [{"role": "user", "content": user}]})
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"])


def ask(record: dict, question: str, lang: str = "id", provider: str = "template", model: str | None = None) -> Answer:
    t0 = time.time()
    fallback = template_explain(record, lang)
    if provider == "template":
        return Answer(fallback, "template", True, latency_s=time.time() - t0)
    system, user = SYSTEM[lang], _user_prompt(record, question, lang)
    try:
        if provider == "ollama":
            raw = _ollama(system, user, model or "qwen2.5:3b")
        elif provider == "anthropic":
            raw = _anthropic(system, user, model or "claude-sonnet-5")
        else:
            raise ValueError(provider)
    except (httpx.HTTPError, KeyError) as e:
        note = "Model tidak tersedia; memakai penjelasan bawaan." if lang == "id" else \
               "Model unavailable; showing the built-in explanation."
        return Answer(f"{fallback}\n\n_{note} ({type(e).__name__})_", provider, True, fell_back=True,
                      latency_s=time.time() - t0)
    g = check(raw, record, relevant_facts(record))
    if g["grounded"]:
        return Answer(raw, provider, True, latency_s=time.time() - t0, raw=raw)
    note = ("Jawaban model memuat angka yang tidak berasal dari kalkulator "
            f"({', '.join(g['ungrounded'])}); memakai penjelasan bawaan.") if lang == "id" else \
           (f"The model's answer contained numbers not produced by the calculator "
            f"({', '.join(g['ungrounded'])}); showing the built-in explanation.")
    return Answer(f"{fallback}\n\n_{note}_", provider, False, g["ungrounded"], True, time.time() - t0, raw)
