import pytest

from iklimtutor import calculators as calc
from iklimtutor.grounding import check, parse_number
from iklimtutor.tutor import ask, template_explain


def test_parse_indonesian_and_english():
    assert (1234.5, 1) in parse_number("1.234,5")
    assert (1234.5, 1) in parse_number("1,234.5")
    assert (0.85, 2) in parse_number("0,85")
    vals = [v for v, _ in parse_number("1.020")]
    assert 1020 in vals and 1.02 in vals


def test_electricity_emissions():
    r = calc.electricity_emissions(150, emission_factor=0.85)["results"]
    assert r["annual_kwh"] == 1800
    assert r["annual_co2_kg"] == pytest.approx(1530)


def test_pv_and_trend_use_presets():
    pv = calc.rooftop_pv("Sleman", 2.0, performance_ratio=0.8)
    assert 1200 < pv["results"]["specific_yield_kwh_per_kwp"] < 1700
    tr = calc.local_warming_trend("Sleman")
    assert -1 < tr["results"]["trend_c_per_decade"] < 1


@pytest.mark.parametrize("name,kw", [
    ("electricity_emissions", {"monthly_kwh": 237}),
    ("rooftop_pv", {"city": "Kupang", "kwp": 3}),
    ("local_warming_trend", {"city": "Medan"}),
])
@pytest.mark.parametrize("lang", ["id", "en"])
def test_template_is_fully_grounded(name, kw, lang):
    rec = calc.run(name, **kw)
    g = check(template_explain(rec, lang), rec)
    assert g["grounded"], g


def test_fabricated_number_is_caught():
    rec = calc.electricity_emissions(150, emission_factor=0.85)
    assert not check("Emisinya sekitar 2.400 kg CO2 per tahun.", rec)["grounded"]
    assert not check("Faktor emisinya 0,90 kg/kWh.", rec)["grounded"]
    assert check("Emisinya sekitar 1,5 ton CO2 per tahun.", rec)["grounded"]  # honest rounding


def test_unavailable_model_falls_back(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:9")
    a = ask(calc.electricity_emissions(100), "Jelaskan", provider="ollama")
    assert a.fell_back and "kWh" in a.text
