"""[M2 未実装] 国土地理院 住所→緯度経度ジオコーディング。

エンドポイント: GET https://msearch.gsi.go.jp/address-search/AddressSearch?q=<住所>
キー不要。GeoJSON形式で候補が返る（先頭要素の geometry.coordinates を採用する想定）。
Candidate.address を入力に Candidate.lat / lon を埋める関数を実装する。

TODO(M2): geocode(address) を実装し、reinfolibのタイル問い合わせ
          (enrich_reinfolib.py) の前段として使う。
"""
from __future__ import annotations

from typing import Optional


def geocode(address: str) -> Optional[tuple[float, float]]:
    """住所から (緯度, 経度) を返す。未実装。"""
    raise NotImplementedError("enrich_geocode.geocode は M2 で実装予定です。")
