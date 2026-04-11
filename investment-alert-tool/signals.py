"""
売買シグナル検出モジュール
テクニカル指標からBUY/SELL/ALERTシグナルを生成します
"""

from dataclasses import dataclass
from typing import List
import pandas as pd
import numpy as np
from config import ALERT_THRESHOLDS


@dataclass
class Signal:
    """売買シグナル"""
    signal_type: str   # 'BUY', 'SELL', 'ALERT'
    reason: str        # シグナルの理由（日本語）
    strength: str      # 'STRONG', 'MODERATE', 'WEAK'
    value: float = 0.0  # 関連する数値

    def __str__(self) -> str:
        strength_map = {"STRONG": "強", "MODERATE": "中", "WEAK": "弱"}
        return f"[{self.signal_type}] {self.reason} (強度: {strength_map.get(self.strength, self.strength)})"


def _val(series_val) -> float:
    """NaN チェック付きで float に変換"""
    if series_val is None or (isinstance(series_val, float) and np.isnan(series_val)):
        return float("nan")
    return float(series_val)


def detect_signals(df: pd.DataFrame, symbol: str = "") -> List[Signal]:
    """
    DataFrameからテクニカルシグナルを検出する

    Args:
        df: add_all_indicators() 済みのDataFrame
        symbol: 銘柄コード（ログ用）

    Returns:
        検出されたSignalのリスト
    """
    signals: List[Signal] = []

    if len(df) < 2:
        return signals

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # ---- RSI -------------------------------------------------------
    rsi = _val(latest.get("RSI"))
    if not np.isnan(rsi):
        thresholds = ALERT_THRESHOLDS
        if rsi < thresholds["rsi_strong_oversold"]:
            signals.append(Signal("BUY", f"RSI 強売られすぎ ({rsi:.1f})", "STRONG", rsi))
        elif rsi < thresholds["rsi_oversold"]:
            signals.append(Signal("BUY", f"RSI 売られすぎ ({rsi:.1f})", "MODERATE", rsi))
        elif rsi > thresholds["rsi_strong_overbought"]:
            signals.append(Signal("SELL", f"RSI 強買われすぎ ({rsi:.1f})", "STRONG", rsi))
        elif rsi > thresholds["rsi_overbought"]:
            signals.append(Signal("SELL", f"RSI 買われすぎ ({rsi:.1f})", "MODERATE", rsi))

    # ---- ストキャスティクス ----------------------------------------
    stoch_k = _val(latest.get("Stoch_K"))
    stoch_d = _val(latest.get("Stoch_D"))
    prev_k = _val(prev.get("Stoch_K"))
    prev_d = _val(prev.get("Stoch_D"))
    if not any(np.isnan(v) for v in [stoch_k, stoch_d, prev_k, prev_d]):
        if stoch_k < 20 and stoch_d < 20:
            signals.append(Signal("BUY", f"ストキャス 売られすぎ (K={stoch_k:.1f})", "MODERATE", stoch_k))
        elif stoch_k > 80 and stoch_d > 80:
            signals.append(Signal("SELL", f"ストキャス 買われすぎ (K={stoch_k:.1f})", "MODERATE", stoch_k))
        # %K が %D を上抜け（売られすぎ圏内）
        if prev_k <= prev_d and stoch_k > stoch_d and stoch_k < 30:
            signals.append(Signal("BUY", "ストキャス 上抜けクロス", "WEAK", stoch_k))
        elif prev_k >= prev_d and stoch_k < stoch_d and stoch_k > 70:
            signals.append(Signal("SELL", "ストキャス 下抜けクロス", "WEAK", stoch_k))

    # ---- ゴールデンクロス / デッドクロス (SMA5/SMA25) ---------------
    sma5 = _val(latest.get("SMA_5"))
    sma25 = _val(latest.get("SMA_25"))
    prev_sma5 = _val(prev.get("SMA_5"))
    prev_sma25 = _val(prev.get("SMA_25"))
    if not any(np.isnan(v) for v in [sma5, sma25, prev_sma5, prev_sma25]):
        if prev_sma5 <= prev_sma25 and sma5 > sma25:
            signals.append(Signal("BUY", "ゴールデンクロス (SMA5 > SMA25)", "STRONG", sma5))
        elif prev_sma5 >= prev_sma25 and sma5 < sma25:
            signals.append(Signal("SELL", "デッドクロス (SMA5 < SMA25)", "STRONG", sma5))

    # ---- MACD クロス -----------------------------------------------
    macd = _val(latest.get("MACD"))
    macd_sig = _val(latest.get("MACD_Signal"))
    prev_macd = _val(prev.get("MACD"))
    prev_macd_sig = _val(prev.get("MACD_Signal"))
    if not any(np.isnan(v) for v in [macd, macd_sig, prev_macd, prev_macd_sig]):
        if prev_macd <= prev_macd_sig and macd > macd_sig:
            strength = "STRONG" if macd < 0 else "MODERATE"  # ゼロライン下からのクロスは強め
            signals.append(Signal("BUY", "MACDゴールデンクロス", strength, macd))
        elif prev_macd >= prev_macd_sig and macd < macd_sig:
            strength = "STRONG" if macd > 0 else "MODERATE"
            signals.append(Signal("SELL", "MACDデッドクロス", strength, macd))

    # ---- ボリンジャーバンド ----------------------------------------
    bb_upper = _val(latest.get("BB_Upper"))
    bb_lower = _val(latest.get("BB_Lower"))
    close = _val(latest.get("Close"))
    if not any(np.isnan(v) for v in [bb_upper, bb_lower, close]):
        if close < bb_lower:
            signals.append(Signal("BUY", f"ボリンジャー下限割れ (下限: {bb_lower:.2f})", "MODERATE", close))
        elif close > bb_upper:
            signals.append(Signal("SELL", f"ボリンジャー上限超え (上限: {bb_upper:.2f})", "MODERATE", close))

    # ---- 出来高スパイク --------------------------------------------
    volume = _val(latest.get("Volume"))
    vol_sma = _val(latest.get("Volume_SMA_20"))
    prev_close = _val(prev.get("Close"))
    if not any(np.isnan(v) for v in [volume, vol_sma]) and vol_sma > 0:
        ratio = volume / vol_sma
        threshold = ALERT_THRESHOLDS["volume_spike_multiplier"]
        if ratio >= threshold:
            direction = "BUY" if (not np.isnan(close) and not np.isnan(prev_close) and close > prev_close) else "SELL"
            signals.append(Signal(
                "ALERT",
                f"出来高急増 ({ratio:.1f}倍, {'上昇' if direction == 'BUY' else '下落'})",
                "MODERATE",
                ratio,
            ))

    # ---- 急騰・急落アラート ----------------------------------------
    ret_1d = _val(latest.get("Return_1d"))
    if not np.isnan(ret_1d):
        strong_thresh = ALERT_THRESHOLDS["price_change_strong"]
        normal_thresh = ALERT_THRESHOLDS["price_change_alert"]
        if ret_1d <= -strong_thresh:
            signals.append(Signal("ALERT", f"急落 ({ret_1d*100:.1f}%)", "STRONG", ret_1d))
        elif ret_1d <= -normal_thresh:
            signals.append(Signal("ALERT", f"下落 ({ret_1d*100:.1f}%)", "MODERATE", ret_1d))
        elif ret_1d >= strong_thresh:
            signals.append(Signal("ALERT", f"急騰 ({ret_1d*100:+.1f}%)", "STRONG", ret_1d))
        elif ret_1d >= normal_thresh:
            signals.append(Signal("ALERT", f"上昇 ({ret_1d*100:+.1f}%)", "MODERATE", ret_1d))

    return signals


def summarize_signals(signals: List[Signal]) -> str:
    """シグナルリストを総合評価する"""
    if not signals:
        return "NEUTRAL"

    score = 0
    for sig in signals:
        weight = {"STRONG": 3, "MODERATE": 2, "WEAK": 1}.get(sig.strength, 1)
        if sig.signal_type == "BUY":
            score += weight
        elif sig.signal_type == "SELL":
            score -= weight

    if score >= 4:
        return "STRONG_BUY"
    elif score >= 2:
        return "BUY"
    elif score <= -4:
        return "STRONG_SELL"
    elif score <= -2:
        return "SELL"
    else:
        return "NEUTRAL"
