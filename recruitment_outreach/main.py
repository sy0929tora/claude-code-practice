#!/usr/bin/env python3
"""
採用アウトリーチ ツール (Recruitment Outreach Tool)
パーソルキャリア doda 向け 法人営業メール自動生成

使い方:
  python main.py "企業名"
  python main.py "企業名" --industry "IT・Web" --variations 3
  python main.py "企業名" --output result.json
"""
import argparse
import json
import sys
from pathlib import Path

from researcher import research_company
from generator import generate_outreach, OutreachResult


# ── Display helpers ───────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════╗
║     doda 採用アウトリーチ ジェネレーター                 ║
║     Recruitment Outreach Generator  (Persol Career)      ║
╚══════════════════════════════════════════════════════════╝
"""

SEP = "─" * 60


def _priority_bar(score: int) -> str:
    filled = score // 10
    bar = "█" * filled + "░" * (10 - filled)
    if score >= 70:
        label = "HIGH"
    elif score >= 40:
        label = "MED"
    else:
        label = "LOW"
    return f"[{bar}] {score}/100  ({label})"


def print_results(result: OutreachResult, company_name: str) -> None:
    print("\n" + "═" * 60)
    print(f"  {company_name}  ─  アウトリーチレポート")
    print("═" * 60)

    # Priority
    print(f"\n【優先度スコア】  {_priority_bar(result.priority_score)}")
    print(f"  {result.priority_reason}")

    # Recommended contact
    print(f"\n【推奨コンタクト先】  {result.recommended_contact}")

    # Analysis summary
    print(f"\n【企業分析サマリー】")
    print(f"  {result.analysis_summary}")

    # Pain points
    print(f"\n【採用課題・ペインポイント】")
    for i, point in enumerate(result.pain_points, 1):
        print(f"  {i}. {point}")

    # Email variations
    for i, email in enumerate(result.emails, 1):
        print(f"\n{SEP}")
        print(f"  営業メール案 {i}  ／  アプローチ: {email.angle}")
        print(SEP)
        print(f"件名:  {email.subject}")
        print()
        print(email.body)

    # Talking points
    print(f"\n{SEP}")
    print("  フォローアップ トーキングポイント（電話フォロー時）")
    print(SEP)
    for point in result.talking_points:
        print(f"  •  {point}")

    print()


def save_results(result: OutreachResult, output_path: str, company_name: str) -> None:
    data = {
        "company_name": company_name,
        "priority_score": result.priority_score,
        "priority_reason": result.priority_reason,
        "analysis_summary": result.analysis_summary,
        "pain_points": result.pain_points,
        "recommended_contact": result.recommended_contact,
        "emails": [
            {
                "angle": e.angle,
                "subject": e.subject,
                "body": e.body,
            }
            for e in result.emails
        ],
        "talking_points": result.talking_points,
    }
    Path(output_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="企業名を入力すると採用状況を分析し、個別最適化された営業メールを生成します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py "株式会社メルカリ"
  python main.py "サイバーエージェント" --industry "IT・Web" --variations 3
  python main.py "パナソニック株式会社" --output panasonic_outreach.json

環境変数:
  ANTHROPIC_API_KEY  (必須) Anthropic API キー
        """,
    )
    parser.add_argument(
        "company_name",
        help="営業対象の企業名（例: 株式会社メルカリ）",
    )
    parser.add_argument(
        "--industry",
        metavar="INDUSTRY",
        default=None,
        help="業界名（省略可）。指定すると業界コンテキストも調査します。例: IT・Web, 製造業, 小売",
    )
    parser.add_argument(
        "--variations",
        type=int,
        default=2,
        choices=[1, 2, 3],
        metavar="N",
        help="生成するメールのバリエーション数 1〜3（デフォルト: 2）",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="結果をJSONファイルに保存するパス（省略可）",
    )
    return parser


def main() -> None:
    print(BANNER)
    parser = build_parser()
    args = parser.parse_args()

    company = args.company_name

    try:
        # ── Step 1: Web research ───────────────────────────────────────────
        print(f"🔍  「{company}」の情報を調査中...\n")
        research_data = research_company(company, args.industry)

        if research_data.has_data():
            found = sum([
                len(research_data.overview_results),
                len(research_data.job_listing_results),
                len(research_data.news_results),
                len(research_data.industry_results),
            ])
            print(f"✓  調査完了 ({found} 件の検索結果を取得)\n")
        else:
            print("✓  調査スキップ（duckduckgo-search 未インストール）\n")

        # ── Step 2: Analysis + email generation ───────────────────────────
        print(f"📝  メール生成中...\n")
        result = generate_outreach(company, research_data, args.variations)
        print("✓  生成完了\n")

        # ── Step 3: Display ────────────────────────────────────────────────
        print_results(result, company)

        # ── Step 4: Save (optional) ────────────────────────────────────────
        if args.output:
            save_results(result, args.output, company)
            print(f"💾  結果を保存しました: {args.output}\n")

    except KeyboardInterrupt:
        print("\n\n処理を中断しました。")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌  エラーが発生しました: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
