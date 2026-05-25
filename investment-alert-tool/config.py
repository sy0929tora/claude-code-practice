# ==============================================================
# 投資アラートツール 設定ファイル
# このファイルを編集してウォッチリストやポートフォリオを設定してください
# ==============================================================

# 監視銘柄リスト（米国株・日本株・ETFなど何でも可）
# 日本株は銘柄コード + ".T" 例: 7203.T (トヨタ)
WATCHLIST = [
    {"symbol": "9433.T", "name": "KDDI"},
    {"symbol": "9889.T", "name": "JBCC HD"},
    {"symbol": "VOO",    "name": "VOO (S&P500)"},
    {"symbol": "MSFT",   "name": "マイクロソフト"},
    {"symbol": "NVDA",   "name": "エヌビディア"},
    {"symbol": "IONQ",   "name": "IonQ"},
]

# 保有銘柄・ポートフォリオ（空リストでも可）
PORTFOLIO = [
    {"symbol": "9433.T", "shares": 100, "avg_cost": 2653.0},
    {"symbol": "9889.T", "shares": 100, "avg_cost": 1178.0},
    {"symbol": "VOO",    "shares": 2,   "avg_cost": 652.83},
    {"symbol": "MSFT",   "shares": 1,   "avg_cost": 376.34},
    {"symbol": "NVDA",   "shares": 1,   "avg_cost": 175.00},
    {"symbol": "IONQ",   "shares": 4,   "avg_cost": 28.58},
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
