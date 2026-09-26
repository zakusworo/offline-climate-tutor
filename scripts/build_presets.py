"""Download NASA POWER monthly data once and bundle it, so classrooms work offline.

Writes src/iklimtutor/presets.json with annual mean T2M (1981-2024) and the
2001-2024 mean all-sky irradiance for each city.
"""

import json
from pathlib import Path

import httpx

CITIES = {
    "Balikpapan": (-1.27, 116.83),
    "Bandung": (-6.91, 107.61),
    "Cepu": (-7.15, 111.59),
    "Jakarta": (-6.21, 106.85),
    "Kupang": (-10.17, 123.61),
    "Makassar": (-5.14, 119.43),
    "Malang": (-7.96, 112.62),
    "Medan": (3.59, 98.67),
    "Palembang": (-2.99, 104.76),
    "Pontianak": (-0.03, 109.34),
    "Sleman": (-7.73, 110.36),
    "Jayapura": (-2.53, 140.72),
}
API = "https://power.larc.nasa.gov/api/temporal/monthly/point"
OUT = Path(__file__).resolve().parents[1] / "src" / "iklimtutor" / "presets.json"

presets = {}
for city, (lat, lon) in CITIES.items():
    r = httpx.get(API, params={"parameters": "T2M,ALLSKY_SFC_SW_DWN", "community": "RE",
                               "latitude": lat, "longitude": lon, "start": 1981, "end": 2024,
                               "format": "JSON"}, timeout=120)
    r.raise_for_status()
    p = r.json()["properties"]["parameter"]
    t2m = {k[:4]: v for k, v in p["T2M"].items() if k.endswith("13") and v != -999}
    ghi = [v for k, v in p["ALLSKY_SFC_SW_DWN"].items() if k.endswith("13") and v != -999 and int(k[:4]) >= 2001]
    presets[city] = {
        "lat": lat, "lon": lon, "annual_t2m": t2m,
        "ghi_kwh_m2_day": round(sum(ghi) / len(ghi), 3),
        "source": f"NASA POWER monthly (MERRA-2/CERES), {lat},{lon}, downloaded for offline use",
    }
    print(city, len(t2m), presets[city]["ghi_kwh_m2_day"])

OUT.write_text(json.dumps(presets, indent=1))
