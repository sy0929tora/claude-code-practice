"""intake_gmail.py の正規表現/HTML抽出ロジックの単体テスト（M4）。

実際の通知メールHTMLは未入手のため、想定書式を模したサンプルHTMLで
「共通パターンで拾えるか」だけを検証する。実メールでの抽出精度は
README/モジュールdocstring記載の通りTODO（要調整）。
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import intake_gmail  # noqa: E402

SAMPLE_HTML = """
<html><body>
<table>
<tr><td>
  横浜市港北区大倉山1丁目 新築一戸建て 6,480万円 東急東横線「大倉山」駅 歩6分
  土地面積101.31m2 建物面積80.52m2 3LDK 2026年築
  <a href="https://suumo.jp/example/12345/">詳細を見る</a>
</td></tr>
</table>
</body></html>
"""


def _fake_message(html: str, sender: str) -> dict:
    data = base64.urlsafe_b64encode(html.encode("utf-8")).decode("utf-8").rstrip("=")
    return {
        "id": "msg1",
        "payload": {
            "headers": [{"name": "From", "value": sender}],
            "mimeType": "text/html",
            "body": {"data": data},
        },
    }


def test_parse_suumo_extracts_core_fields():
    results = intake_gmail.parse_suumo(SAMPLE_HTML)
    assert len(results) >= 1
    r = results[0]
    assert r["price_man"] == 6480.0
    assert r["walk_min"] == 6.0
    assert r["station"] == "大倉山"
    assert r["layout"] == "3LDK"
    assert r["built_year"] == 2026
    assert r["land_sqm"] == 101.31
    assert r["bldg_sqm"] == 80.52
    assert "suumo.jp" in r["source_url"]


def test_detect_portal_from_sender():
    msg = _fake_message(SAMPLE_HTML, "SUUMO <no-reply@suumo.jp>")
    assert intake_gmail._detect_portal(msg) == "suumo"

    msg2 = _fake_message(SAMPLE_HTML, "東急リバブル <no-reply@livable.co.jp>")
    assert intake_gmail._detect_portal(msg2) == "livable"

    msg3 = _fake_message(SAMPLE_HTML, "unknown@example.com")
    assert intake_gmail._detect_portal(msg3) == "unknown"


def test_extract_html_body_decodes_base64url():
    msg = _fake_message(SAMPLE_HTML, "SUUMO <no-reply@suumo.jp>")
    html = intake_gmail._extract_html_body(msg)
    assert "大倉山" in html


def test_messages_to_candidates_end_to_end():
    msg = _fake_message(SAMPLE_HTML, "SUUMO <no-reply@suumo.jp>")
    candidates = intake_gmail.messages_to_candidates([msg])
    assert len(candidates) == 1
    c = candidates[0]
    assert c.price_man == 6480.0
    assert c.intake_source == "gmail:suumo"


def test_messages_to_candidates_skips_unknown_portal():
    msg = _fake_message(SAMPLE_HTML, "someone@example.com")
    candidates = intake_gmail.messages_to_candidates([msg])
    assert candidates == []
