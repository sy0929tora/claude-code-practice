import { Link } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { Card, CardTitle } from '../components/common/Card';
import { EmptyState } from '../components/common/EmptyState';
import { Alert } from '../components/common/Alert';
import { db } from '../db/db';
import { formatDate } from '../lib/format';

export default function Notes() {
  const holdings = useLiveQuery(() => db.holdings.toArray(), []);
  const theses = useLiveQuery(() => db.theses.toArray(), []);
  const reviews = useLiveQuery(() => db.thesisReviews.toArray(), []);

  if (!holdings || !theses || !reviews) return null;

  const holdingsWithThesis = new Set(theses.map((t) => t.holdingId).filter((v): v is number => v !== undefined));
  const missing = holdings.filter((h) => h.id !== undefined && !holdingsWithThesis.has(h.id));

  const active = theses.filter((t) => t.status === 'ACTIVE').sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const closed = theses.filter((t) => t.status === 'CLOSED').sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const reviewCountByThesis = new Map<number, number>();
  for (const r of reviews) reviewCountByThesis.set(r.thesisId, (reviewCountByThesis.get(r.thesisId) ?? 0) + 1);
  const holdingById = new Map(holdings.map((h) => [h.id, h]));

  const noReview = active.filter((t) => t.id !== undefined && !reviewCountByThesis.has(t.id));

  return (
    <div>
      <PageHeader title="投資ノート" />
      <div className="space-y-4 px-4 py-4">
        {missing.length > 0 && (
          <Alert tone="warning">
            <div className="font-semibold">未記入の銘柄が{missing.length}件あります</div>
            <div className="mt-1 flex flex-wrap gap-2">
              {missing.map((h) => (
                <Link
                  key={h.id}
                  to={`/notes/new?holdingId=${h.id}`}
                  className="rounded-full bg-white px-2.5 py-1 text-[12px] font-semibold text-amber-800 shadow-sm dark:bg-slate-900 dark:text-amber-300"
                >
                  {h.name} を書く
                </Link>
              ))}
            </div>
          </Alert>
        )}

        {noReview.length > 0 && (
          <Card>
            <CardTitle>決算レビュー待ち</CardTitle>
            <div className="space-y-2">
              {noReview.map((t) => {
                const h = t.holdingId ? holdingById.get(t.holdingId) : undefined;
                return (
                  <Link
                    key={t.id}
                    to={`/notes/${t.id}`}
                    className="flex items-center justify-between rounded-lg px-1 py-1 text-[14px] active:bg-slate-50 dark:active:bg-slate-800"
                  >
                    <span className="font-semibold text-slate-700 dark:text-slate-200">{h?.name ?? '（不明）'}</span>
                    <span className="text-teal-600 dark:text-teal-400">決算後に振り返る →</span>
                  </Link>
                );
              })}
            </div>
          </Card>
        )}

        <div>
          <h2 className="mb-1.5 px-1 text-[13px] font-bold text-slate-500 dark:text-slate-400">運用中のノート</h2>
          {active.length === 0 ? (
            <EmptyState title="運用中のノートはまだありません" />
          ) : (
            <div className="space-y-2">
              {active.map((t) => {
                const h = t.holdingId ? holdingById.get(t.holdingId) : undefined;
                return (
                  <Link key={t.id} to={`/notes/${t.id}`}>
                    <Card className="active:bg-slate-50 dark:active:bg-slate-800">
                      <div className="mb-1 flex items-center justify-between">
                        <span className="font-bold text-slate-900 dark:text-slate-50">{h?.name ?? '（候補銘柄）'}</span>
                        <span className="text-[11px] text-slate-400">{formatDate(t.createdAt)}</span>
                      </div>
                      <p className="line-clamp-2 text-[13px] text-slate-500 dark:text-slate-400">{t.whyBuy}</p>
                      <div className="mt-1 text-[11px] text-slate-400">
                        レビュー {reviewCountByThesis.get(t.id!) ?? 0} 件
                      </div>
                    </Card>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {closed.length > 0 && (
          <div>
            <h2 className="mb-1.5 px-1 text-[13px] font-bold text-slate-500 dark:text-slate-400">クローズ済み</h2>
            <div className="space-y-2">
              {closed.map((t) => {
                const h = t.holdingId ? holdingById.get(t.holdingId) : undefined;
                return (
                  <Link key={t.id} to={`/notes/${t.id}`}>
                    <Card className="opacity-70 active:bg-slate-50 dark:active:bg-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-700 dark:text-slate-200">{h?.name ?? '（候補銘柄）'}</span>
                        <span className="text-[11px] text-slate-400">{formatDate(t.createdAt)}</span>
                      </div>
                    </Card>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
