"""notify.py の差分検出ロジックのテスト（メール送信自体はモックしない=呼ばない）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import notify  # noqa: E402
from models import ScoredCandidate  # noqa: E402


def _sc(name, price, total_score, rank=1):
    return ScoredCandidate(
        name=name, station="大倉山", price_man=price, total_score=total_score, rank=rank
    )


def test_find_new_high_scorers_excludes_previously_seen():
    scored = [_sc("A", 6000, 80), _sc("B", 5000, 60)]
    previous = {"A::6000": 80}
    new = notify.find_new_high_scorers(scored, previous, threshold=70)
    assert [s.name for s in new] == []


def test_find_new_high_scorers_includes_new_high_score():
    scored = [_sc("A", 6000, 80), _sc("B", 5000, 60)]
    previous = {}
    new = notify.find_new_high_scorers(scored, previous, threshold=70)
    assert [s.name for s in new] == ["A"]


def test_find_new_high_scorers_excludes_below_threshold():
    scored = [_sc("C", 7000, 50)]
    new = notify.find_new_high_scorers(scored, {}, threshold=70)
    assert new == []


def test_load_previous_scores_missing_file_returns_empty(tmp_path):
    assert notify.load_previous_scores(tmp_path / "does_not_exist.xlsx") == {}
