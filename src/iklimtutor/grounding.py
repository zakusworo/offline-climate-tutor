"""Numeric grounding check.

Every number in a tutor answer must match a number in the calculator record
or the fact cards (within a relative tolerance, allowing unit rescaling by
1000 and rounding). Numbers that match nothing are reported as ungrounded.
Handles Indonesian formatting (1.234,5) and English formatting (1,234.5).
"""

from __future__ import annotations

import re

NUM = re.compile(r"(?<![\w.,])-?\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|-?\d+(?:[.,]\d+)?")
# Small integers (list markers, "2 things", years) are too common to police.
IGNORE_BELOW = 10
YEAR = range(1850, 2101)


def parse_number(tok: str) -> list[tuple[float, int]]:
    """Candidate (value, decimals) readings of a token.

    '1.234' may be 1234 (ID) or 1.234 (EN), so both readings are kept.
    """
    tok = tok.strip()
    if "," in tok and "." in tok:
        dec = "," if tok.rfind(",") > tok.rfind(".") else "."
        thou = "." if dec == "," else ","
        return [(float(tok.replace(thou, "").replace(dec, ".")), len(tok) - tok.rfind(dec) - 1)]
    for sep in ",.":
        if sep in tok:
            if tok.count(sep) > 1:
                return [(float(tok.replace(sep, "")), 0)]
            head, tail = tok.split(sep)
            cands = [(float(f"{head}.{tail}"), len(tail))]
            if len(tail) == 3:
                cands.append((float(head + tail), 0))
            return cands
    return [(float(tok), 0)]


def extract_numbers(text: str) -> list[tuple[str, list[tuple[float, int]]]]:
    return [(m.group(), parse_number(m.group())) for m in NUM.finditer(text)]


def allowed_numbers(*records) -> list[float]:
    vals: list[float] = []

    def walk(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            vals.append(float(x))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            vals.extend(v for _, cs in extract_numbers(x) for v, _ in cs)

    for r in records:
        walk(r)
    return vals


def _matches(v: float, decimals: int, allowed: list[float], rel: float) -> bool:
    """Match within `rel`, or within half a unit of the last digit written (honest rounding)."""
    tol_round = 0.5 * 10 ** -decimals
    for a in allowed:
        for scale in (1, 1000, 0.001, 100, 0.01):
            t = a * scale
            if t == 0:
                if v == 0:
                    return True
                continue
            if abs(v - t) <= max(rel * abs(t), tol_round + 1e-9):
                return True
    return False


def check(answer: str, *records, rel: float = 0.02) -> dict:
    allowed = allowed_numbers(*records)
    found = extract_numbers(answer)

    def exempt(v: float) -> bool:
        return float(v).is_integer() and (abs(v) < IGNORE_BELOW or int(v) in YEAR)

    policed = [(s, cs) for s, cs in found if not all(exempt(v) for v, _ in cs)]
    bad = [s for s, cs in policed if not any(_matches(v, d, allowed, rel) for v, d in cs)]
    return {"n_numbers": len(policed), "ungrounded": bad, "grounded": not bad}
