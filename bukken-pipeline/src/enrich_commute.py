"""Google Maps Routes API による通勤時間の実測（M3）。

エンドポイント: POST https://routes.googleapis.com/directions/v2:computeRoutes
  headers: X-Goog-Api-Key: <GOOGLE_MAPS_API_KEY>, X-Goog-FieldMask: routes.duration
  body(JSON): origin.location.latLng, destination.address, travelMode="TRANSIT",
              arrivalTime=<次の平日09:00 JSTのRFC3339(UTC)文字列>

# 注意（重要）: 旧Directions API（GET .../maps/api/directions/json）は使っていない
2025年3月1日以降に作成したGoogle Cloudプロジェクトでは、旧来の Directions API
（レガシー）を新規に有効化できなくなっている（Googleが後継の Routes API に統合済み）。
そのためこのモジュールは最初から Routes API (`computeRoutes`) で実装している。
料金: Compute Routes - Essentials は月10,000コール無料（本ツールの呼び出し量なら
実運用でも無料枠に収まる想定）。有効化にはGoogle Cloud側で課金アカウント
（クレジットカード）の登録が必要（詳細はREADME参照）。

物件ごとに横浜・高田馬場の2本を叩き、所要分を
Candidate.commute_yokohama_min / commute_takadanobaba_min に格納する。
config/reference_commute.csv はseedとして残し、取得成功時のみ実測で上書きする
（score.py の ScoringContext は Candidate 側が None のときだけ seed を見る設計）。

代替候補（有料）: 駅すぱあと / NAVITIME。まずはGoogleで実装。
"""
from __future__ import annotations

import datetime
import logging
import os
import re
from typing import Optional
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)

COMPUTE_ROUTES_ENDPOINT = "https://routes.googleapis.com/directions/v2:computeRoutes"
JST = ZoneInfo("Asia/Tokyo")
DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?)s$")

# 目的駅は固定2拠点（§3）。曖昧さ回避のため都道府県名を付与している。
DESTINATIONS = {
    "yokohama": "横浜駅, 神奈川県横浜市",
    "takadanobaba": "高田馬場駅, 東京都新宿区",
}


def next_weekday_9am_epoch(now: Optional[datetime.datetime] = None) -> int:
    """次の平日（今日が平日で9:00より前ならその日）09:00 JSTのUnix epoch秒を返す。"""
    now = now.astimezone(JST) if now else datetime.datetime.now(JST)
    candidate = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += datetime.timedelta(days=1)
    while candidate.weekday() >= 5:  # 5=土, 6=日
        candidate += datetime.timedelta(days=1)
    return int(candidate.timestamp())


def _rfc3339_utc(epoch: int) -> str:
    """Routes APIが要求するRFC3339(UTC, "Z"終端)形式に変換する。"""
    dt = datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise RuntimeError(
            "GOOGLE_MAPS_API_KEY が未設定です。.env に設定するか、"
            "このenrichステージをスキップしてください（run.pyで--commuteを付けない）。"
        )
    return key


def _parse_duration_seconds(duration_str: str) -> Optional[float]:
    """Routes APIのduration表現（例: "2700s"）を秒数に変換する。"""
    m = DURATION_RE.match(duration_str or "")
    return float(m.group(1)) if m else None


def fetch_commute_minutes(
    lat: float, lon: float, destination: str, arrival_time: Optional[int] = None,
    timeout: float = 15.0,
) -> Optional[float]:
    """物件座標から destination までの平日09:00着 電車通勤の所要分を返す。取得不可ならNone。"""
    arrival_time = arrival_time or next_weekday_9am_epoch()
    body = {
        "origin": {"location": {"latLng": {"latitude": lat, "longitude": lon}}},
        "destination": {"address": destination},
        "travelMode": "TRANSIT",
        "arrivalTime": _rfc3339_utc(arrival_time),
        "languageCode": "ja",
        "regionCode": "JP",
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": _api_key(),
        "X-Goog-FieldMask": "routes.duration",
    }
    try:
        resp = requests.post(COMPUTE_ROUTES_ENDPOINT, json=body, headers=headers, timeout=timeout)
        resp.raise_for_status()
        response_body = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning("Routes API通信失敗（dest=%s）: %s", destination, e)
        return None

    routes = response_body.get("routes")
    if not routes:
        logger.warning("Routes APIが経路を返しませんでした（dest=%s）: %s", destination, response_body)
        return None

    duration_sec = _parse_duration_seconds(routes[0].get("duration"))
    if duration_sec is None:
        logger.warning("Routes APIのduration形式が想定外です（dest=%s）: %r", destination, routes[0].get("duration"))
        return None
    return round(duration_sec / 60.0, 1)


def enrich_commute(candidates) -> None:
    """Candidate のリストを in-place で更新し、横浜・高田馬場の実測通勤分を埋める。

    座標(lat/lon)が無い候補はスキップ（score.py 側で reference_commute.csv の
    seedにフォールバックする）。
    """
    arrival_time = next_weekday_9am_epoch()
    for c in candidates:
        if c.lat is None or c.lon is None:
            continue
        try:
            yoko = fetch_commute_minutes(c.lat, c.lon, DESTINATIONS["yokohama"], arrival_time)
            taka = fetch_commute_minutes(c.lat, c.lon, DESTINATIONS["takadanobaba"], arrival_time)
        except RuntimeError:
            logger.warning("GOOGLE_MAPS_API_KEY未設定のため通勤実測をスキップ")
            return
        if yoko is not None:
            c.commute_yokohama_min = yoko
        if taka is not None:
            c.commute_takadanobaba_min = taka
        if yoko is not None or taka is not None:
            c.commute_source = "google_routes"
