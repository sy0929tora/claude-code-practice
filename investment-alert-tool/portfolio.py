"""
ポートフォリオ管理モジュール
保有銘柄の損益計算とサマリーを管理します
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Position:
    """保有ポジション"""
    symbol: str
    shares: float
    avg_cost: float  # 平均取得価格


@dataclass
class PositionPnL:
    """ポジションの損益情報"""
    symbol: str
    shares: float
    avg_cost: float
    current_price: float
    cost_basis: float      # 取得コスト合計
    market_value: float    # 評価額
    pnl: float             # 評価損益（絶対額）
    pnl_pct: float         # 評価損益（%）


class Portfolio:
    """ポートフォリオ管理クラス"""

    def __init__(self, positions: List[dict]):
        """
        Args:
            positions: config.py の PORTFOLIO リスト
                例: [{"symbol": "AAPL", "shares": 10, "avg_cost": 175.0}]
        """
        self.positions: List[Position] = []
        for p in positions:
            self.positions.append(Position(
                symbol=p["symbol"],
                shares=float(p["shares"]),
                avg_cost=float(p["avg_cost"]),
            ))

    def get_pnl(self, current_prices: Dict[str, float]) -> Dict[str, PositionPnL]:
        """
        各ポジションの損益を計算する

        Args:
            current_prices: {symbol: price} の辞書

        Returns:
            {symbol: PositionPnL} の辞書（"_total" キーに合計も含む）
        """
        result: Dict[str, PositionPnL] = {}
        total_cost = 0.0
        total_value = 0.0

        for pos in self.positions:
            price = current_prices.get(pos.symbol)
            if price is None:
                continue

            cost_basis = pos.shares * pos.avg_cost
            market_value = pos.shares * price
            pnl = market_value - cost_basis
            pnl_pct = pnl / cost_basis * 100 if cost_basis > 0 else 0.0

            result[pos.symbol] = PositionPnL(
                symbol=pos.symbol,
                shares=pos.shares,
                avg_cost=pos.avg_cost,
                current_price=price,
                cost_basis=cost_basis,
                market_value=market_value,
                pnl=pnl,
                pnl_pct=pnl_pct,
            )

            total_cost += cost_basis
            total_value += market_value

        # 合計
        total_pnl = total_value - total_cost
        total_pnl_pct = total_pnl / total_cost * 100 if total_cost > 0 else 0.0
        result["_total"] = PositionPnL(
            symbol="_total",
            shares=0,
            avg_cost=0,
            current_price=0,
            cost_basis=total_cost,
            market_value=total_value,
            pnl=total_pnl,
            pnl_pct=total_pnl_pct,
        )

        return result

    def get_position(self, symbol: str) -> Optional[Position]:
        """指定銘柄の保有ポジションを取得"""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None

    def has_position(self, symbol: str) -> bool:
        """指定銘柄を保有しているか"""
        return self.get_position(symbol) is not None
