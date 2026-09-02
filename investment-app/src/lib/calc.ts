import type { Holding, PriceSnapshot, Track } from '../db/db';

export interface HoldingValuation {
  holding: Holding;
  latestPrice: number | null;
  marketValue: number;
  costValue: number;
  gainLoss: number;
  gainLossRatio: number;
}

/** ticker -> 最新の手入力株価 */
export function buildLatestPriceMap(snapshots: PriceSnapshot[]): Map<string, number> {
  const map = new Map<string, { price: number; date: string }>();
  for (const s of snapshots) {
    const cur = map.get(s.ticker);
    if (!cur || s.date >= cur.date) {
      map.set(s.ticker, { price: s.price, date: s.date });
    }
  }
  const out = new Map<string, number>();
  for (const [ticker, v] of map) out.set(ticker, v.price);
  return out;
}

export function valuateHolding(holding: Holding, priceMap: Map<string, number>): HoldingValuation {
  const latestPrice = priceMap.get(holding.ticker) ?? null;
  const costValue = holding.avgCost * holding.shares;
  const marketValue = (latestPrice ?? holding.avgCost) * holding.shares;
  const gainLoss = marketValue - costValue;
  const gainLossRatio = costValue > 0 ? gainLoss / costValue : 0;
  return { holding, latestPrice, marketValue, costValue, gainLoss, gainLossRatio };
}

export function valuateHoldings(holdings: Holding[], priceMap: Map<string, number>): HoldingValuation[] {
  return holdings.map((h) => valuateHolding(h, priceMap));
}

export function sumByTrack(valuations: HoldingValuation[]): Record<Track, number> {
  const totals: Record<Track, number> = { CORE: 0, DEFENSE: 0, OFFENSE: 0 };
  for (const v of valuations) {
    totals[v.holding.track] += v.marketValue;
  }
  return totals;
}

export interface AllocationSummary {
  totalValue: number;
  coreValue: number;
  satelliteValue: number;
  coreSatelliteRatio: number; // 0-1, コアの比率
  defenseValue: number;
  offenseValue: number;
  defenseOffenseRatio: number; // 0-1, サテライト内での守りの比率
}

export function computeAllocation(valuations: HoldingValuation[]): AllocationSummary {
  const totals = sumByTrack(valuations);
  const totalValue = totals.CORE + totals.DEFENSE + totals.OFFENSE;
  const satelliteValue = totals.DEFENSE + totals.OFFENSE;
  return {
    totalValue,
    coreValue: totals.CORE,
    satelliteValue,
    coreSatelliteRatio: totalValue > 0 ? totals.CORE / totalValue : 0,
    defenseValue: totals.DEFENSE,
    offenseValue: totals.OFFENSE,
    defenseOffenseRatio: satelliteValue > 0 ? totals.DEFENSE / satelliteValue : 0,
  };
}

/** 課税配当の概算手取り（20.315%控除） */
export const DIVIDEND_TAX_RATE = 0.20315;

export function netDividend(gross: number, taxable: boolean): number {
  return taxable ? gross * (1 - DIVIDEND_TAX_RATE) : gross;
}

// ---------------------------------------------------------------------------
// 億り人シミュレーター（複利計算）
// ---------------------------------------------------------------------------

export interface SimulatorInput {
  principal: number; // 現在の資産
  monthlyContribution: number;
  annualReturnPercent: number; // 例: 5 = 5%
  years: number;
}

export interface SimulatorYearPoint {
  year: number;
  contributions: number; // 累計元本（初期資産＋積立累計）
  balance: number; // 評価額
}

export function simulateCompoundGrowth(input: SimulatorInput): SimulatorYearPoint[] {
  const { principal, monthlyContribution, annualReturnPercent, years } = input;
  const monthlyRate = annualReturnPercent / 100 / 12;
  const points: SimulatorYearPoint[] = [];
  let balance = principal;
  let contributions = principal;
  points.push({ year: 0, contributions, balance });
  for (let year = 1; year <= years; year++) {
    for (let m = 0; m < 12; m++) {
      balance = balance * (1 + monthlyRate) + monthlyContribution;
      contributions += monthlyContribution;
    }
    points.push({ year, contributions, balance: Math.round(balance) });
  }
  return points;
}

/** 目標金額に到達するまでの年数（見つからなければnull） */
export function yearsToTarget(input: SimulatorInput, target: number): number | null {
  const points = simulateCompoundGrowth({ ...input, years: Math.max(input.years, 60) });
  const hit = points.find((p) => p.balance >= target);
  return hit ? hit.year : null;
}

/** ポジション比率（総資産に対する各保有の比率） */
export function positionRatio(valuation: HoldingValuation, totalValue: number): number {
  return totalValue > 0 ? valuation.marketValue / totalValue : 0;
}
