"""Google Maps Directions API による通勤時間の実測（M3）。

エンドポイント: GET https://maps.googleapis.com/maps/api/directions/json
  params: mode=transit, arrival_time=<次の平日09:00のepoch秒(JST)>,
          origin=<物件座標>, destination="横浜駅" / "高田馬場駅", key=<GOOGLE_MAPS_API_KEY>

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
from typing import Optional
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)

DIRECTIONS_ENDPOINT = "https://maps.googleapis.com/maps/api/directions/json"
JST = ZoneInfo("Asia/Tokyo")

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


def _api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise RuntimeError(
            "GOOGLE_MAPS_API_KEY が未設定です。.env に設定するか、"
            "このenrichステージをスキップしてください（run.py --no-commute）。"
        )
    return key


def fetch_commute_minutes(
    lat: float, lon: float, destination: str, arrival_time: Optional[int] = None,
    timeout: float = 15.0,
) -> Optional[float]:
    """物件座標から destination までの平日09:00着 電車通勤の所要分を返す。取得不可ならNone。"""
    arrival_time = arrival_time or next_weekday_9am_epoch()
    params = {
        "origin": f"{lat},{lon}",
        "destination": destination,
        "mode": "transit",
        "arrival_time": arrival_time,
        "key": _api_key(),
        "language": "ja",
        "region": "jp",
    }
    try:
        resp = requests.get(DIRECTIONS_ENDPOINT, params=params, timeout=timeout)
        resp.raise_for_status()
        body = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning("Directions API通信失敗（dest=%s）: %s", destination, e)
        return None

    if body.get("status") != "OK" or not body.get("routes"):
        logger.warning(
            "Directions APIが経路を返しませんでした（dest=%s, status=%s）",
            destination, body.get("status"),
        )
        return None

    leg = body["routes"][0]["legs"][0]
    duration_sec = leg["duration"]["value"]
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
            c.commute_source = "google_directions"
