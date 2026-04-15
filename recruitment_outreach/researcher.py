"""
researcher.py - Web research module

Searches the web for company information using DuckDuckGo.
Gathers: company overview, job listings, recent news, industry context.
"""
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


@dataclass
class CompanyResearch:
    company_name: str
    overview_results: list = field(default_factory=list)
    job_listing_results: list = field(default_factory=list)
    news_results: list = field(default_factory=list)
    industry_results: list = field(default_factory=list)

    def has_data(self) -> bool:
        return any([
            self.overview_results,
            self.job_listing_results,
            self.news_results,
            self.industry_results,
        ])

    def to_text(self) -> str:
        """Format research data as structured text for Claude."""
        sections = []

        if self.overview_results:
            sections.append("### 会社概要・事業内容")
            for r in self.overview_results[:5]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")[:300]
                url = r.get("url", "")
                sections.append(f"- {title}\n  {snippet}\n  出典: {url}")

        if self.job_listing_results:
            sections.append("\n### 求人・採用状況")
            for r in self.job_listing_results[:5]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")[:300]
                sections.append(f"- {title}\n  {snippet}")

        if self.news_results:
            sections.append("\n### 最新ニュース・動向（2024〜2025年）")
            for r in self.news_results[:5]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")[:300]
                sections.append(f"- {title}\n  {snippet}")

        if self.industry_results:
            sections.append("\n### 業界コンテキスト・採用トレンド")
            for r in self.industry_results[:3]:
                title = r.get("title", "")
                snippet = r.get("snippet", "")[:300]
                sections.append(f"- {title}\n  {snippet}")

        if not sections:
            return "（Web調査データなし）"

        return "\n".join(sections)


def _ddg_search(query: str, max_results: int = 5) -> list:
    """Perform a DuckDuckGo search and return structured results."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(
                query,
                max_results=max_results,
                region="jp-ja",
                safesearch="moderate",
            ):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                })
    except Exception as e:
        # Silently continue; Claude will work with whatever data is available
        pass
    return results


def research_company(
    company_name: str,
    industry: Optional[str] = None,
) -> CompanyResearch:
    """
    Research a company across multiple dimensions.
    Returns a CompanyResearch object with all gathered data.
    """
    research = CompanyResearch(company_name=company_name)

    if not HAS_DDGS:
        print("  ⚠️  duckduckgo-search がインストールされていません。")
        print("      pip install duckduckgo-search でインストールしてください。")
        print("  ⚠️  Web調査なしでメール生成を続行します。\n")
        return research

    queries = [
        # (query, target_field, label)
        (
            f"{company_name} 会社概要 事業内容 サービス",
            "overview_results",
            "会社概要・事業内容",
        ),
        (
            f"{company_name} 採用 求人 中途 2024 2025",
            "job_listing_results",
            "採用・求人状況",
        ),
        (
            f"{company_name} ニュース 事業拡大 資金調達 新規事業 2024 2025",
            "news_results",
            "最新ニュース・動向",
        ),
    ]

    if industry:
        queries.append((
            f"{industry} 人材不足 採用難 エンジニア不足 課題 2024 2025",
            "industry_results",
            f"{industry}業界コンテキスト",
        ))

    for query, field_name, label in queries:
        print(f"  → {label}を検索中...")
        results = _ddg_search(query, max_results=5)
        setattr(research, field_name, results)
        time.sleep(0.8)  # rate limiting

    return research
