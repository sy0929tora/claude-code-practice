"""Gmail API から保存検索メールを取得し candidates 化する（M4）。

絶対制約: ポータルのWebページはスクレイピングしない。ここで読むのは
利用者本人の受信箱に届いたメールのみ（Gmail APIでOAuth認可の上、自分の
メールを読む）。ポータル側のメール配信機能を正規に使っているだけであり、
Webページへのアクセスは一切行わない。

- ラベル（.env の GMAIL_LABEL、既定"bukken"）の新着メールを取得
- 本文HTMLから物件サマリ（価格/所在地/駅/徒歩/築年/面積/URL）を抽出
- ポータルごとに書式が違うため、ポータル別パーサを用意（SUUMO・東急リバブルの2種）

# 未検証事項（重要）
実際の保存検索通知メールのサンプルをこの環境では入手できていないため、
`parse_suumo` / `parse_livable` は各社が公開している一般的なメールテンプレートの
構造（物件名・価格・所在地・徒歩分・専有/建物面積・築年をラベル付きで列挙し、
物件ごとに詳細ページへのリンクが続く）を仮定した正規表現ベースの実装であり、
**実際のメールで一度動作確認し、抽出漏れがあればパターンを調整すること**。
抽出できなかったフィールドは None のまま candidates.csv 相当に落ちるので、
手動補完すれば良い（§5-4の設計通り）。
"""
from __future__ import annotations

import base64
import logging
import os
import re
from typing import Optional

from bs4 import BeautifulSoup

from models import Candidate

logger = logging.getLogger(__name__)

PRICE_RE = re.compile(r"([0-9,]+)\s*万円")
WALK_RE = re.compile(r"歩\s*([0-9]+)\s*分")
LAYOUT_RE = re.compile(r"([1-9][SLDK]{1,4})")
BUILT_YEAR_RE = re.compile(r"(19|20)\d{2}年")
LAND_SQM_RE = re.compile(r"土地[^0-9]{0,4}([0-9]+(?:\.[0-9]+)?)\s*m")
BLDG_SQM_RE = re.compile(r"(?:建物|専有)[^0-9]{0,4}([0-9]+(?:\.[0-9]+)?)\s*m")
# 「路線名「駅名」駅」のようにカギ括弧で駅名が明示される書式を優先し、
# 無ければ「XX駅」の直前の空白区切りトークンをそのまま駅名とみなす。
STATION_RE_BRACKETED = re.compile(r"「([^「」\s]+)」駅")
STATION_RE_PLAIN = re.compile(r"(?:^|[\s、])([^\s、「」]{1,10})駅")
URL_RE = re.compile(r"https?://\S+")


def get_gmail_service():
    """Gmail APIサービスオブジェクトを返す（初回はブラウザOAuth認可）。"""
    from googleapiclient.discovery import build

    from google_auth import get_credentials

    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def _resolve_label_id(service, label_name: str) -> Optional[str]:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"] == label_name:
            return label["id"]
    return None


def list_label_messages(service, label_name: Optional[str] = None) -> list[dict]:
    """指定ラベル（省略時は.envのGMAIL_LABEL、既定"bukken"）の新着メールを取得する。"""
    label_name = label_name or os.environ.get("GMAIL_LABEL", "bukken")
    label_id = _resolve_label_id(service, label_name)
    if label_id is None:
        logger.warning(
            "ラベル '%s' が見つかりません。Gmail側でラベルを作成し、"
            "保存検索メールにフィルタで自動付与してください。", label_name,
        )
        return []

    messages = []
    page_token = None
    while True:
        resp = (
            service.users()
            .messages()
            .list(userId="me", labelIds=[label_id], pageToken=page_token)
            .execute()
        )
        messages.extend(resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    full_messages = []
    for m in messages:
        full = service.users().messages().get(userId="me", id=m["id"], format="full").execute()
        full_messages.append(full)
    return full_messages


def _extract_html_body(message: dict) -> str:
    """Gmail APIのmessageペイロードからHTML本文を取り出す（base64url decode込み）。"""

    def walk(part) -> Optional[str]:
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode(
                "utf-8", errors="replace"
            )
        for sub in part.get("parts", []) or []:
            found = walk(sub)
            if found:
                return found
        return None

    payload = message.get("payload", {})
    return walk(payload) or ""


def _detect_portal(message: dict) -> str:
    headers = {h["name"].lower(): h["value"] for h in message.get("payload", {}).get("headers", [])}
    sender = headers.get("from", "")
    if "suumo" in sender.lower():
        return "suumo"
    if "livable" in sender.lower() or "東急リバブル" in sender:
        return "livable"
    return "unknown"


def _parse_common(text_block: str) -> dict:
    """ポータル共通の緩いパターンでフィールドを拾う（ポータル別パーサの土台）。"""
    price_m = PRICE_RE.search(text_block)
    walk_m = WALK_RE.search(text_block)
    layout_m = LAYOUT_RE.search(text_block)
    built_m = BUILT_YEAR_RE.search(text_block)
    land_m = LAND_SQM_RE.search(text_block)
    bldg_m = BLDG_SQM_RE.search(text_block)
    station_m = STATION_RE_BRACKETED.search(text_block) or STATION_RE_PLAIN.search(text_block)
    url_m = URL_RE.search(text_block)

    return {
        "price_man": float(price_m.group(1).replace(",", "")) if price_m else None,
        "walk_min": float(walk_m.group(1)) if walk_m else None,
        "layout": layout_m.group(1) if layout_m else None,
        "built_year": int(built_m.group(0)[:4]) if built_m else None,
        "land_sqm": float(land_m.group(1)) if land_m else None,
        "bldg_sqm": float(bldg_m.group(1)) if bldg_m else None,
        "station": station_m.group(1) if station_m else None,
        "source_url": url_m.group(0) if url_m else None,
    }


def parse_suumo(html: str) -> list[dict]:
    """SUUMOの保存検索通知メールから物件情報のリストを抽出する。

    実装方針: 1通のメールに複数物件が並ぶ想定で、物件名らしき見出し（<a>や<td>の
    テキスト）をブロック区切りとして、そのブロック内テキストを共通パーサに渡す。
    """
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.find_all(["tr", "div", "li"])
    results = []
    seen_text = set()
    for block in blocks:
        text = block.get_text(separator=" ", strip=True)
        if not text or text in seen_text:
            continue
        if "万円" not in text:
            continue
        seen_text.add(text)
        fields = _parse_common(text)
        if fields["price_man"] is None:
            continue
        # get_text()はhref属性を落とすので、リンクURLはタグから別途拾う。
        link = block.find("a", href=True)
        if link is not None:
            fields["source_url"] = link["href"]
        name_m = re.search(r"^([^\s]{3,30}?)(?:\s|$)", text)
        fields["name"] = name_m.group(1) if name_m else text[:30]
        fields["intake_source"] = "gmail:suumo"
        results.append(fields)
    return results


def parse_livable(html: str) -> list[dict]:
    """東急リバブルの保存検索通知メールから物件情報のリストを抽出する。

    書式がSUUMOと近い（一覧型テーブル）想定のため、当面は共通ロジックを再利用し、
    intake_sourceのみ変える。差分が判明したら専用パターンに分岐させる。
    """
    results = parse_suumo(html)
    for r in results:
        r["intake_source"] = "gmail:livable"
    return results


PARSERS = {
    "suumo": parse_suumo,
    "livable": parse_livable,
}


def messages_to_candidates(messages: list[dict]) -> list[Candidate]:
    candidates = []
    for msg in messages:
        portal = _detect_portal(msg)
        parser = PARSERS.get(portal)
        if parser is None:
            logger.warning(
                "未対応の送信元のためスキップしました（message id=%s）。"
                "対応ポータルを増やす場合は intake_gmail.py にパーサを追加してください。",
                msg.get("id"),
            )
            continue
        html = _extract_html_body(msg)
        if not html:
            continue
        for fields in parser(html):
            if not fields.get("name") or fields.get("price_man") is None:
                continue
            fields.setdefault("station", "")
            try:
                candidates.append(Candidate(**fields))
            except Exception as e:  # pydanticのバリデーションエラー等
                logger.warning("メールからの候補生成に失敗（id=%s）: %s", msg.get("id"), e)
    return candidates


def fetch_candidates_from_gmail(label_name: Optional[str] = None) -> list[Candidate]:
    service = get_gmail_service()
    messages = list_label_messages(service, label_name)
    return messages_to_candidates(messages)
