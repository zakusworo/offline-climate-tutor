"""Deterministic calculators. The tutor never computes numbers itself.

Each calculator returns a flat dict of named results plus the inputs and
assumptions it used, so the grounding check can compare any number the
language model writes against this record.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
CONSTANTS = yaml.safe_load((HERE / "constants.yaml").read_text())
PRESETS = json.loads((HERE / "presets.json").read_text()) if (HERE / "presets.json").exists() else {}


def const(name: str) -> float:
    return CONSTANTS[name]["value"]


def electricity_emissions(monthly_kwh: float, emission_factor: float | None = None) -> dict:
    """Household electricity use -> annual CO2."""
    ef = emission_factor if emission_factor is not None else const("grid_emission_factor_kg_per_kwh")
    annual_kwh = monthly_kwh * 12
    annual_kg = annual_kwh * ef
    return {
        "calculator": "electricity_emissions",
        "inputs": {"monthly_kwh": monthly_kwh, "emission_factor_kg_per_kwh": ef},
        "results": {"annual_kwh": round(annual_kwh, 1), "annual_co2_kg": round(annual_kg, 1),
                    "annual_co2_t": round(annual_kg / 1000, 2)},
        "assumptions": ["grid_emission_factor_kg_per_kwh"],
    }


def rooftop_pv(city: str, kwp: float, performance_ratio: float | None = None,
               emission_factor: float | None = None) -> dict:
    """Rooftop PV yield from the city's long-term mean irradiance (NASA POWER)."""
    p = PRESETS[city]
    pr = performance_ratio if performance_ratio is not None else const("pv_performance_ratio")
    ef = emission_factor if emission_factor is not None else const("grid_emission_factor_kg_per_kwh")
    ghi = p["ghi_kwh_m2_day"]
    specific_yield = ghi * 365 * pr  # kWh per kWp per year, flat-plate approximation
    annual_kwh = specific_yield * kwp
    return {
        "calculator": "rooftop_pv",
        "inputs": {"city": city, "kwp": kwp, "performance_ratio": pr,
                   "ghi_kwh_m2_day": ghi, "emission_factor_kg_per_kwh": ef},
        "results": {"specific_yield_kwh_per_kwp": round(specific_yield, 0),
                    "annual_kwh": round(annual_kwh, 0),
                    "annual_co2_avoided_kg": round(annual_kwh * ef, 0)},
        "assumptions": ["pv_performance_ratio", "grid_emission_factor_kg_per_kwh",
                        "horizontal irradiance used as plane-of-array (no tilt gain)"],
        "data_source": p["source"],
    }


def local_warming_trend(city: str, start: int = 1981, end: int = 2024) -> dict:
    """OLS trend of annual mean 2 m temperature for the city's grid cell."""
    series = {int(y): t for y, t in PRESETS[city]["annual_t2m"].items() if start <= int(y) <= end}
    years = np.array(sorted(series))
    temps = np.array([series[y] for y in years])
    slope, intercept = np.polyfit(years, temps, 1)
    first10, last10 = temps[:10].mean(), temps[-10:].mean()
    return {
        "calculator": "local_warming_trend",
        "inputs": {"city": city, "start": int(years[0]), "end": int(years[-1])},
        "results": {"trend_c_per_decade": round(slope * 10, 2),
                    "first_decade_mean_c": round(first10, 2), "last_decade_mean_c": round(last10, 2),
                    "decade_difference_c": round(last10 - first10, 2)},
        "assumptions": ["reanalysis grid cell (~50 km), not a weather station",
                        "linear trend; year-to-year variability (ENSO) not removed"],
        "data_source": PRESETS[city]["source"],
    }


def run(name: str, **kwargs) -> dict:
    return {"electricity_emissions": electricity_emissions, "rooftop_pv": rooftop_pv,
            "local_warming_trend": local_warming_trend}[name](**kwargs)
