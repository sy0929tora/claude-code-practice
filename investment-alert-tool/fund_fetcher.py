"""
投資信託データ取得モジュール
Yahoo Finance Japan から基準価額をスクレイピング
"""

import re
import time
import pandas as pd
import urllib.request
from datetime import datetime, timedelta


def fetch_fund_data(fund_code: str, days: int = 365) -> pd.DataFrame:
    """
    投資信託の基準価額データを取得する

    Args:
        fund_code: ファンドコード (例: 0331418A)
        days: 取得日数

    Returns:
        DataFrame: Date index, Close (基準価額/10,000口) を含むデータフレーム
    """
    # まず yfinance で試みる
    try:
        import yfinance as yf
        for ticker in [f"{fund_code}.T", fund_code]:
            try:
                df = yf.Ticker(ticker).history(period="2y")
                if not df.empty and len(df) >= 5:
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                    return df
            except Exception:
                pass
    except Exception:
        pass

    # Yahoo Finance Japan からスクレイピング
    return _fetch_yahoo_japan(fund_code, days)


def _fetch_yahoo_japan(fund_code: str, days: int) -> pd.DataFrame:
    """Yahoo Finance Japan の投資信託ページから基準価額を取得"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 30)

    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    all_rows = []

    for page in range(1, 30):
        url = (
            f"https://finance.yahoo.co.jp/fund/historical"
            f"?code={fund_code}&startDate={start_str}&endDate={end_str}"
            f"&tm=d&p={page}"
        )
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
        except Exception:
            break

        rows = _parse_table(html)
        if not rows:
            break
        all_rows.extend(rows)

        # 次ページがなければ終了
        if not re.search(rf'[?&]p={page + 1}["\s&]', html) and "次へ" not in html:
            break
        time.sleep(0.3)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows, columns=["Date", "Close"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    df = df[~df.index.duplicated()]
    df["Open"] = df["Close"]
    df["High"] = df["Close"]
    df["Low"] = df["Close"]
    df["Volume"] = 0
    return df


def _parse_table(html: str):
    """HTML から 日付 / 基準価額 ペアを抽出"""
    rows = []
    tr_re = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
    td_re = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
    tag_re = re.compile(r"<[^>]+>")
    date_re = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")

    for tr in tr_re.finditer(html):
        cells = [tag_re.sub("", c).strip() for c in td_re.findall(tr.group(1))]
        if len(cells) < 2:
            continue
        dm = date_re.search(cells[0])
        if not dm:
            continue
        try:
            date_str = f"{dm.group(1)}-{dm.group(2).zfill(2)}-{dm.group(3).zfill(2)}"
            price = float(cells[1].replace(",", "").replace("円", "").strip())
            rows.append((date_str, price))
        except (ValueError, TypeError):
            continue
    return rows
