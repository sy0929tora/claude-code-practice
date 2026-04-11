# ==============================================================
# 投資アラートツール 設定ファイル
# このファイルを編集してウォッチリストやポートフォリオを設定してください
# ==============================================================

# 監視銘柄リスト（米国株・日本株・ETFなど何でも可）
# 日本株は銘柄コード + ".T" 例: 7203.T (トヨタ)
WATCHLIST = [
    {"symbol": "AAPL",   "name": "Apple"},
    {"symbol": "NVDA",   "name": "NVIDIA"},
    {"symbol": "TSLA",   "name": "Tesla"},
    {"symbol": "7203.T", "name": "トヨタ自動車"},
    {"symbol": "9984.T", "name": "ソフトバンクグループ"},
    {"symbol": "SPY",    "name": "S&P500 ETF"},
]

# 保有銘柄・ポートフォリオ（空リストでも可）
PORTFOLIO = [
    {"symbol": "AAPL",   "shares": 10,  "avg_cost": 175.0},
    {"symbol": "NVDA",   "shares": 5,   "avg_cost": 450.0},
    {"symbol": "7203.T", "shares": 100, "avg_cost": 2800.0},
]

# アラート閾値
ALERT_THRESHOLDS = {
    "rsi_overbought": 70,       # RSI買われすぎ
    "rsi_oversold": 30,         # RSI売られすぎ
    "rsi_strong_overbought": 80,
    "rsi_strong_oversold": 20,
    "volume_spike_multiplier": 2.0,  # 出来高スパイク（平均の何倍）
    "price_change_alert": 0.05,      # 価格変動アラート（±5%）
    "price_change_strong": 0.08,     # 強いアラート（±8%）
}

# Claude AIモデル設定
ANTHROPIC_MODEL = "claude-opus-4-6"
