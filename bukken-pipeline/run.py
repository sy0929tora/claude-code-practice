#!/usr/bin/env python3
"""物件探索・自動採点パイプライン CLI。

M1: 手動CSV入力 → 採点 → output.xlsx
M2以降: --geocode / --reinfolib / --commute / --gmail 等のフラグで
        enrich ステージを追加していく（TODO）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from intake_manual import dedupe, load_candidates_csv  # noqa: E402
from output_sheet import write_xlsx  # noqa: E402
from score import ScoringContext, score_and_rank  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="物件探索・自動採点パイプライン")
    parser.add_argument(
        "--input", default=str(ROOT / "data" / "candidates.csv"), help="入力CSVパス"
    )
    parser.add_argument(
        "--output", default=str(ROOT / "data" / "output.xlsx"), help="出力xlsxパス"
    )
    parser.add_argument(
        "--criteria", default=None, help="criteria.yaml のパス（省略時 config/criteria.yaml）"
    )
    args = parser.parse_args(argv)

    candidates = load_candidates_csv(args.input)
    candidates = dedupe(candidates)
    if not candidates:
        print("入力候補が0件です。data/candidates.csv を確認してください。", file=sys.stderr)
        return 1

    criteria = None
    if args.criteria:
        with open(args.criteria, encoding="utf-8") as f:
            criteria = yaml.safe_load(f)
    ctx = ScoringContext(criteria=criteria)

    scored = score_and_rank(candidates, ctx)

    out_path = write_xlsx(scored, Path(args.output))

    print(f"{len(scored)}件を採点しました。出力: {out_path}")
    print()
    print(f"{'順位':>4} {'総合':>6}  物件名")
    for s in scored:
        print(f"{s.rank:>4} {s.total_score:>6.1f}  {s.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
