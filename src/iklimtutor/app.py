"""Streamlit classroom app. Run: streamlit run src/iklimtutor/app.py"""

import streamlit as st

from iklimtutor import calculators as calc
from iklimtutor.activities import ACTIVITIES
from iklimtutor.tutor import ask

st.set_page_config(page_title="Iklim Tutor", layout="centered")

with st.sidebar:
    lang = st.radio("Bahasa / Language", ["id", "en"], format_func={"id": "Indonesia", "en": "English"}.get)
    provider = st.selectbox("Tutor", ["template", "ollama", "anthropic"],
                            help="template = tanpa model (selalu jalan, offline)")
    model = st.text_input("Model", "qwen2.5:3b" if provider == "ollama" else
                          "claude-sonnet-5" if provider == "anthropic" else "", disabled=provider == "template")
    st.divider()
    st.caption("Asumsi (guru boleh mengubah)" if lang == "id" else "Assumptions (teacher may edit)")
    ef = st.number_input("Grid EF, kg CO2/kWh", 0.3, 1.5, calc.const("grid_emission_factor_kg_per_kwh"), 0.01)
    pr = st.number_input("PV performance ratio", 0.5, 0.95, calc.const("pv_performance_ratio"), 0.01)
    for k, v in calc.CONSTANTS.items():
        if v["status"] != "verified" and v["value"] is not None:
            st.warning(f"{k}: {v['status']}")

act = st.selectbox("Aktivitas" if lang == "id" else "Activity", list(ACTIVITIES),
                   format_func=lambda k: ACTIVITIES[k][f"title_{lang}"])
a = ACTIVITIES[act]
st.markdown(f"**{'Tujuan' if lang == 'id' else 'Objective'}:** {a[f'objective_{lang}']}")

cities = sorted(calc.PRESETS)
if act == "electricity_emissions":
    kwh = st.number_input("kWh / bulan" if lang == "id" else "kWh / month", 10.0, 5000.0, 150.0, 10.0)
    rec = calc.electricity_emissions(kwh, emission_factor=ef)
elif act == "rooftop_pv":
    city = st.selectbox("Kota" if lang == "id" else "City", cities, index=cities.index("Sleman"))
    kwp = st.number_input("kWp", 0.5, 100.0, 2.0, 0.5)
    rec = calc.rooftop_pv(city, kwp, performance_ratio=pr, emission_factor=ef)
else:
    city = st.selectbox("Kota" if lang == "id" else "City", cities, index=cities.index("Sleman"))
    rec = calc.local_warming_trend(city)
    series = calc.PRESETS[city]["annual_t2m"]
    st.line_chart({"°C": {int(y): t for y, t in series.items()}})

st.subheader("Hasil kalkulator" if lang == "id" else "Calculator result")
st.json(rec["results"])

q = st.text_input("Pertanyaan Anda" if lang == "id" else "Your question",
                  "Jelaskan arti hasil ini." if lang == "id" else "Explain what this means.")
if st.button("Tanya tutor" if lang == "id" else "Ask the tutor"):
    with st.spinner("..."):
        ans = ask(rec, q, lang, provider, model or None)
    st.markdown(ans.text)
    st.caption(f"{ans.provider} · grounded={ans.grounded} · fallback={ans.fell_back} · {ans.latency_s:.1f}s")

st.divider()
st.markdown(f"**{'Refleksi' if lang == 'id' else 'Reflection'}**")
for item in a[f"reflection_{lang}"]:
    st.markdown(f"- {item}")
