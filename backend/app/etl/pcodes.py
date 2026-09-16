"""P-code (humanitarian place-code) normalisation.

P-codes are the stable identifiers used by HDX COD-AB / COD-PS. Pipelines
normalise them before upsert so re-runs and joins are case/whitespace-safe.
"""

from __future__ import annotations

import math

_MISSING = {"", "NAN", "NONE", "<NA>", "NAT", "NULL"}


def normalize_pcode(value: object) -> str | None:
    """Return a canonical P-code (stripped, uppercased) or None if missing.

    Accepts messy CSV/shapefile cells: blanks, the string ``nan``, pandas
    ``NaN``/``NaT``, and ``None``. Never invents a code.
    """
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None

    text = str(value).strip().upper()
    if text in _MISSING:
        return None
    return text
