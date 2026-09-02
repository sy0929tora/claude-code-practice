import { Link, useNavigate, useParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { Card, CardTitle } from '../components/common/Card';
import { StatTile } from '../components/common/StatTile';
import { EmptyState } from '../components/common/EmptyState';
import { db } from '../db/db';
import { buildLatestPriceMap, valuateHolding } from '../lib/calc';
import { formatDate, formatJPY, formatPercent, formatSigned, MARKET_LABEL, TRACK_LABEL } from '../lib/format';
import { PlusIcon, TrashIcon } from '../components/icons';

const TX_LABEL: Record<string, string> = { BUY: '買い', SELL: '売り', DIVIDEND: '配当' };

export default function HoldingDetail() {
  const { id } = useParams();
  const holdingId = Number(id);
  const navigate = useNavigate();

  const holding = useLiveQuery(() => db.holdings.get(holdingId), [holdingId]);
  const account = useLiveQuery(() => (holding ? db.accounts.get(holding.accountId) : undefined), [holding]);
  const priceMap = useLiveQuery(
    () => db.priceSnapshots.toArray().then(buildLatestPriceMap),
    [],
  );
  const thesis = useLiveQuery(
    () =>
      db.theses
        .where({ holdingId })
        .toArray()
        .then((rows) => rows.sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0]),
    [holdingId],
  );
  const transactions = useLiveQuery(
    () =>
      db.transactions
        .where({ holdingId })
        .toArray()
        .then((rows) => rows.sort((a, b) => b.date.localeCompare(a.date))),
    [holdingId],
  );

  if (!holding || !priceMap) return null;

  const valuation = valuateHolding(holding, priceMap);

  async function handleDelete() {
    if (!confirm(`「${holding!.name}」を削除しますか？関連する投資ノート・取引記録も削除されます。`)) return;
    await db.transaction('rw', [db.holdings, db.theses, db.thesisReviews, db.transactions], async () => {
      const theses = await db.theses.where({ holdingId }).toArray();
      for (const t of theses) {
        if (t.id) await db.thesisReviews.where({ thesisId: t.id }).delete();
      }
      await db.theses.where({ holdingId }).delete();
      await db.transactions.where({ holdingId }).delete();
      await db.holdings.delete(holdingId);
    });
    navigate('/portfolio');
  }

  return (
    <div>
      <PageHeader
        title={holding.name}
        back
        action={
          <Link to={`/portfolio/holdings/${holdingId}/edit`} className="text-[13px] font-semibold text-teal-600 dark:text-teal-400">
            編集
          </Link>
        }
      />
      <div className="space-y-4 px-4 py-4">
        <Card>
          <div className="mb-1 flex items-center gap-2 text-[12px] text-slate-400">
            <span>{holding.ticker}</span>
            <span>・</span>
            <span>{MARKET_LABEL[holding.market]}</span>
            <span>・</span>
            <span>{TRACK_LABEL[holding.track]}</span>
            <span>・</span>
            <span>{account?.name}</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatTile label="評価額" value={formatJPY(valuation.marketValue)} />
            <StatTile
              label="評価損益"
              value={formatSigned(valuation.gainLoss)}
              sub={formatSigned(valuation.gainLossRatio, (v) => formatPercent(v))}
              tone={valuation.gainLoss > 0 ? 'gain' : valuation.gainLoss < 0 ? 'loss' : 'neutral'}
            />
            <StatTile label="保有数量" value={`${holding.shares.toLocaleString('ja-JP')}株`} />
            <StatTile label="取得単価" value={formatJPY(holding.avgCost)} />
          </div>
          <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
            <StatTile
              label="現在値"
              value={valuation.latestPrice !== null ? formatJPY(valuation.latestPrice) : '未入力'}
            />
          </div>
        </Card>

        <Card>
          <div className="mb-3 flex items-center justify-between">
            <CardTitle className="mb-0">投資ノート（Thesis）</CardTitle>
            {thesis ? (
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                  thesis.status === 'ACTIVE'
                    ? 'bg-teal-100 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400'
                    : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
                }`}
              >
                {thesis.status === 'ACTIVE' ? '運用中' : 'クローズ済'}
              </span>
            ) : null}
          </div>
          {thesis ? (
            <div className="space-y-2">
              <div>
                <div className="text-[12px] font-semibold text-slate-400">なぜ買うか</div>
                <p className="whitespace-pre-wrap text-[14px] text-slate-700 dark:text-slate-200">{thesis.whyBuy}</p>
              </div>
              <div>
                <div className="text-[12px] font-semibold text-slate-400">撤退条件</div>
                <p className="whitespace-pre-wrap text-[14px] text-slate-700 dark:text-slate-200">
                  {thesis.exitConditions || '（未記入）'}
                </p>
              </div>
              <Link
                to={`/notes/${thesis.id}`}
                className="mt-1 inline-block text-[13px] font-semibold text-teal-600 dark:text-teal-400"
              >
                ノートの詳細・決算レビューを見る →
              </Link>
            </div>
          ) : (
            <EmptyState
              title="ノート未記入"
              description="買う前の仮説を書いておくと、決算後の答え合わせで学びに変わります。"
              action={
                <Link
                  to={`/notes/new?holdingId=${holdingId}`}
                  className="min-h-11 rounded-xl bg-teal-600 px-4 py-2.5 text-[15px] font-semibold text-white active:bg-teal-700"
                >
                  ノートを書く
                </Link>
              }
            />
          )}
        </Card>

        <Card>
          <div className="mb-3 flex items-center justify-between">
            <CardTitle className="mb-0">取引記録</CardTitle>
            <Link
              to={`/portfolio/holdings/${holdingId}/transactions/new`}
              className="flex items-center gap-1 text-[13px] font-semibold text-teal-600 dark:text-teal-400"
            >
              <PlusIcon className="h-3.5 w-3.5" /> 記録する
            </Link>
          </div>
          {transactions && transactions.length > 0 ? (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {transactions.map((tx) => (
                <div key={tx.id} className="flex items-center justify-between py-2 text-[13px]">
                  <div>
                    <span className="font-semibold text-slate-700 dark:text-slate-200">{TX_LABEL[tx.type]}</span>
                    <span className="ml-2 text-slate-400">{formatDate(tx.date)}</span>
                  </div>
                  <div className="tabular-nums text-slate-600 dark:text-slate-300">
                    {tx.type === 'DIVIDEND' ? formatJPY(tx.price) : `${formatJPY(tx.price)} × ${tx.qty}`}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[13px] text-slate-400">記録なし（履歴がなくても保有数量だけで管理できます）</p>
          )}
        </Card>

        <button
          onClick={handleDelete}
          className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-rose-200 py-2.5 text-[13px] font-semibold text-rose-500 active:bg-rose-50 dark:border-rose-900/50 dark:active:bg-rose-950/30"
        >
          <TrashIcon className="h-4 w-4" /> この銘柄を削除
        </button>
      </div>
    </div>
  );
}
