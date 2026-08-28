"""不動産情報ライブラリAPI（国交省）による相場・ハザード・用途地域の補完（M2）。

API仕様（エンドポイント名・パラメータの一次情報。実装前に必ず参照すること）:
  https://www.reinfolib.mlit.go.jp/help/apiManual/
APIキー申請:
  https://www.reinfolib.mlit.go.jp/api/request/ （審査5営業日目安）
認証: HTTPヘッダ `Ocp-Apim-Subscription-Key: <REINFOLIB_API_KEY>`（.env参照）
共通ベースURL: https://www.reinfolib.mlit.go.jp/ex-api/external/<API-ID>

このモジュールは以下を提供する:
  1. XIT001（不動産価格 取引価格・成約価格 情報取得API）で、駅の最寄り取引事例から
     成約坪単価の中央値を算出し、reference_land.csv 相当のseedを実データで上書きする。
  2. タイル系API（XKT系、GeoJSON）で、物件座標が該当レイヤのポリゴンに含まれるかを
     判定し、hazard_0_3 を自動推定する。

# 実装上の注意（重要 / 未検証事項）
この環境からは reinfolib.mlit.go.jp への実アクセスがネットワークポリシーで
ブロックされており、実レスポンスで検証できていない。以下は公開ドキュメント・
実装記事の断片的な情報から実装した「best effort」であり、**実キーを入手した
利用者が最初に1回、`tests/manual_reinfolib_smoke.py`（TODO）等で実レスポンスを
確認し、フィールド名・レイヤIDのずれがあれば補正すること**:
  - XIT001 のレスポンススキーマ（`data` 配下の各取引レコードのキー名）は
    国交省の他統計API（不動産取引価格情報など）で広く使われている命名
    （TradePrice, Area, NearestStation, Type 等）を踏襲していると推定。
  - ハザード（洪水浸水想定区域）のタイルAPI IDは `XKT026`、用途地域は `XKT002`
    と、複数の実装解説記事で一致していたためこれを採用。土砂災害警戒区域の
    タイルIDは未確認のため TODO とし、洪水のみ自動判定する。
  - タイルのポリゴン内に含まれるかの判定は、`properties` 内の浸水ランク等の
    詳細フィールドを使わず「該当ポリゴンに1つでも交差すればハザードあり」という
    粗い二値判定にとどめている（hazard_0_3は交差なし=0 / 交差あり=2固定）。
    ランク別の重み付け（0-3の段階分け）は実レスポンスを見てから精緻化する。
"""
from __future__ import annotations

import logging
import math
import os
import statistics
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/"

# JIS X0401 都道府県コード（このツールが対象とする東京・神奈川のみ）
PREF_CODE = {"東京都": "13", "神奈川県": "14"}

TILE_ZOOM = 15          # 洪水浸水タイルの推奨ズームレベル（実装記事より。~1-2km四方/タイル）
FLOOD_API_ID = "XKT026"  # 洪水浸水想定区域（想定最大規模）
ZONING_API_ID = "XKT002"  # 用途地域
# TODO: 土砂災害警戒区域のタイルIDが確認でき次第、LANDSLIDE_API_ID を追加する。

SQM_TO_TSUBO = 0.3025


def _headers() -> dict:
    key = os.environ.get("REINFOLIB_API_KEY")
    if not key:
        raise RuntimeError(
            "REINFOLIB_API_KEY が未設定です。.env に設定するか、"
            "このenrichステージをスキップしてください（run.py --no-reinfolib）。"
        )
    return {"Ocp-Apim-Subscription-Key": key}


# ---------------------------------------------------------------------------
# XIT001: 取引価格から相場坪単価を推定
# ---------------------------------------------------------------------------

def fetch_transactions(area_pref: str, city_code: Optional[str] = None,
                        year: Optional[int] = None, quarter: Optional[int] = None,
                        timeout: float = 15.0) -> list[dict]:
    """XIT001 で指定都道府県（・市区町村）の取引価格情報を取得する。

    area_pref: "東京都" / "神奈川県"
    city_code: 市区町村コード（任意。指定すると絞り込める）
    year/quarter: 取引時期（省略時は直近4四半期分を年をずらして数回叩く想定だが、
                  M2では呼び出し側が年を指定するシンプルな実装にとどめる）
    """
    params = {"area": PREF_CODE[area_pref]}
    if city_code:
        params["city"] = city_code
    if year:
        params["year"] = str(year)
    if quarter:
        params["quarter"] = str(quarter)

    resp = requests.get(BASE_URL + "XIT001", params=params, headers=_headers(), timeout=timeout)
    resp.raise_for_status()
    body = resp.json()
    # ドキュメント上、実データは "data" キー配下に配列で入る想定。
    return body.get("data", body if isinstance(body, list) else [])


def estimate_land_price_per_tsubo(
    station: str, area_pref: str, city_code: Optional[str] = None,
    years: Optional[list[int]] = None,
) -> Optional[tuple[float, str]]:
    """指定駅が最寄りの取引事例から、坪単価（万円/坪）の中央値を推定する。

    戻り値: (坪単価, 出典文字列) / 事例が無ければ None。
    """
    import datetime

    years = years or [datetime.date.today().year - 1, datetime.date.today().year - 2]

    tsubo_prices: list[float] = []
    used_years: list[int] = []
    for year in years:
        try:
            records = fetch_transactions(area_pref, city_code=city_code, year=year)
        except requests.RequestException as e:
            logger.warning("XIT001取得失敗（%s, %s年）: %s", station, year, e)
            continue

        for rec in records:
            if rec.get("NearestStation") != station:
                continue
            if "土地" not in (rec.get("Type") or ""):
                continue
            try:
                trade_price_man = float(rec["TradePrice"]) / 10000  # 円→万円想定。
                area_sqm = float(rec["Area"])
            except (KeyError, TypeError, ValueError):
                continue
            if area_sqm <= 0:
                continue
            tsubo_price = trade_price_man / (area_sqm * SQM_TO_TSUBO)
            tsubo_prices.append(tsubo_price)
        if records:
            used_years.append(year)

    if not tsubo_prices:
        return None

    median_price = statistics.median(tsubo_prices)
    source = f"reinfolib XIT001 {','.join(str(y) for y in used_years)}年 n={len(tsubo_prices)}"
    return round(median_price, 1), source


# ---------------------------------------------------------------------------
# タイルAPI: ハザード・用途地域（座標ベース）
# ---------------------------------------------------------------------------

def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """標準のslippy-map式で緯度経度をタイル座標(x,y)に変換する。"""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def _point_in_ring(lat: float, lon: float, ring: list[list[float]]) -> bool:
    """レイキャスト法による点-多角形包含判定（穴なしの単純多角形を想定）。"""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
        ):
            inside = not inside
        j = i
    return inside


def _point_in_geojson_polygons(lat: float, lon: float, features: list[dict]) -> bool:
    for feat in features:
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue
        if gtype == "Polygon":
            polygons = [coords]
        elif gtype == "MultiPolygon":
            polygons = coords
        else:
            continue
        for poly in polygons:
            if not poly:
                continue
            outer_ring = poly[0]
            if _point_in_ring(lat, lon, outer_ring):
                return True
    return False


def fetch_tile_features(api_id: str, lat: float, lon: float, zoom: int = TILE_ZOOM,
                         timeout: float = 15.0) -> list[dict]:
    x, y = lat_lon_to_tile(lat, lon, zoom)
    params = {"response_format": "geojson", "z": zoom, "x": x, "y": y}
    resp = requests.get(BASE_URL + api_id, params=params, headers=_headers(), timeout=timeout)
    resp.raise_for_status()
    body = resp.json()
    return body.get("features", [])


def estimate_hazard(lat: float, lon: float) -> int:
    """洪水浸水想定区域タイルに座標が含まれれば2、含まれなければ0を返す（粗い二値判定）。

    TODO: properties内のランク（想定浸水深カテゴリ）を見て0-3の段階分けに精緻化する。
    """
    try:
        features = fetch_tile_features(FLOOD_API_ID, lat, lon)
    except requests.RequestException as e:
        logger.warning("洪水タイル取得失敗（lat=%s, lon=%s）: %s", lat, lon, e)
        return 0
    return 2 if _point_in_geojson_polygons(lat, lon, features) else 0


def estimate_zoning(lat, lon) -> Optional[str]:
    """用途地域タイルから該当地の用途地域名を返す（1件目採用。境界上は不定）。"""
    try:
        features = fetch_tile_features(ZONING_API_ID, lat, lon)
    except requests.RequestException as e:
        logger.warning("用途地域タイル取得失敗（lat=%s, lon=%s）: %s", lat, lon, e)
        return None
    for feat in features:
        geom = feat.get("geometry") or {}
        polygons = (
            [geom["coordinates"]] if geom.get("type") == "Polygon"
            else geom.get("coordinates", []) if geom.get("type") == "MultiPolygon"
            else []
        )
        for poly in polygons:
            if poly and _point_in_ring(lat, lon, poly[0]):
                props = feat.get("properties", {})
                # プロパティのキー名は実レスポンス未検証。候補キーを順に試す。
                for key in ("YoutoName", "用途地域", "name", "type"):
                    if key in props:
                        return props[key]
    return None


def enrich_hazard_and_zoning(candidates) -> None:
    """Candidate のリストを in-place で更新し、hazard_0_3 / zoning を自動補完する。

    座標(lat/lon)が無い候補は enrich_geocode.geocode_candidates を先に実行しておくこと。
    手動入力で既にhazard_0_3が0以外に設定されている候補は上書きしない（利用者の
    現地確認や重説情報の方が信頼できるため）。zoningも同様に既存値を優先する。
    """
    for c in candidates:
        if c.lat is None or c.lon is None:
            continue
        if c.hazard_0_3 == 0:
            try:
                c.hazard_0_3 = estimate_hazard(c.lat, c.lon)
            except RuntimeError:
                logger.warning("REINFOLIB_API_KEY未設定のためハザード自動判定をスキップ")
                return
        if not c.zoning:
            zoning = estimate_zoning(c.lat, c.lon)
            if zoning:
                c.zoning = zoning


def refresh_reference_land_csv(
    stations: list[str],
    csv_path,
    area_pref_of=None,
) -> dict[str, str]:
    """指定駅について XIT001 から坪単価を推定し、reference_land.csv を上書き更新する。

    取得できた駅だけ実データで置き換え、取得できなかった駅は既存のseed行を残す
    （§5-1「実データで上書き/更新」に対応）。

    area_pref_of: station -> "東京都"/"神奈川県"。省略時は東京23区/横浜・川崎の
                   よくある駅を簡易辞書で判定し、それ以外は神奈川県扱いにする（TODO:
                   駅マスタAPIが特定でき次第、正確な都道府県判定に置き換える）。
    戻り値: {station: "updated" | "seed" | "not_found"}
    """
    import csv as csv_module

    csv_path = Path(csv_path)
    existing: dict[str, dict] = {}
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as f:
            for row in csv_module.DictReader(f):
                existing[row["station"]] = row

    # 簡易判定（config/reference_commute.csvの駅一覧が前提。TODO: 駅マスタAPIで精緻化）。
    # 日吉/元住吉/武蔵小杉/新丸子/大倉山/菊名/綱島/新川崎/鹿島田は神奈川県（川崎・横浜）。
    tokyo_stations = {"西馬込", "馬込", "大森", "西大井", "品川"}
    if area_pref_of is None:
        area_pref_of = lambda st: "東京都" if st in tokyo_stations else "神奈川県"  # noqa: E731

    status: dict[str, str] = {}
    for station in stations:
        try:
            result = estimate_land_price_per_tsubo(station, area_pref_of(station))
        except RuntimeError:
            logger.warning("REINFOLIB_API_KEY未設定のため相場更新をスキップ")
            return {s: "seed" for s in stations}
        if result:
            price, source = result
            existing[station] = {
                "station": station,
                "land_price_man_per_tsubo": str(price),
                "source": source,
            }
            status[station] = "updated"
        elif station in existing:
            status[station] = "seed"
        else:
            status[station] = "not_found"

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        # lineterminatorを明示しないとcsvモジュールが既定で\r\nを書き、
        # 既存ファイル(\n)と比べて実質差分の無いgit diffを毎回発生させてしまう。
        writer = csv_module.DictWriter(
            f, fieldnames=["station", "land_price_man_per_tsubo", "source"], lineterminator="\n"
        )
        writer.writeheader()
        for row in existing.values():
            writer.writerow(row)

    return status
