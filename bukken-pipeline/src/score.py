"""スコアリング本体（§6 のルーブリックを寸分違わず実装する）。

この数式は利用者が別途持っている Excel トラッカーと一致している前提。
将来ここを変更する場合は tests/test_score.py の期待値も合わせて更新し、
Excel 側とズレていないか必ず突き合わせること。
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import yaml

from models import Candidate, ScoredCandidate

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return min(hi, max(lo, x))


def load_criteria(path: Optional[Path] = None) -> dict:
    path = path or CONFIG_DIR / "criteria.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_reference_land(path: Optional[Path] = None) -> dict:
    """駅 -> {price: 万/坪, source: str} の辞書を返す。"""
    path = path or CONFIG_DIR / "reference_land.csv"
    ref = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ref[row["station"]] = {
                "price": float(row["land_price_man_per_tsubo"]),
                "source": row["source"],
            }
    return ref


def load_reference_commute(path: Optional[Path] = None) -> dict:
    """駅 -> {yokohama: 分, takadanobaba: 分} の辞書を返す。"""
    path = path or CONFIG_DIR / "reference_commute.csv"
    ref = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ref[row["station"]] = {
                "yokohama": float(row["to_yokohama_min"]),
                "takadanobaba": float(row["to_takadanobaba_min"]),
            }
    return ref


class ScoringContext:
    """criteria.yaml と reference_*.csv を1回だけ読み込み、使い回すための入れ物。

    enrich_reinfolib / enrich_commute が実測値を Candidate に埋めた場合は
    そちらを優先し、埋まっていない場合のみここの seed にフォールバックする。
    """

    def __init__(
        self,
        criteria: Optional[dict] = None,
        reference_land: Optional[dict] = None,
        reference_commute: Optional[dict] = None,
    ):
        self.criteria = criteria or load_criteria()
        self.reference_land = reference_land or load_reference_land()
        self.reference_commute = reference_commute or load_reference_commute()

    def land_price_for(self, station: str) -> tuple[Optional[float], Optional[str]]:
        row = self.reference_land.get(station)
        if row is None:
            return None, None
        return row["price"], row["source"]

    def commute_for(self, station: str) -> tuple[Optional[float], Optional[float]]:
        row = self.reference_commute.get(station)
        if row is None:
            return None, None
        return row["yokohama"], row["takadanobaba"]


def score_candidate(c: Candidate, ctx: ScoringContext) -> ScoredCandidate:
    cfg = ctx.criteria
    base_year = cfg["base_year"]
    sqm_to_tsubo = cfg["sqm_to_tsubo"]
    bldg_unit_price = cfg["bldg_unit_price"]
    bldg_lifespan = cfg["bldg_lifespan"]
    weights = cfg["weights"]
    hazard_max_penalty = cfg["hazard_max_penalty"]
    redflag_max_penalty = cfg["redflag_max_penalty"]

    data = c.model_dump()

    # --- 通勤（実測があれば優先、無ければ seed） ---
    commute_yokohama = c.commute_yokohama_min
    commute_takadanobaba = c.commute_takadanobaba_min
    if commute_yokohama is None or commute_takadanobaba is None:
        seed_yoko, seed_taka = ctx.commute_for(c.station)
        if commute_yokohama is None:
            commute_yokohama = seed_yoko
        if commute_takadanobaba is None:
            commute_takadanobaba = seed_taka
    if commute_yokohama is None or commute_takadanobaba is None:
        raise ValueError(
            f"通勤時間が不明です（駅={c.station}）。reference_commute.csv に seed を追加するか、"
            "enrich_commute.py で実測値を取得してください。"
        )

    # --- 相場土地坪単価（enrich_reinfolib が実測値+出典を埋めていれば使う想定だが、
    #     現状 Candidate は坪単価そのものを保持するフィールドを持たないため、
    #     M1〜M2時点では常に reference_land.csv (seed または reinfolib 更新後) を参照する ---
    land_price, land_price_source = ctx.land_price_for(c.station)
    if land_price is None:
        raise ValueError(
            f"相場土地坪単価が不明です（駅={c.station}）。reference_land.csv に seed を追加するか、"
            "enrich_reinfolib.py で実測値を取得してください。"
        )

    if c.land_sqm is None or c.bldg_sqm is None or c.built_year is None:
        raise ValueError(f"面積または築年が不明です（id={c.id}, name={c.name}）。")

    land_tsubo = c.land_sqm * sqm_to_tsubo
    bldg_tsubo = c.bldg_sqm * sqm_to_tsubo
    age_years = base_year - c.built_year
    residual_rate = clamp(1 - age_years / bldg_lifespan, 0, 1)

    estimated_land_value = land_tsubo * land_price
    estimated_bldg_value = bldg_tsubo * bldg_unit_price * residual_rate
    estimated_fair_price = estimated_land_value + estimated_bldg_value

    price = c.price_man
    discount_rate = (estimated_fair_price - price) / price
    land_ratio = estimated_land_value / price
    commute_total = commute_yokohama + commute_takadanobaba

    value_score = clamp(50 + discount_rate * 200)
    asset_score = clamp(land_ratio / 0.6 * 100)

    commute_score = max(
        0.0,
        clamp(100 - (commute_total - 45) * 2)
        - (30 if (commute_yokohama > 45 or commute_takadanobaba > 45) else 0),
    )

    size_score = clamp(
        (min(land_tsubo / 18, 1.5) + min(c.bldg_sqm / 85, 1.5)) / 3 * 100
    )
    age_score = clamp(100 - age_years / 15 * 100)

    if c.walk_min is None:
        station_score = 0.0
    else:
        station_score = clamp(100 - (c.walk_min - 5) / 15 * 100)

    hazard_penalty = c.hazard_0_3 / 3 * hazard_max_penalty
    redflag_penalty = c.redflag_0_3 / 3 * redflag_max_penalty

    weight_sum = sum(weights.values())
    weighted = (
        value_score * weights["value"]
        + asset_score * weights["asset"]
        + commute_score * weights["commute"]
        + size_score * weights["size"]
        + age_score * weights["age"]
        + station_score * weights["station"]
    ) / weight_sum

    total_score = clamp(weighted - hazard_penalty - redflag_penalty)

    data.update(
        commute_yokohama_min=commute_yokohama,
        commute_takadanobaba_min=commute_takadanobaba,
        land_price_source=land_price_source,
        value_score=round(value_score, 2),
        asset_score=round(asset_score, 2),
        commute_score=round(commute_score, 2),
        size_score=round(size_score, 2),
        age_score=round(age_score, 2),
        station_score=round(station_score, 2),
        hazard_penalty=round(hazard_penalty, 2),
        redflag_penalty=round(redflag_penalty, 2),
        total_score=round(total_score, 2),
        estimated_land_value=round(estimated_land_value, 1),
        estimated_bldg_value=round(estimated_bldg_value, 1),
        estimated_fair_price=round(estimated_fair_price, 1),
        land_price_used=land_price,
    )
    return ScoredCandidate(**data)


def score_and_rank(
    candidates: list[Candidate], ctx: Optional[ScoringContext] = None
) -> list[ScoredCandidate]:
    ctx = ctx or ScoringContext()
    scored = [score_candidate(c, ctx) for c in candidates]
    scored.sort(key=lambda s: s.total_score, reverse=True)
    for i, s in enumerate(scored, start=1):
        s.rank = i
    return scored
