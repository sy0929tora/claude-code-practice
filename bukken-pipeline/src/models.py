"""物件候補（Candidate）のデータモデル。

各 intake（手動 / Gmail）と各 enrich ステージはすべてこの型を介して
やり取りする。フィールドは「§8 サンプルデータ」の列に合わせている。
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Candidate(BaseModel):
    """1件の物件候補。

    id は dedupe 後に採番し直すため、intake 時点では入力ソース内での
    連番や仮IDでよい。dedupe キーは (住所正規化 or name, price_man)。
    """

    id: Optional[str] = None
    name: str
    station: str
    walk_min: Optional[float] = None
    price_man: float
    land_sqm: Optional[float] = None
    bldg_sqm: Optional[float] = None
    layout: Optional[str] = None
    built_year: Optional[int] = None
    zoning: Optional[str] = None
    corner: int = 0          # 角地フラグ 0/1
    hazard_0_3: int = 0      # ハザード懸念度 0(なし)〜3(強)
    redflag_0_3: int = 0     # 資産性の赤信号（セットバック大・敷地最低限度等）0〜3

    # --- 出典・enrich ステージが埋める付加情報 ---
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    land_price_source: Optional[str] = None       # 相場データの出典
    commute_yokohama_min: Optional[float] = None
    commute_takadanobaba_min: Optional[float] = None
    commute_source: Optional[str] = None           # "google_directions" or "seed"
    source_url: Optional[str] = None                # ポータル掲載URL（Gmail intake用）
    intake_source: Optional[str] = None               # "manual" / "gmail:suumo" 等
    note: Optional[str] = None                          # 推定値である旨などのメモ

    @field_validator("hazard_0_3", "redflag_0_3", "corner")
    @classmethod
    def _clamp_0_3(cls, v: int) -> int:
        return max(0, min(3, v)) if v is not None else 0

    def dedupe_key(self) -> tuple:
        """住所（無ければ name）と価格で重複判定する。"""
        addr_key = (self.address or self.name or "").strip()
        return (addr_key, round(self.price_man, 0))


class ScoredCandidate(Candidate):
    """スコアリング後の物件候補。score.py が生成する。"""

    value_score: float = 0.0      # 割安点
    asset_score: float = 0.0      # 資産点
    commute_score: float = 0.0    # 通勤点
    size_score: float = 0.0       # 広さ点
    age_score: float = 0.0        # 築浅点
    station_score: float = 0.0    # 駅点
    hazard_penalty: float = 0.0   # ハザ減
    redflag_penalty: float = 0.0  # 赤信号減
    total_score: float = 0.0      # 総合
    rank: Optional[int] = None

    # 中間量（デバッグ・監査用に保持）
    estimated_land_value: Optional[float] = Field(default=None, description="推定土地値(万円)")
    estimated_bldg_value: Optional[float] = Field(default=None, description="建物価値(万円)")
    estimated_fair_price: Optional[float] = Field(default=None, description="推定適正(万円)")
    land_price_used: Optional[float] = Field(default=None, description="採用した相場土地坪単価(万/坪)")
