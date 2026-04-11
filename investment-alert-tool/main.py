#!/usr/bin/env python3
"""
投資アラートツール (Investment Alert Tool)
=========================================
株価を監視し、テクニカルシグナルの検出と Claude AI による分析を行います。

使用例:
  python main.py                     # ウォッチリスト全銘柄をスキャン
  python main.py -s AAPL             # 特定銘柄のみ
  python main.py -s AAPL -a          # AI 詳細分析付き
  python main.py --monitor 300       # 5分ごとに繰り返し監視
  python main.py --portfolio         # ポートフォリオサマリーのみ
  python main.py -s 7203.T -a        # 日本株 (トヨタ) を AI 分析
"""

import argparse
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from config import WATCHLIST, PORTFOLIO
from fetcher import fetch_stock_data, fetch_ticker_info, get_current_price
from indicators import add_all_indicators
from signals import detect_signals, summarize_signals, Signal
from portfolio import Portfolio, PositionPnL
from analyzer import analyze_with_claude


# ── 表示ユーティリティ ────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"


def color(text: str, code: str) -> str:
    return f"{code}{text}{RESET}"


def print_header():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print(color("=" * 62, BOLD))
    print(color("  📈  投資アラートツール  (Investment Alert Tool)", BOLD))
    print(color(f"  🕐  {now}", DIM))
    print(color("=" * 62, BOLD))


def print_separator():
    print(color("  " + "-" * 58, DIM))


def fmt_price(value: float) -> str:
    if value >= 10000:
        return f"{value:,.0f}"
    return f"{value:.2f}"


def fmt_change(pct: float) -> str:
    sign = "+" if pct >= 0 else ""
    arrow = "▲" if pct >= 0 else "▼"
    col = GREEN if pct >= 0 else RED
    return color(f"{arrow} {sign}{pct:.2f}%", col)


def signal_badge(sig_type: str) -> str:
    if sig_type == "BUY":
        return color("[BUY ]", GREEN + BOLD)
    elif sig_type == "SELL":
        return color("[SELL]", RED + BOLD)
    else:
        return color("[INFO]", YELLOW)


def summary_badge(summary: str) -> str:
    labels = {
        "STRONG_BUY":  color("⬆⬆ 強い買い", GREEN + BOLD),
        "BUY":         color("⬆  買い",      GREEN),
        "NEUTRAL":     color("━  中立",       DIM),
        "SELL":        color("⬇  売り",       RED),
        "STRONG_SELL": color("⬇⬇ 強い売り",  RED + BOLD),
    }
    return labels.get(summary, summary)


# ── スキャン処理 ───────────────────────────────────────────────────

def scan_symbol(
    symbol: str,
    name: str,
    portfolio: Portfolio,
    current_prices: Dict[str, float],
    analyze: bool = False,
    verbose: bool = False,
) -> Optional[List[Signal]]:
    """
    1銘柄をスキャンして結果を表示する

    Returns:
        検出されたシグナルのリスト（エラー時は None）
    """
    print(f"\n  {BOLD}{CYAN}{name}  ({symbol}){RESET}")
    print_separator()

    try:
        # データ取得
        df = fetch_stock_data(symbol, period="6mo")
        if df.empty or len(df) < 30:
            print(f"    ❌ データ不足（最低30日分必要）")
            return None

        # インジケータ追加
        df = add_all_indicators(df)

        # 価格情報
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["Close"])
        prev_close = float(prev["Close"])
        price_change_pct = (close - prev_close) / prev_close * 100

        current_prices[symbol] = close

        print(f"    現在値: {BOLD}{fmt_price(close)}{RESET}  {fmt_change(price_change_pct)}")

        # 主要インジケータ
        if verbose:
            rsi_val = latest.get("RSI")
            macd_val = latest.get("MACD")
            macd_sig_val = latest.get("MACD_Signal")
            sma5 = latest.get("SMA_5")
            sma25 = latest.get("SMA_25")

            if rsi_val is not None and not pd.isna(rsi_val):
                rsi_label = ""
                if rsi_val > 70:
                    rsi_label = color("  ⚠ 買われすぎ", RED)
                elif rsi_val < 30:
                    rsi_label = color("  ⚠ 売られすぎ", GREEN)
                print(f"    RSI(14):  {rsi_val:.1f}{rsi_label}")

            if macd_val is not None and macd_sig_val is not None:
                if not (pd.isna(macd_val) or pd.isna(macd_sig_val)):
                    cross = color("↑ 上回り", GREEN) if macd_val > macd_sig_val else color("↓ 下回り", RED)
                    print(f"    MACD:     {macd_val:.4f} / {macd_sig_val:.4f}  {cross}")

            if sma5 is not None and sma25 is not None:
                if not (pd.isna(sma5) or pd.isna(sma25)):
                    trend = color("上昇トレンド", GREEN) if sma5 > sma25 else color("下降トレンド", RED)
                    print(f"    SMA5/25:  {fmt_price(sma5)} / {fmt_price(sma25)}  {trend}")

        # シグナル検出
        signals = detect_signals(df, symbol)
        summary = summarize_signals(signals)

        print(f"    総合評価: {summary_badge(summary)}")

        if signals:
            print(f"    シグナル ({len(signals)}件):")
            for sig in signals:
                strength_icon = {"STRONG": "●", "MODERATE": "○", "WEAK": "·"}.get(sig.strength, "·")
                print(f"      {strength_icon} {signal_badge(sig.signal_type)} {sig.reason}")

        # ポートフォリオ損益
        pnl_map = portfolio.get_pnl(current_prices)
        pos_pnl: Optional[PositionPnL] = pnl_map.get(symbol)
        if pos_pnl:
            pnl_str = fmt_change(pos_pnl.pnl_pct)
            print(
                f"    保有: {pos_pnl.shares}株 @ {fmt_price(pos_pnl.avg_cost)}  →  "
                f"損益 {pnl_str}  ({pos_pnl.pnl:+,.0f})"
            )

        # AI 分析（要求があるか、強いシグナルがあるとき）
        should_analyze = analyze or any(s.strength == "STRONG" for s in signals)
        if should_analyze:
            ticker_info = fetch_ticker_info(symbol) if analyze else None
            print(f"\n    {BOLD}🤖 Claude AI 分析中...{RESET}")
            print("  " + "─" * 58)
            analyze_with_claude(symbol, df, signals, pos_pnl, ticker_info)
            print("  " + "─" * 58)

        return signals

    except Exception as exc:
        print(f"    ❌ エラー: {exc}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


def show_portfolio_summary(portfolio: Portfolio, current_prices: Dict[str, float]):
    """ポートフォリオサマリーを表示する"""
    if not portfolio.positions:
        return

    pnl_map = portfolio.get_pnl(current_prices)
    total = pnl_map.get("_total")
    if not total:
        return

    print()
    print(color("  " + "=" * 58, BOLD))
    print(color("    💼  ポートフォリオ サマリー", BOLD))
    print(color("  " + "=" * 58, BOLD))

    # 個別ポジション
    for pos in portfolio.positions:
        p = pnl_map.get(pos.symbol)
        if p:
            print(
                f"    {pos.symbol:<10} {p.shares:>6.0f}株  "
                f"取得: {fmt_price(p.avg_cost):>10}  "
                f"評価: {fmt_price(p.current_price):>10}  "
                f"{fmt_change(p.pnl_pct)}"
            )

    print(color("  " + "─" * 58, DIM))
    total_col = GREEN if total.pnl >= 0 else RED
    print(
        f"    {'合計':<10}"
        f"{'投資額':>20}: {total.cost_basis:>12,.0f}\n"
        f"{'':>10}{'評価額':>20}: {total.market_value:>12,.0f}\n"
        f"{'':>10}{'評価損益':>20}: "
        + color(f"{total.pnl:>+12,.0f}  ({total.pnl_pct:+.1f}%)", total_col)
    )


# ── メイン ──────────────────────────────────────────────────────────

def run_scan(
    targets: List[dict],
    portfolio: Portfolio,
    analyze: bool,
    verbose: bool,
    portfolio_only: bool,
):
    """スキャンを1回実行する"""
    print_header()
    current_prices: Dict[str, float] = {}

    if portfolio_only:
        # ポートフォリオのみ: 価格だけ取得
        for pos in portfolio.positions:
            price = get_current_price(pos.symbol)
            if price:
                current_prices[pos.symbol] = price
    else:
        for t in targets:
            scan_symbol(
                t["symbol"],
                t["name"],
                portfolio,
                current_prices,
                analyze=analyze,
                verbose=verbose,
            )

    # ポートフォリオサマリー
    if portfolio.positions:
        show_portfolio_summary(portfolio, current_prices)

    print(color(f"\n  ✅ スキャン完了: {datetime.now().strftime('%H:%M:%S')}", DIM))


def main():
    parser = argparse.ArgumentParser(
        prog="investment-alert",
        description="投資アラートツール — 株価監視・テクニカルシグナル・AI分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--symbol", "-s",
        metavar="CODE",
        help="特定銘柄のみスキャン (例: AAPL, NVDA, 7203.T)",
    )
    parser.add_argument(
        "--analyze", "-a",
        action="store_true",
        help="すべての対象銘柄で Claude AI 詳細分析を実行",
    )
    parser.add_argument(
        "--monitor", "-m",
        type=int,
        metavar="SECONDS",
        help="指定秒ごとに繰り返し監視（例: --monitor 300 で5分ごと）",
    )
    parser.add_argument(
        "--portfolio", "-p",
        action="store_true",
        help="ポートフォリオサマリーのみ表示",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細な指標情報を表示",
    )
    parser.add_argument(
        "--watchlist",
        action="store_true",
        help="現在のウォッチリストを表示して終了",
    )

    args = parser.parse_args()

    # ウォッチリスト表示
    if args.watchlist:
        print("\n📋 ウォッチリスト:")
        for item in WATCHLIST:
            print(f"  {item['symbol']:<12} {item['name']}")
        print()
        sys.exit(0)

    portfolio = Portfolio(PORTFOLIO)

    # スキャン対象を決定
    if args.symbol:
        sym = args.symbol.upper()
        # ウォッチリストから名前を検索
        name = next((w["name"] for w in WATCHLIST if w["symbol"].upper() == sym), sym)
        targets = [{"symbol": sym, "name": name}]
    else:
        targets = WATCHLIST

    def do_scan():
        run_scan(
            targets=targets,
            portfolio=portfolio,
            analyze=args.analyze,
            verbose=args.verbose,
            portfolio_only=args.portfolio,
        )

    if args.monitor:
        print(color(f"\n  📡 監視モード: {args.monitor}秒ごとに更新  (Ctrl+C で終了)", CYAN))
        while True:
            try:
                do_scan()
                print(color(f"\n  ⏳ {args.monitor}秒後に次回スキャン...", DIM))
                time.sleep(args.monitor)
            except KeyboardInterrupt:
                print(color("\n\n  👋 監視を終了しました。", BOLD))
                break
    else:
        do_scan()


if __name__ == "__main__":
    main()
