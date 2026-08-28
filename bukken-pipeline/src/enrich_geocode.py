"""国土地理院 住所→緯度経度ジオコーディング（M2）。

エンドポイント: GET https://msearch.gsi.go.jp/address-search/AddressSearch?q=<住所>
キー不要。GeoJSON FeatureCollectionが返り、features[0].geometry.coordinates が
[経度, 緯度] の順で入っている（GeoJSON標準の lon, lat 順なので注意）。

Candidate.address を入力に Candidate.lat / lon を埋める。失敗時（該当なし・
通信エラー）は None を返し、呼び出し側（run.py）で候補をスキップさせず、
そのまま座標なしで処理を続行させる（reinfolibのタイル判定など座標が必須の
enrichだけがスキップされる）。
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

GSI_ENDPOINT = "https://msearch.gsi.go.jp/address-search/AddressSearch"


def geocode(address: str, timeout: float = 10.0) -> Optional[tuple[float, float]]:
    """住所文字列から (緯度, 経度) を返す。取得できなければ None。"""
    if not address or not address.strip():
        return None
    try:
        resp = requests.get(GSI_ENDPOINT, params={"q": address}, timeout=timeout)
        resp.raise_for_status()
        features = resp.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning("GSIジオコーディング失敗（住所=%s）: %s", address, e)
        return None

    if not features:
        logger.warning("GSIジオコーディングで該当なし（住所=%s）", address)
        return None

    try:
        lon, lat = features[0]["geometry"]["coordinates"][:2]
        return float(lat), float(lon)
    except (KeyError, IndexError, TypeError, ValueError) as e:
        logger.warning("GSIレスポンスの形式が想定と違います（住所=%s）: %s", address, e)
        return None


def geocode_candidates(candidates, timeout: float = 10.0) -> None:
    """Candidate のリストを in-place で更新し、lat/lon を埋める（address必須）。"""
    for c in candidates:
        if c.lat is not None and c.lon is not None:
            continue
        if not c.address:
            continue
        result = geocode(c.address, timeout=timeout)
        if result is not None:
            c.lat, c.lon = result
