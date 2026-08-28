"""M2/M3 enrichモジュールの単体テスト。

実APIはこの開発環境のネットワークポリシーで到達できないため、`requests`を
モックして「レスポンスを正しく解釈できるか」「失敗時にseedへ安全にフォールバック
するか」を検証する。実キーでの実地検証は利用者自身が一度行うこと（README参照）。
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import enrich_commute  # noqa: E402
import enrich_geocode  # noqa: E402
import enrich_reinfolib  # noqa: E402
from models import Candidate  # noqa: E402

JST = ZoneInfo("Asia/Tokyo")


# --- enrich_geocode -------------------------------------------------------

def test_geocode_parses_gsi_response():
    fake_json = [
        {"geometry": {"coordinates": [139.6503, 35.5563]}, "properties": {}}
    ]
    resp = MagicMock()
    resp.json.return_value = fake_json
    resp.raise_for_status.return_value = None
    with patch("enrich_geocode.requests.get", return_value=resp) as mock_get:
        result = enrich_geocode.geocode("神奈川県横浜市港北区大倉山1-1-1")
    assert result == (35.5563, 139.6503)
    assert mock_get.call_args.kwargs["params"]["q"] == "神奈川県横浜市港北区大倉山1-1-1"


def test_geocode_returns_none_on_empty_result():
    resp = MagicMock()
    resp.json.return_value = []
    resp.raise_for_status.return_value = None
    with patch("enrich_geocode.requests.get", return_value=resp):
        assert enrich_geocode.geocode("存在しない住所です") is None


def test_geocode_candidates_skips_when_no_address():
    c = Candidate(name="テスト", station="大倉山", price_man=6000)
    enrich_geocode.geocode_candidates([c])
    assert c.lat is None and c.lon is None


# --- enrich_reinfolib -------------------------------------------------------

def test_lat_lon_to_tile_matches_known_value():
    # 東京駅付近、z=15での既知に近いタイル座標帯であることを確認（厳密値はWeb実装と突合）
    x, y = enrich_reinfolib.lat_lon_to_tile(35.681236, 139.767125, 15)
    assert isinstance(x, int) and isinstance(y, int)
    assert x > 0 and y > 0


def test_point_in_ring_square():
    ring = [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]
    assert enrich_reinfolib._point_in_ring(5, 5, ring) is True
    assert enrich_reinfolib._point_in_ring(50, 50, ring) is False


def test_estimate_hazard_true_when_point_inside_flood_polygon():
    geojson_features = [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[139.6, 35.5], [139.6, 35.6], [139.7, 35.6], [139.7, 35.5], [139.6, 35.5]]],
            },
        }
    ]
    with patch("enrich_reinfolib.fetch_tile_features", return_value=geojson_features), \
         patch.dict("os.environ", {"REINFOLIB_API_KEY": "dummy"}):
        assert enrich_reinfolib.estimate_hazard(35.55, 139.65) == 2


def test_estimate_hazard_false_when_no_features():
    with patch("enrich_reinfolib.fetch_tile_features", return_value=[]), \
         patch.dict("os.environ", {"REINFOLIB_API_KEY": "dummy"}):
        assert enrich_reinfolib.estimate_hazard(35.55, 139.65) == 0


def test_estimate_land_price_per_tsubo_computes_median():
    fake_records = [
        {"NearestStation": "大倉山", "Type": "宅地(土地と建物)", "TradePrice": "60000000", "Area": "100"},
        {"NearestStation": "大倉山", "Type": "宅地(土地と建物)", "TradePrice": "66000000", "Area": "100"},
        {"NearestStation": "菊名", "Type": "宅地(土地と建物)", "TradePrice": "50000000", "Area": "100"},
    ]
    with patch("enrich_reinfolib.fetch_transactions", return_value=fake_records), \
         patch.dict("os.environ", {"REINFOLIB_API_KEY": "dummy"}):
        result = enrich_reinfolib.estimate_land_price_per_tsubo("大倉山", "神奈川県", years=[2024])
    assert result is not None
    price, source = result
    # 6000万/(100*0.3025)=198.35, 6600万/(100*0.3025)=218.18 -> median
    assert 195 < price < 220
    assert "reinfolib" in source


def test_refresh_reference_land_csv_keeps_seed_when_no_new_data(tmp_path):
    csv_path = tmp_path / "reference_land.csv"
    csv_path.write_text(
        "station,land_price_man_per_tsubo,source\n大倉山,200,概算\n", encoding="utf-8"
    )
    with patch("enrich_reinfolib.estimate_land_price_per_tsubo", return_value=None), \
         patch.dict("os.environ", {"REINFOLIB_API_KEY": "dummy"}):
        status = enrich_reinfolib.refresh_reference_land_csv(["大倉山"], csv_path)
    assert status["大倉山"] == "seed"
    content = csv_path.read_text(encoding="utf-8")
    assert "200" in content


def test_refresh_reference_land_csv_updates_when_new_data(tmp_path):
    csv_path = tmp_path / "reference_land.csv"
    csv_path.write_text(
        "station,land_price_man_per_tsubo,source\n大倉山,200,概算\n", encoding="utf-8"
    )
    with patch(
        "enrich_reinfolib.estimate_land_price_per_tsubo",
        return_value=(210.5, "reinfolib XIT001 2024年 n=5"),
    ), patch.dict("os.environ", {"REINFOLIB_API_KEY": "dummy"}):
        status = enrich_reinfolib.refresh_reference_land_csv(["大倉山"], csv_path)
    assert status["大倉山"] == "updated"
    content = csv_path.read_text(encoding="utf-8")
    assert "210.5" in content


# --- enrich_commute -------------------------------------------------------

def test_next_weekday_9am_epoch_from_weekday_morning():
    # 2026-08-28(金)朝7時 -> 同日9時
    now = datetime.datetime(2026, 8, 28, 7, 0, tzinfo=JST)
    epoch = enrich_commute.next_weekday_9am_epoch(now)
    result = datetime.datetime.fromtimestamp(epoch, JST)
    assert result == datetime.datetime(2026, 8, 28, 9, 0, tzinfo=JST)


def test_next_weekday_9am_epoch_skips_weekend():
    # 2026-08-28(金)夜 -> 翌週月曜(8/31)の9時
    now = datetime.datetime(2026, 8, 28, 20, 0, tzinfo=JST)
    epoch = enrich_commute.next_weekday_9am_epoch(now)
    result = datetime.datetime.fromtimestamp(epoch, JST)
    assert result == datetime.datetime(2026, 8, 31, 9, 0, tzinfo=JST)
    assert result.weekday() == 0  # 月曜


def test_fetch_commute_minutes_parses_duration():
    fake_body = {
        "status": "OK",
        "routes": [{"legs": [{"duration": {"value": 2700}}]}],  # 45分
    }
    resp = MagicMock()
    resp.json.return_value = fake_body
    resp.raise_for_status.return_value = None
    with patch("enrich_commute.requests.get", return_value=resp), \
         patch.dict("os.environ", {"GOOGLE_MAPS_API_KEY": "dummy"}):
        minutes = enrich_commute.fetch_commute_minutes(35.55, 139.65, "横浜駅")
    assert minutes == 45.0


def test_fetch_commute_minutes_returns_none_on_no_route():
    resp = MagicMock()
    resp.json.return_value = {"status": "ZERO_RESULTS", "routes": []}
    resp.raise_for_status.return_value = None
    with patch("enrich_commute.requests.get", return_value=resp), \
         patch.dict("os.environ", {"GOOGLE_MAPS_API_KEY": "dummy"}):
        assert enrich_commute.fetch_commute_minutes(35.55, 139.65, "横浜駅") is None
