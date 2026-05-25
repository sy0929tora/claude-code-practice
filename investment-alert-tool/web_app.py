"""
投資アラートツール — Webアプリ版
iPhoneのSafariからアクセスできるWebインターフェース
"""

import json
import math
import os

import pandas as pd
from flask import Flask, Response, render_template, stream_with_context

import anthropic
from analyzer import build_analysis_prompt
from config import PORTFOLIO, WATCHLIST
from fetcher import fetch_stock_data, fetch_ticker_info
from indicators import add_all_indicators
from portfolio import Portfolio
from signals import detect_signals, summarize_signals

app = Flask(__name__)
portfolio = Portfolio(PORTFOLIO)

# スキャン結果のキャッシュ（市場閉鎖時に最終データを返すため）
_scan_cache: dict = {}


def _safe_float(val) -> float | None:
    """NaN / None を None に変換"""
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


# ── API エンドポイント ────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/watchlist")
def api_watchlist():
    """ウォッチリストを返す"""
    return {"watchlist": WATCHLIST}


@app.route("/api/fx")
def api_fx():
    """USD/JPY リアルタイムレートを返す"""
    try:
        import yfinance as yf
        ticker = yf.Ticker("USDJPY=X")
        rate = ticker.fast_info.last_price
        return {"usdjpy": round(float(rate), 2)}
    except Exception as exc:
        return {"error": str(exc), "usdjpy": 150.0}, 200


@app.route("/api/news/<symbol>")
def api_news(symbol: str):
    """Yahoo Finance RSSからニュースを取得する"""
    import urllib.request
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    symbol = symbol.upper()
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        items = []
        for item in (channel.findall("item") if channel is not None else [])[:6]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub = item.findtext("pubDate", "")
            try:
                dt = parsedate_to_datetime(pub)
                pub_fmt = dt.strftime("%m/%d %H:%M")
            except Exception:
                pub_fmt = pub[:16]
            items.append({"title": title, "link": link, "pub": pub_fmt})
        return {"news": items, "symbol": symbol}
    except Exception as exc:
        return {"error": str(exc), "news": []}, 200


@app.route("/api/scan/<symbol>")
def api_scan(symbol: str):
    """1銘柄をスキャンして価格・指標・シグナルを返す"""
    symbol = symbol.upper()
    name = next((w["name"] for w in WATCHLIST if w["symbol"].upper() == symbol), symbol)

    try:
        df = fetch_stock_data(symbol, period="6mo")
        if df.empty or len(df) < 30:
            return {"error": "データ不足（最低30日分が必要）", "symbol": symbol}, 400

        df = add_all_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        close = float(latest["Close"])
        prev_close = float(prev["Close"])
        change_pct = (close - prev_close) / prev_close * 100

        signals = detect_signals(df, symbol)
        summary = summarize_signals(signals)

        current_prices = {symbol: close}
        pnl_map = portfolio.get_pnl(current_prices)
        pos = pnl_map.get(symbol)

        result = {
            "symbol": symbol,
            "name": name,
            "price": round(close, 2),
            "change_pct": round(change_pct, 2),
            "rsi": _safe_float(latest.get("RSI")),
            "macd": _safe_float(latest.get("MACD")),
            "macd_signal": _safe_float(latest.get("MACD_Signal")),
            "sma5": _safe_float(latest.get("SMA_5")),
            "sma25": _safe_float(latest.get("SMA_25")),
            "bb_upper": _safe_float(latest.get("BB_Upper")),
            "bb_lower": _safe_float(latest.get("BB_Lower")),
            "stoch_k": _safe_float(latest.get("Stoch_K")),
            "signals": [
                {"type": s.signal_type, "reason": s.reason, "strength": s.strength}
                for s in signals
            ],
            "summary": summary,
            "chart": {
                "dates": [d.strftime("%m/%d") for d in df.index[-60:]],
                "closes": [round(float(v), 2) for v in df["Close"].iloc[-60:]],
                "sma25": [_safe_float(v) for v in df["SMA_25"].iloc[-60:]],
            },
        }

        if pos:
            result["portfolio"] = {
                "shares": pos.shares,
                "avg_cost": round(pos.avg_cost, 2),
                "pnl": round(pos.pnl, 0),
                "pnl_pct": round(pos.pnl_pct, 1),
            }

        # キャッシュに保存
        _scan_cache[symbol] = result
        return result

    except Exception as exc:
        # キャッシュがあれば返す（市場閉鎖時など）
        if symbol in _scan_cache:
            cached = dict(_scan_cache[symbol])
            cached["cached"] = True
            return cached
        return {"error": str(exc), "symbol": symbol}, 500


@app.route("/api/analyze/<symbol>")
def api_analyze(symbol: str):
    """Claude AI による分析をストリーミングで返す (SSE)"""
    symbol = symbol.upper()

    def generate():
        try:
            df = fetch_stock_data(symbol, period="6mo")
            if df.empty or len(df) < 30:
                yield f"data: {json.dumps({'error': 'データ不足'})}\n\n"
                return

            df = add_all_indicators(df)
            signals = detect_signals(df, symbol)

            close = float(df["Close"].iloc[-1])
            current_prices = {symbol: close}
            pnl_map = portfolio.get_pnl(current_prices)
            pos_pnl = pnl_map.get(symbol)

            ticker_info = fetch_ticker_info(symbol)
            prompt = build_analysis_prompt(symbol, df, signals, pos_pnl, ticker_info)

            system_prompt = (
                "あなたは豊富な経験を持つ投資アナリストです。"
                "テクニカル分析を中心に、客観的かつ実践的な投資アドバイスを提供します。"
                "分析は簡潔かつ具体的に行い、投資家が即座にアクションを取れるよう心がけてください。"
            )

            client = anthropic.Anthropic()
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2048,
                thinking={"type": "adaptive"},
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── 起動 ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
