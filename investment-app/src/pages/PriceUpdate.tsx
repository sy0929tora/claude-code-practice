import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { db } from '../db/db';
import { buildLatestPriceMap } from '../lib/calc';
import { formatDate, todayISO } from '../lib/format';

export default function PriceUpdate() {
  const holdings = useLiveQuery(() => db.holdings.toArray(), []);
  const snapshots = useLiveQuery(() => db.priceSnapshots.toArray(), []);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<Record<string, boolean>>({});

  if (!holdings || !snapshots) return null;

  const tickers = Array.from(new Map(holdings.map((h) => [h.ticker, h.name])).entries());
  const priceMap = buildLatestPriceMap(snapshots);
  const latestDateByTicker = new Map<string, string>();
  for (const s of snapshots) {
    const cur = latestDateByTicker.get(s.ticker);
    if (!cur || s.date > cur) latestDateByTicker.set(s.ticker, s.date);
  }

  async function saveOne(ticker: string) {
    const raw = drafts[ticker];
    const price = Number(raw);
    if (!raw || !Number.isFinite(price) || price < 0) return;
    const today = todayISO();
    const existing = await db.priceSnapshots.where({ ticker, date: today }).first();
    if (existing?.id) {
      await db.priceSnapshots.update(existing.id, { price });
    } else {
      await db.priceSnapshots.add({ ticker, price, date: today });
    }
    setSaved((s) => ({ ...s, [ticker]: true }));
    setTimeout(() => setSaved((s) => ({ ...s, [ticker]: false })), 1500);
  }

  async function saveAll() {
    for (const [ticker] of tickers) {
      if (drafts[ticker]) await saveOne(ticker);
    }
  }

  if (tickers.length === 0) {
    return (
      <div>
        <PageHeader title="価格を更新" back />
        <div className="px-4 py-6">
          <EmptyState title="保有銘柄がありません" description="先に銘柄を登録してください。" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="価格を更新" back />
      <div className="space-y-3 px-4 py-4">
        <p className="text-[12px] text-slate-400">
          証券アプリの表示を見ながら、円建ての最新価格を入力してください。株価は毎分の値動きを追う必要はありません
          — 週1回や決算後の更新で十分です。
        </p>
        {tickers.map(([ticker, name]) => (
          <Card key={ticker}>
            <div className="mb-2 flex items-center justify-between">
              <div>
                <div className="font-bold text-slate-900 dark:text-slate-50">{name}</div>
                <div className="text-[12px] text-slate-400">{ticker}</div>
              </div>
              <div className="text-right text-[11px] text-slate-400">
                現在値: {priceMap.get(ticker) !== undefined ? priceMap.get(ticker)!.toLocaleString('ja-JP') : '未入力'}
                <br />
                更新日: {formatDate(latestDateByTicker.get(ticker))}
              </div>
            </div>
            <div className="flex gap-2">
              <input
                type="number"
                inputMode="decimal"
                step="any"
                placeholder="新しい価格（円）"
                value={drafts[ticker] ?? ''}
                onChange={(e) => setDrafts((d) => ({ ...d, [ticker]: e.target.value }))}
                className="min-h-11 w-full flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-[15px] tabular-nums outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50"
              />
              <Button variant={saved[ticker] ? 'secondary' : 'primary'} onClick={() => saveOne(ticker)}>
                {saved[ticker] ? '保存済み' : '保存'}
              </Button>
            </div>
          </Card>
        ))}
        <Button variant="secondary" className="w-full" onClick={saveAll}>
          入力した価格をまとめて保存
        </Button>
      </div>
    </div>
  );
}
