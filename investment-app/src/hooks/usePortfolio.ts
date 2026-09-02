import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../db/db';
import { buildLatestPriceMap, valuateHoldings } from '../lib/calc';

/** 保有銘柄一覧＋最新株価から算出した評価額付きの一覧 */
export function useHoldingValuations() {
  return useLiveQuery(async () => {
    const [holdings, snapshots] = await Promise.all([
      db.holdings.toArray(),
      db.priceSnapshots.toArray(),
    ]);
    const priceMap = buildLatestPriceMap(snapshots);
    return valuateHoldings(holdings, priceMap);
  }, []);
}

export function useAccounts() {
  return useLiveQuery(() => db.accounts.toArray(), []);
}

export function useActiveTheses() {
  return useLiveQuery(() => db.theses.where('status').equals('ACTIVE').toArray(), []);
}

export function useGoal() {
  return useLiveQuery(() => db.goals.toCollection().first(), []);
}

export function useAppSettings() {
  return useLiveQuery(() => db.appSettings.toCollection().first(), []);
}
