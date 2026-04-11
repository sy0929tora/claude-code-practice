"""
テクニカル指標計算モジュール
主要なテクニカル指標を pandas/numpy で計算します
"""

import pandas as pd
import numpy as np


def sma(prices: pd.Series, window: int) -> pd.Series:
    """単純移動平均 (Simple Moving Average)"""
    return prices.rolling(window=window).mean()


def ema(prices: pd.Series, window: int) -> pd.Series:
    """指数移動平均 (Exponential Moving Average)"""
    return prices.ewm(span=window, adjust=False).mean()


def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index)
    70以上: 買われすぎ, 30以下: 売られすぎ
    """
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal_period: int = 9):
    """
    MACD (Moving Average Convergence Divergence)

    Returns:
        tuple: (macd_line, signal_line, histogram)
    """
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0):
    """
    ボリンジャーバンド

    Returns:
        tuple: (upper_band, middle_band, lower_band)
    """
    middle = sma(prices, window)
    std = prices.rolling(window=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    """
    ストキャスティクス (%K, %D)

    Returns:
        tuple: (k_line, d_line)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    d = k.rolling(window=d_period).mean()
    return k, d


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    ATR (Average True Range) - ボラティリティ指標
    """
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameにすべてのテクニカル指標を追加する

    Args:
        df: Open, High, Low, Close, Volume を含むDataFrame

    Returns:
        指標を追加したDataFrame
    """
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # 移動平均
    df["SMA_5"] = sma(close, 5)
    df["SMA_25"] = sma(close, 25)
    df["SMA_75"] = sma(close, 75)
    df["EMA_12"] = ema(close, 12)
    df["EMA_26"] = ema(close, 26)

    # RSI
    df["RSI"] = rsi(close)

    # MACD
    df["MACD"], df["MACD_Signal"], df["MACD_Hist"] = macd(close)

    # ボリンジャーバンド
    df["BB_Upper"], df["BB_Mid"], df["BB_Lower"] = bollinger_bands(close)
    # バンド幅（ボラティリティの目安）
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Mid"]

    # ストキャスティクス
    df["Stoch_K"], df["Stoch_D"] = stochastic(high, low, close)

    # ATR
    df["ATR"] = atr(high, low, close)

    # 出来高移動平均
    df["Volume_SMA_20"] = df["Volume"].rolling(20).mean()

    # 価格変化率
    df["Return_1d"] = close.pct_change(1)
    df["Return_5d"] = close.pct_change(5)

    return df
