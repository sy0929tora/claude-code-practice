"""§6 の数式が §8 のサンプル期待値と一致することを確認する回帰テスト。

期待値は依頼書 §8 の表（±1点で一致すればOK）。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from intake_manual import load_candidates_csv  # noqa: E402
from score import ScoringContext, score_and_rank  # noqa: E402

EXPECTED_TOTAL = {
    "横浜市港北区師岡町(新築)": 82,
    "川崎市中原区小杉陣屋町2": 67,
    "川崎市中原区井田2(日吉物件)": 60,
    "大田区中央5": 55,
    "横浜市港北区篠原北1": 48,
}

EXPECTED_RANK = {
    "横浜市港北区師岡町(新築)": 1,
    "川崎市中原区小杉陣屋町2": 2,
    "川崎市中原区井田2(日吉物件)": 3,
    "大田区中央5": 4,
    "横浜市港北区篠原北1": 5,
}


def _score_samples():
    candidates = load_candidates_csv(ROOT / "data" / "candidates.csv")
    ctx = ScoringContext()
    return score_and_rank(candidates, ctx)


def test_sample_totals_within_tolerance():
    scored = _score_samples()
    assert len(scored) == 5
    for s in scored:
        expected = EXPECTED_TOTAL[s.name]
        assert abs(s.total_score - expected) <= 1, (
            f"{s.name}: got {s.total_score}, expected {expected}±1"
        )


def test_sample_ranking():
    scored = _score_samples()
    for s in scored:
        assert s.rank == EXPECTED_RANK[s.name], (
            f"{s.name}: got rank {s.rank}, expected {EXPECTED_RANK[s.name]}"
        )


def test_clamp_bounds():
    from score import clamp

    assert clamp(150) == 100
    assert clamp(-10) == 0
    assert clamp(42) == 42


def test_dedupe_by_address_and_price():
    from intake_manual import dedupe
    from models import Candidate

    a = Candidate(name="物件A", station="日吉", price_man=5000, address="東京都渋谷区1-1-1")
    b = Candidate(name="物件A(重複)", station="日吉", price_man=5000, address="東京都渋谷区1-1-1")
    c = Candidate(name="物件B", station="日吉", price_man=6000, address="東京都渋谷区2-2-2")

    result = dedupe([a, b, c])
    assert len(result) == 2
    assert result[0].name == "物件A"
    assert result[1].name == "物件B"
