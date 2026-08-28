"""高得点の新着物件を通知する（M5・任意機能）。

前回実行時の output.xlsx と今回の採点結果を比較し、新規に出現した候補のうち
総合スコアが閾値以上のものを Gmail 経由でメール通知する。

# LINE Notifyについて
依頼書ではLINE通知も選択肢に挙がっていたが、LINE Notifyは2025年3月31日に
サービス終了済み（LINE社発表）。後継はLINE公式アカウントのMessaging APIだが、
公式アカウント作成・チャネルアクセストークン発行など追加のセットアップが要るため、
本ツールでは実装しない。当面はメール通知のみとする（TODO: 希望があれば
Messaging APIでの通知を別途実装）。
"""
from __future__ import annotations

import base64
import logging
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import pandas as pd

from models import ScoredCandidate

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 75.0


def _dedupe_key(name: str, price_man: float) -> str:
    """物件名+価格から比較キーを作る。xlsx往復でint/floatの型がぶれても一致するよう丸める。"""
    return f"{name}::{round(float(price_man))}"


def load_previous_scores(prev_output_path: Path) -> dict[str, float]:
    """前回output.xlsxの {住所+価格キー: 総合スコア} を返す（無ければ空辞書）。"""
    prev_output_path = Path(prev_output_path)
    if not prev_output_path.exists():
        return {}
    try:
        df = pd.read_excel(prev_output_path)
    except Exception as e:  # 破損ファイル等
        logger.warning("前回のoutput読み込みに失敗: %s", e)
        return {}
    if "物件名" not in df.columns or "価格(万円)" not in df.columns:
        return {}
    return {
        _dedupe_key(row["物件名"], row["価格(万円)"]): row.get("総合", None)
        for _, row in df.iterrows()
    }


def find_new_high_scorers(
    scored: list[ScoredCandidate],
    previous_scores: dict[str, float],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[ScoredCandidate]:
    """前回未出現 かつ 総合スコアが閾値以上の候補を返す。"""
    result = []
    for s in scored:
        key = _dedupe_key(s.name, s.price_man)
        if key in previous_scores:
            continue
        if s.total_score >= threshold:
            result.append(s)
    return result


def _format_email_body(candidates: list[ScoredCandidate]) -> str:
    lines = ["新規の高得点物件が見つかりました。\n"]
    for s in candidates:
        lines.append(
            f"■ {s.name}（総合{s.total_score}点・{s.rank}位）\n"
            f"  価格: {s.price_man}万円 / {s.station}駅 徒歩{s.walk_min}分\n"
            f"  掲載URL: {s.source_url or '(なし)'}\n"
        )
    return "\n".join(lines)


def notify_email(candidates: list[ScoredCandidate], to_addr: Optional[str] = None) -> bool:
    """Gmail API（gmail.send スコープ）で通知メールを送る。送れたらTrue。"""
    to_addr = to_addr or os.environ.get("NOTIFY_EMAIL_TO")
    if not to_addr:
        logger.info("NOTIFY_EMAIL_TO 未設定のためメール通知をスキップします。")
        return False
    if not candidates:
        return False

    from googleapiclient.discovery import build

    from google_auth import get_credentials

    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(_format_email_body(candidates))
    message["to"] = to_addr
    message["subject"] = f"【bukken-pipeline】新規の高得点物件 {len(candidates)}件"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return True


def notify_new_high_scorers(
    scored: list[ScoredCandidate],
    prev_output_path: Path,
    threshold: Optional[float] = None,
) -> list[ScoredCandidate]:
    """前回出力と比較して新規高得点候補を検出し、あれば通知する。検出した候補を返す。"""
    threshold = threshold if threshold is not None else float(
        os.environ.get("NOTIFY_SCORE_THRESHOLD", DEFAULT_THRESHOLD)
    )
    previous = load_previous_scores(prev_output_path)
    new_high = find_new_high_scorers(scored, previous, threshold)
    if new_high:
        try:
            notify_email(new_high)
        except Exception as e:
            logger.warning("メール通知に失敗しました: %s", e)
    return new_high
