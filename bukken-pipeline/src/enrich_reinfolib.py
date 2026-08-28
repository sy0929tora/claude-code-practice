"""[M2 未実装] 不動産情報ライブラリAPI（国交省）による相場・ハザード・用途地域の補完。

API仕様（エンドポイント名・パラメータ・タイル仕様は必ずここを参照すること）:
  https://www.reinfolib.mlit.go.jp/help/apiManual/
APIキー申請:
  https://www.reinfolib.mlit.go.jp/api/request/ （審査5営業日目安）
認証: HTTPヘッダ Ocp-Apim-Subscription-Key: <REINFOLIB_API_KEY>（.env参照）

使用予定エンドポイント:
  - XIT001 不動産価格（取引価格・成約価格）取得
    → 駅/地域周辺の成約坪単価を算出し、config/reference_land.csv を実データで上書き。
  - 用途地域・ハザード（洪水浸水想定/土砂災害等）タイル（GeoJSON/PBF、z/x/y指定）
    → enrich_geocode.py で得た緯度経度をタイル座標（標準のslippy-map式）に変換し、
      物件座標が該当レイヤに含まれるか判定して hazard_0_3 を自動推定する。

TODO(M2):
  - fetch_transaction_prices(station: str) -> list[dict]  (XIT001)
  - lat_lon_to_tile(lat, lon, zoom) -> (x, y)              (slippy-map式)
  - fetch_hazard_flags(lat, lon) -> int                     (0-3)
  - fetch_zoning(lat, lon) -> str | None
  - 失敗時は config/reference_land.csv の seed にフォールバックし、
    パイプライン全体を止めないこと（score.py の ScoringContext がこの契約に依存）。
"""
from __future__ import annotations
