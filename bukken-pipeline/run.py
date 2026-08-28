#!/usr/bin/env python3
"""物件探索・自動採点パイプライン CLI。

段階（すべて任意フラグ。指定しなければ M1 と同じ「CSV→採点→xlsx」のみ動く）:
  --gmail      Gmail保存検索メールから候補を取り込み、CSV候補とマージ（M4）
  --geocode    国土地理院で住所→緯度経度を補完（M2）
  --reinfolib  不動産情報ライブラリで相場更新・ハザード/用途地域を自動判定（M2、--geocode必須）
  --commute    Google Maps Routes APIで横浜・高田馬場の通勤時間を実測（M3、--geocode必須）
  --sheets     採点結果をGoogle Sheetsにも出力（M5）
  --notify     前回出力と比較し、新規の高得点候補をメール通知（M5）
  --all        上記の enrich/notify 系フラグをすべて有効化（xlsx出力は常に行う）

どのAPIも未設定・失敗時はログに警告を出してseed値/スキップにフォールバックし、
パイプライン全体は止めない（§7「各APIは失敗時にseed値へフォールバック」）。
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from intake_manual import dedupe, load_candidates_csv  # noqa: E402
from output_sheet import write_google_sheet, write_xlsx  # noqa: E402
from score import ScoringContext, score_and_rank  # noqa: E402

logger = logging.getLogger("bukken_pipeline")


def build_parser() -> argparse.ArgumentParser:
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
    parser.add_argument("--gmail", action="store_true", help="Gmailの保存検索メールも取り込む")
    parser.add_argument("--geocode", action="store_true", help="国土地理院で住所→緯度経度")
    parser.add_argument(
        "--reinfolib", action="store_true", help="不動産情報ライブラリで相場・ハザード更新"
    )
    parser.add_argument("--commute", action="store_true", help="Google Maps Routes APIで通勤実測")
    parser.add_argument("--sheets", action="store_true", help="Google Sheetsにも出力")
    parser.add_argument("--notify", action="store_true", help="新規高得点候補をメール通知")
    parser.add_argument(
        "--all", action="store_true", help="gmail/geocode/reinfolib/commute/sheets/notifyを全て有効化"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="デバッグログを表示"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")

    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.all:
        args.gmail = args.geocode = args.reinfolib = args.commute = True
        args.sheets = args.notify = True
    if (args.reinfolib or args.commute) and not args.geocode:
        logger.info("--reinfolib/--commuteは座標が必要なため--geocodeも自動的に有効化します。")
        args.geocode = True

    candidates = load_candidates_csv(args.input)

    if args.gmail:
        try:
            from intake_gmail import fetch_candidates_from_gmail

            gmail_candidates = fetch_candidates_from_gmail()
            logger.info("Gmailから%d件の候補を取得しました。", len(gmail_candidates))
            candidates.extend(gmail_candidates)
        except Exception as e:
            logger.warning("Gmail取り込みに失敗しました（スキップして続行）: %s", e)

    candidates = dedupe(candidates)
    if not candidates:
        print("入力候補が0件です。data/candidates.csv を確認してください。", file=sys.stderr)
        return 1

    if args.geocode:
        try:
            from enrich_geocode import geocode_candidates

            geocode_candidates(candidates)
        except Exception as e:
            logger.warning("ジオコーディングに失敗しました（スキップして続行）: %s", e)

    if args.reinfolib:
        try:
            from enrich_reinfolib import enrich_hazard_and_zoning, refresh_reference_land_csv

            stations = sorted({c.station for c in candidates if c.station})
            refresh_reference_land_csv(stations, ROOT / "config" / "reference_land.csv")
            enrich_hazard_and_zoning(candidates)
        except Exception as e:
            logger.warning("不動産情報ライブラリ連携に失敗しました（seedのまま続行）: %s", e)

    if args.commute:
        try:
            from enrich_commute import enrich_commute

            enrich_commute(candidates)
        except Exception as e:
            logger.warning("通勤時間の実測に失敗しました（seedのまま続行）: %s", e)

    criteria = None
    if args.criteria:
        with open(args.criteria, encoding="utf-8") as f:
            criteria = yaml.safe_load(f)
    ctx = ScoringContext(criteria=criteria)

    scored = score_and_rank(candidates, ctx)

    out_path = Path(args.output)
    previous_scores = {}
    if args.notify:
        # 上書きされる前の前回結果を「前回」として読んでおく。
        from notify import load_previous_scores

        previous_scores = load_previous_scores(out_path)

    write_xlsx(scored, out_path)

    print(f"{len(scored)}件を採点しました。出力: {out_path}")
    print()
    print(f"{'順位':>4} {'総合':>6}  物件名")
    for s in scored:
        print(f"{s.rank:>4} {s.total_score:>6.1f}  {s.name}")

    if args.sheets:
        try:
            url = write_google_sheet(scored)
            print(f"\nGoogle Sheetsにも出力しました: {url}")
        except Exception as e:
            logger.warning("Google Sheets出力に失敗しました: %s", e)

    if args.notify:
        try:
            from notify import find_new_high_scorers, notify_email

            new_high = find_new_high_scorers(scored, previous_scores)
            if new_high:
                notify_email(new_high)
                print(f"\n新規高得点候補 {len(new_high)}件を通知しました。")
        except Exception as e:
            logger.warning("通知処理に失敗しました: %s", e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
