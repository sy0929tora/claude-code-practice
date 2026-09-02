import { Link } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { Card } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { PlusIcon } from '../components/icons';
import { useHoldingValuations, useAccounts, useAppSettings } from '../hooks/usePortfolio';
import { positionRatio } from '../lib/calc';
import { formatJPY, formatPercent, formatSigned, ACCOUNT_TYPE_LABEL, TRACK_LABEL } from '../lib/format';
import { db } from '../db/db';

const TRACK_DOT: Record<string, string> = {
  CORE: 'bg-teal-500',
  DEFENSE: 'bg-sky-500',
  OFFENSE: 'bg-orange-500',
};

export default function Portfolio() {
  const valuations = useHoldingValuations();
  const accounts = useAccounts();
  const settings = useAppSettings();
  const thesisHoldingIds = useLiveQuery(
    () => db.theses.where('status').equals('ACTIVE').toArray().then((rows) => new Set(rows.map((t) => t.holdingId))),
    [],
  );

  const totalValue = valuations?.reduce((s, v) => s + v.marketValue, 0) ?? 0;

  return (
    <div>
      <PageHeader
        title="ポートフォリオ"
        action={
          <Link to="/portfolio/prices" className="text-[13px] font-semibold text-teal-600 dark:text-teal-400">
            価格更新
          </Link>
        }
      />
      <div className="space-y-4 px-4 py-4">
        <div className="flex gap-2">
          <Link to="/portfolio/holdings/new" className="flex-1">
            <Button className="flex w-full items-center justify-center gap-1">
              <PlusIcon className="h-4 w-4" /> 銘柄を追加
            </Button>
          </Link>
          <Link to="/portfolio/accounts/new" className="flex-1">
            <Button variant="secondary" className="w-full">
              口座を追加
            </Button>
          </Link>
        </div>

        {accounts && accounts.length === 0 && (
          <EmptyState
            title="口座が未登録です"
            description="先に口座（NISA成長投資枠、課税口座など）を登録してください。"
          />
        )}

        {valuations && valuations.length === 0 && accounts && accounts.length > 0 && (
          <EmptyState title="保有銘柄がありません" description="「銘柄を追加」から最初のポジションを登録しましょう。" />
        )}

        {accounts?.map((account) => {
          const rows = valuations?.filter((v) => v.holding.accountId === account.id) ?? [];
          if (rows.length === 0) return null;
          const accountTotal = rows.reduce((s, v) => s + v.marketValue, 0);
          return (
            <div key={account.id}>
              <div className="mb-1.5 flex items-baseline justify-between px-1">
                <h2 className="text-[13px] font-bold text-slate-500 dark:text-slate-400">
                  {account.name}
                  <span className="ml-1.5 font-normal text-slate-400">{ACCOUNT_TYPE_LABEL[account.type]}</span>
                </h2>
                <span className="text-[12px] font-semibold text-slate-400">{formatJPY(accountTotal)}</span>
              </div>
              <div className="space-y-2">
                {rows.map((v) => {
                  const ratio = positionRatio(v, totalValue);
                  const overLimit = settings && ratio > settings.maxPositionRatio;
                  const hasThesis = v.holding.id !== undefined && thesisHoldingIds?.has(v.holding.id);
                  return (
                    <Link key={v.holding.id} to={`/portfolio/holdings/${v.holding.id}`}>
                      <Card className="active:bg-slate-50 dark:active:bg-slate-800">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${TRACK_DOT[v.holding.track]}`} />
                              <span className="text-[11px] font-semibold text-slate-400">
                                {TRACK_LABEL[v.holding.track]}
                              </span>
                              {!hasThesis && (
                                <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 dark:bg-amber-950/50 dark:text-amber-400">
                                  ノート未記入
                                </span>
                              )}
                              {overLimit && (
                                <span className="rounded bg-rose-100 px-1.5 py-0.5 text-[10px] font-bold text-rose-700 dark:bg-rose-950/50 dark:text-rose-400">
                                  上限超過
                                </span>
                              )}
                            </div>
                            <div className="truncate font-bold text-slate-900 dark:text-slate-50">{v.holding.name}</div>
                            <div className="text-[12px] text-slate-400">
                              {v.holding.ticker} ・ {v.holding.shares.toLocaleString('ja-JP')}株
                            </div>
                          </div>
                          <div className="shrink-0 text-right">
                            <div className="font-bold tabular-nums text-slate-900 dark:text-slate-50">
                              {formatJPY(v.marketValue)}
                            </div>
                            <div
                              className={`text-[12px] font-semibold tabular-nums ${
                                v.gainLoss >= 0 ? 'text-rose-500' : 'text-teal-600 dark:text-teal-400'
                              }`}
                            >
                              {formatSigned(v.gainLossRatio, (x) => formatPercent(x))}
                            </div>
                          </div>
                        </div>
                        <div className="mt-2 text-[11px] text-slate-400">資産構成比 {formatPercent(ratio)}</div>
                      </Card>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
