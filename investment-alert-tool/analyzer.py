"""
Claude AI 分析モジュール
Anthropic SDK を使って投資データを AI で分析します
"""

import anthropic
import pandas as pd
import numpy as np
from typing import List, Optional, TYPE_CHECKING

from config import ANTHROPIC_MODEL
from signals import Signal

if TYPE_CHECKING:
    from portfolio import PositionPnL


def _format_num(val, decimals: int = 2, prefix: str = "", suffix: str = "") -> str:
    """数値のフォーマット（NaN対応）"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return f"{prefix}{val:.{decimals}f}{suffix}"


def build_analysis_prompt(
    symbol: str,
    df: pd.DataFrame,
    signals: List[Signal],
    position_pnl: Optional["PositionPnL"] = None,
    ticker_info: dict = None,
) -> str:
    """Claude に送るプロンプトを構築する"""

    if df.empty or len(df) < 2:
        return f"{symbol} のデータが取得できませんでした。"

    latest = df.iloc[-1]

    close = latest.get("Close", float("nan"))
    prev_close = df.iloc[-2].get("Close", float("nan"))
    rsi_val = latest.get("RSI", float("nan"))
    macd_val = latest.get("MACD", float("nan"))
    macd_sig = latest.get("MACD_Signal", float("nan"))
    sma5 = latest.get("SMA_5", float("nan"))
    sma25 = latest.get("SMA_25", float("nan"))
    sma75 = latest.get("SMA_75", float("nan"))
    bb_upper = latest.get("BB_Upper", float("nan"))
    bb_lower = latest.get("BB_Lower", float("nan"))
    stoch_k = latest.get("Stoch_K", float("nan"))
    vol = latest.get("Volume", float("nan"))
    vol_sma = latest.get("Volume_SMA_20", float("nan"))

    # 過去5日間の終値
    recent_closes = df["Close"].tail(5)
    recent_str = "\n".join(
        f"  {idx.strftime('%m/%d') if hasattr(idx, 'strftime') else idx}: "
        f"{_format_num(val)}"
        for idx, val in recent_closes.items()
    )

    # 過去30日のリターン
    ret_30d = float("nan")
    if len(df) >= 30:
        ret_30d = (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-30])) / float(df["Close"].iloc[-30]) * 100

    # シグナルテキスト
    signal_text = ""
    if signals:
        signal_text = "\n【検出シグナル】\n"
        for s in signals:
            strength_label = {"STRONG": "強", "MODERATE": "中", "WEAK": "弱"}.get(s.strength, s.strength)
            signal_text += f"  ・[{s.signal_type}] {s.reason}（強度: {strength_label}）\n"
    else:
        signal_text = "\n【検出シグナル】\n  特筆すべきシグナルなし\n"

    # ポートフォリオ情報
    portfolio_text = ""
    if position_pnl and position_pnl.symbol == symbol:
        p = position_pnl
        portfolio_text = f"""
【保有状況】
  保有株数: {p.shares}株
  平均取得価格: {_format_num(p.avg_cost)}
  取得コスト: {_format_num(p.cost_basis, 0)} 円/ドル
  現在評価額: {_format_num(p.market_value, 0)} 円/ドル
  評価損益: {_format_num(p.pnl, 0)} ({_format_num(p.pnl_pct, 1)}%)
"""

    # 銘柄基本情報
    info_text = ""
    if ticker_info:
        info_text = f"""
【銘柄基本情報】
  銘柄名: {ticker_info.get('name', symbol)}
  セクター: {ticker_info.get('sector', 'N/A')}
  PER: {_format_num(ticker_info.get('pe_ratio'), 1, suffix='倍')}
  配当利回り: {_format_num(ticker_info.get('dividend_yield'), 2, suffix='%') if ticker_info.get('dividend_yield') else 'N/A'}
  アナリスト目標株価: {_format_num(ticker_info.get('analyst_target'))}
  52週高値: {_format_num(ticker_info.get('52w_high'))}
  52週安値: {_format_num(ticker_info.get('52w_low'))}
"""

    prompt = f"""以下の投資データを分析し、{symbol} への投資判断をアドバイスしてください。

【銘柄】{symbol}
{info_text}
【価格情報】
  現在値: {_format_num(close)}
  前日終値: {_format_num(prev_close)}
  前日比: {_format_num((close - prev_close) / prev_close * 100 if not (np.isnan(close) or np.isnan(prev_close)) else float('nan'), 2, suffix='%')}
  30日リターン: {_format_num(ret_30d, 1, suffix='%')}

【テクニカル指標】
  RSI(14): {_format_num(rsi_val, 1)}（70↑=買われすぎ, 30↓=売られすぎ）
  MACD: {_format_num(macd_val, 4)}
  MACDシグナル: {_format_num(macd_sig, 4)}
  SMA(5): {_format_num(sma5)}
  SMA(25): {_format_num(sma25)}
  SMA(75): {_format_num(sma75)}
  ボリンジャーバンド 上限: {_format_num(bb_upper)}
  ボリンジャーバンド 下限: {_format_num(bb_lower)}
  ストキャスティクス %K: {_format_num(stoch_k, 1)}
  出来高: {_format_num(vol, 0)} / 20日平均: {_format_num(vol_sma, 0)}

【直近5日間の終値】
{recent_str}
{signal_text}
{portfolio_text}
---
以下の観点で分析してください:

1. **総合評価**: 現在のテクニカル状況を一言で（強い買い/買い/中立/売り/強い売り）
2. **シグナル解釈**: 検出されたシグナルの意味と信頼性
3. **推奨アクション**: 具体的な行動指針（新規買い/買い増し/様子見/一部利確/全額売却）とその理由
4. **リスク要因**: 注意すべきリスクや逆張りシナリオ
5. **目標・損切ライン**: テクニカルに基づいた目標値と損切り水準の目安
6. **見通し**: 短期（1週間）と中期（1ヶ月）の方向性

⚠️ 注意: この分析はテクニカル指標に基づく参考情報です。投資判断は必ずご自身の責任でお願いします。"""

    return prompt


def analyze_with_claude(
    symbol: str,
    df: pd.DataFrame,
    signals: List[Signal],
    position_pnl: Optional["PositionPnL"] = None,
    ticker_info: dict = None,
    stream_output: bool = True,
) -> str:
    """
    Claude を使って投資データを分析する（ストリーミング対応）

    Args:
        symbol: 銘柄コード
        df: インジケータ付き DataFrame
        signals: 検出シグナルリスト
        position_pnl: 保有ポジション損益（未保有の場合は None）
        ticker_info: 銘柄基本情報（fetch_ticker_info の返り値）
        stream_output: True の場合、分析をリアルタイム出力する

    Returns:
        分析テキスト全文
    """
    client = anthropic.Anthropic()

    prompt = build_analysis_prompt(symbol, df, signals, position_pnl, ticker_info)

    system_prompt = (
        "あなたは豊富な経験を持つ投資アナリストです。"
        "テクニカル分析を中心に、客観的かつ実践的な投資アドバイスを提供します。"
        "分析は簡潔かつ具体的に行い、投資家が即座にアクションを取れるよう心がけてください。"
        "必ず最後に免責事項を付けてください。"
    )

    result = ""

    # ストリーミングで応答を受信（adaptive thinking + 長文対応）
    with client.messages.stream(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            result += text
            if stream_output:
                print(text, end="", flush=True)

    if stream_output:
        print()  # 改行

    return result
