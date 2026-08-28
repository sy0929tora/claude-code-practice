"""[M3 未実装] Google Maps Directions API による通勤時間の実測。

エンドポイント: GET https://maps.googleapis.com/maps/api/directions/json
  params: mode=transit, arrival_time=<次の平日09:00のepoch秒>,
          origin=<物件座標>, destination="横浜駅" / "高田馬場駅"
          key=<GOOGLE_MAPS_API_KEY>（.env参照）

物件ごとに横浜・高田馬場の2本を叩き、所要分を
Candidate.commute_yokohama_min / commute_takadanobaba_min に格納する。
config/reference_commute.csv はseedとして残し、取得成功時のみ実測で上書きする
（score.py の ScoringContext は Candidate 側が None のときだけ seed を見る設計）。

代替候補（有料）: 駅すぱあと / NAVITIME。まずはGoogleで実装する。

TODO(M3):
  - next_weekday_9am_epoch() -> int
  - fetch_commute_minutes(lat, lon, destination: str) -> int | None
  - 失敗時（レート制限・経路なし等）は None を返し、score.py 側のseedフォールバックに委ねる。
"""
from __future__ import annotations
