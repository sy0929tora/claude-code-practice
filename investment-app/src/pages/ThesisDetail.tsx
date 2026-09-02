import { Link, useNavigate, useParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { db } from '../db/db';
import { formatDate, VERDICT_LABEL } from '../lib/format';
import { PlusIcon } from '../components/icons';

const VERDICT_TONE: Record<string, string> = {
  ON_TRACK: 'bg-teal-100 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400',
  OFF_TRACK: 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400',
  EXIT: 'bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400',
};

const FIELDS: { key: 'whyBuy' | 'bullCase' | 'baseCase' | 'bearCase' | 'entryRationale' | 'exitConditions'; label: string }[] = [
  { key: 'whyBuy', label: '① なぜ買うか' },
  { key: 'bullCase', label: '② シナリオ - 強気' },
  { key: 'baseCase', label: '② シナリオ - 基本' },
  { key: 'bearCase', label: '② シナリオ - 弱気' },
  { key: 'entryRationale', label: '③ エントリー根拠' },
  { key: 'exitConditions', label: '④ 撤退条件' },
];

export default function ThesisDetail() {
  const { id } = useParams();
  const thesisId = Number(id);
  const navigate = useNavigate();

  const thesis = useLiveQuery(() => db.theses.get(thesisId), [thesisId]);
  const holding = useLiveQuery(() => (thesis?.holdingId ? db.holdings.get(thesis.holdingId) : undefined), [thesis]);
  const reviews = useLiveQuery(
    () =>
      db.thesisReviews
        .where({ thesisId })
        .toArray()
        .then((rows) => rows.sort((a, b) => b.earningsDate.localeCompare(a.earningsDate))),
    [thesisId],
  );

  if (!thesis) return null;

  async function toggleStatus() {
    await db.theses.update(thesisId, { status: thesis!.status === 'ACTIVE' ? 'CLOSED' : 'ACTIVE' });
  }

  return (
    <div>
      <PageHeader
        title={holding?.name ?? '投資ノート'}
        back
        action={
          <Link to={`/notes/${thesisId}/edit`} className="text-[13px] font-semibold text-teal-600 dark:text-teal-400">
            編集
          </Link>
        }
      />
      <div className="space-y-4 px-4 py-4">
        <div className="flex items-center justify-between">
          <span
            className={`rounded px-2 py-1 text-[11px] font-bold ${
              thesis.status === 'ACTIVE'
                ? 'bg-teal-100 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400'
                : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
            }`}
          >
            {thesis.status === 'ACTIVE' ? '運用中' : 'クローズ済み'}
          </span>
          <button onClick={toggleStatus} className="text-[13px] font-semibold text-slate-400 underline underline-offset-2">
            {thesis.status === 'ACTIVE' ? 'クローズにする' : '再開する'}
          </button>
        </div>

        <Card>
          <div className="space-y-3">
            {FIELDS.map(({ key, label }) => (
              <div key={key}>
                <div className="text-[12px] font-semibold text-slate-400">{label}</div>
                <p className="whitespace-pre-wrap text-[14px] text-slate-700 dark:text-slate-200">
                  {thesis[key] || '（未記入）'}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-3 text-[11px] text-slate-400">作成日: {formatDate(thesis.createdAt)}</div>
        </Card>

        <div>
          <div className="mb-2 flex items-center justify-between px-1">
            <h2 className="text-[13px] font-bold text-slate-500 dark:text-slate-400">決算レビュー</h2>
            <Link
              to={`/notes/${thesisId}/reviews/new`}
              className="flex items-center gap-1 text-[13px] font-semibold text-teal-600 dark:text-teal-400"
            >
              <PlusIcon className="h-3.5 w-3.5" /> 記録する
            </Link>
          </div>
          {reviews && reviews.length > 0 ? (
            <div className="space-y-2">
              {reviews.map((r) => (
                <Card key={r.id}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-[12px] font-semibold text-slate-400">{formatDate(r.earningsDate)}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${VERDICT_TONE[r.verdict]}`}>
                      {VERDICT_LABEL[r.verdict]}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap text-[14px] text-slate-700 dark:text-slate-200">{r.note}</p>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              title="決算レビューはまだありません"
              description="買う前の仮説と決算の答え合わせをすることが、このアプリで一番大事な習慣です。"
            />
          )}
        </div>

        {holding && (
          <Button variant="secondary" className="w-full" onClick={() => navigate(`/portfolio/holdings/${holding.id}`)}>
            銘柄の詳細を見る
          </Button>
        )}
      </div>
    </div>
  );
}
