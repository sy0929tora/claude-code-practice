"""
generator.py - Claude-powered analysis and email generation module

Uses claude-opus-4-6 with adaptive thinking to:
1. Analyze company research data
2. Score outreach priority
3. Generate multiple personalized email variations
4. Produce follow-up talking points
"""
from typing import List

import anthropic
from pydantic import BaseModel

from researcher import CompanyResearch


# ── Pydantic models for structured output ────────────────────────────────────

class EmailVariation(BaseModel):
    angle: str       # e.g., "急募ポジション多数企業へのアプローチ"
    subject: str
    body: str


class OutreachResult(BaseModel):
    priority_score: int           # 0–100; higher = more urgent to contact
    priority_reason: str          # 1–2 sentence rationale
    analysis_summary: str         # ~200 chars company context
    pain_points: List[str]        # 3 specific hiring pain points
    recommended_contact: str      # e.g., "人事部 採用担当者" or "代表取締役"
    emails: List[EmailVariation]  # num_variations email drafts
    talking_points: List[str]     # 3–5 follow-up call talking points


# ── System prompt (cached; stable across requests) ───────────────────────────

SYSTEM_PROMPT = """あなたはパーソルキャリア（doda）人材紹介事業部の法人営業エキスパートです。
企業の採用課題を見抜き、その企業にとって最も響く営業アプローチを設計することが専門です。

## dodaの主な価値提案
- 登録会員数約980万人 ─ 国内最大級の転職データベース
- 各業界・職種専門のキャリアアドバイザーが厳選候補者のみを紹介
- スクリーニング・日程調整・書類整理など採用工数を大幅削減
- 求人広告では届かない「転職潜在層」にリーチ可能
- 成功報酬型（内定承諾時のみ費用発生、掲載料ゼロ）
- 中途採用の平均充足期間: 約2.3ヶ月（業界平均比30%短縮）

## 効果的な営業メールの原則
1. 相手の会社を実際に調べた具体的な証拠を示す（求人タイトル・事業内容・ニュースへの言及）
2. 「あなたの会社だからこそ」感じさせる個別化（汎用表現は禁止）
3. 一方的な売り込みではなく「課題への共感」から入る
4. 抽象的な提案でなく具体的な数値・実績・サービス仕様を交える
5. 行動しやすいCTA（「15分のご説明」「資料送付のご許可」等）
6. 300〜400字が最適（長すぎると読まれない）

## 切り口の例（参考）
- 求人数・採用活動の活発さへの言及（採用コストの効率化提案）
- 事業拡大・新規サービス開始への人材支援
- 業界特有の人材不足問題への共感と解決策
- 現在の採用手法（求人広告・ダイレクトリクルーティング等）を補完する提案
- 採用スピード・即戦力人材確保の緊急性

## 避けるべきこと
- 「突然のご連絡失礼いたします」だけの書き出し（調査内容を冒頭に入れる）
- 「優秀な人材を紹介できます」等の抽象的価値提案
- 一斉送信と分かるような汎用的な文体
- 長すぎる自社紹介"""


# ── Main generation function ──────────────────────────────────────────────────

def generate_outreach(
    company_name: str,
    research: CompanyResearch,
    num_variations: int = 2,
) -> OutreachResult:
    """
    Analyze company research data and generate personalized outreach materials.

    Args:
        company_name: Target company name
        research: CompanyResearch object with gathered web data
        num_variations: Number of email draft variations to produce

    Returns:
        OutreachResult with priority score, analysis, emails, and talking points
    """
    client = anthropic.Anthropic()

    research_text = research.to_text()
    has_research = research.has_data()

    prompt = f"""「{company_name}」へのdoda人材紹介サービスの営業アウトリーチを設計してください。

## Web調査データ
{research_text}

## 指示

### STEP 1: 企業分析
上記データをもとに以下を分析してください：
- 事業内容・規模・成長フェーズ
- 現在の採用状況（求人数・採用職種・採用難易度）
- 最近の事業展開（拡大・新規事業・課題等）
- 業界固有の採用課題

### STEP 2: 優先度スコアリング（0〜100）
以下の観点でスコアリング：
- 求人数の多さ（多いほど高スコア）
- 事業成長シグナル（高成長ほど高スコア）
- 採用難易度の高い職種が含まれるか（エンジニア・専門職等）
- 過去にdodaを使っていない可能性（確認不可なら中程度）

### STEP 3: 営業メール作成（{num_variations}パターン）
各パターンは異なる切り口で作成（例：求人数が多い企業向け、事業拡大中企業向け、等）。

メール条件：
- 文字数: 300〜400字（本文のみ、件名・署名除く）
- 書き出し: 「はじめまして」から始め、すぐに企業固有の情報に言及する
- 企業固有情報（事業内容、採用状況、ニュース等）を必ず含める
- 具体的な数値・サービス仕様を1〜2箇所に入れる
- CTA: 「15分のご説明」「資料送付」「簡単な電話」等の低ハードルな行動を促す
- 署名プレースホルダー: 「パーソルキャリア株式会社 人材紹介事業部 [氏名]」

### STEP 4: 推奨コンタクト先
企業規模・フェーズから想定されるコンタクト先（例: 「人事部 採用担当者」「管理部門担当」「代表取締役」等）

### STEP 5: フォローアップ トーキングポイント（3〜5個）
メール送付後の電話フォロー時に使える、この企業に特化した会話ネタ

必ず日本語で回答してください。"""

    print("  Claude (claude-opus-4-6) が企業を分析・メールを生成しています...")

    response = client.messages.parse(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": prompt}],
        output_format=OutreachResult,
    )

    result = response.parsed_output
    if result is None:
        raise RuntimeError(
            "Claude の出力を構造化データとして解析できませんでした。"
            "もう一度お試しください。"
        )

    return result
