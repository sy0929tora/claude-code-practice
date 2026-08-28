"""手動入力（CSV）から Candidate のリストを読み込む。

将来の対話プロンプト入力（TODO: `intake_manual_interactive()`）もここに追加する想定。
"""
from __future__ import annotations

import csv
from pathlib import Path

from models import Candidate

INT_FIELDS = {"built_year", "corner", "hazard_0_3", "redflag_0_3"}
FLOAT_FIELDS = {"walk_min", "price_man", "land_sqm", "bldg_sqm"}


def _parse_row(row: dict) -> Candidate:
    cleaned = {}
    for k, v in row.items():
        if k is None:
            continue
        v = (v or "").strip()
        if v == "":
            cleaned[k] = None
        elif k in INT_FIELDS:
            cleaned[k] = int(float(v))
        elif k in FLOAT_FIELDS:
            cleaned[k] = float(v)
        else:
            cleaned[k] = v
    cleaned.setdefault("intake_source", "manual")
    if not cleaned.get("id"):
        cleaned["id"] = None
    return Candidate(**cleaned)


def load_candidates_csv(path: str | Path) -> list[Candidate]:
    path = Path(path)
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [_parse_row(row) for row in reader]


def dedupe(candidates: list[Candidate]) -> list[Candidate]:
    """住所(無ければname)+価格で重複を除去。先勝ちで後続の重複を捨てる。"""
    seen = set()
    result = []
    for c in candidates:
        key = c.dedupe_key()
        if key in seen:
            continue
        seen.add(key)
        result.append(c)
    return result
