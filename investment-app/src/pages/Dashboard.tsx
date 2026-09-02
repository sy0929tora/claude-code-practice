import { Link } from 'react-router-dom';
import { PageHeader } from '../components/layout/PageHeader';
import { Card, CardTitle } from '../components/common/Card';
import { RatioGauge } from '../components/common/RatioGauge';
import { StatTile } from '../components/common/StatTile';
import { Alert } from '../components/common/Alert';
import { EmptyState } from '../components/common/EmptyState';
import { useHoldingValuations, useGoal } from '../hooks/usePortfolio';
import { computeAllocation, yearsToTarget } from '../lib/calc';
import { formatJPY, formatJPYCompact, formatPercent, formatSigned, TRACK_LABEL } from '../lib/format';
import { db } from '../db/db';
import { useLiveQuery } from 'dexie-react-hooks';
import { BackupReminderBanner } from '../components/BackupReminderBanner';

export default function Dashboard() {
  const valuations = useHoldingValuations();
  const goal = useGoal();

  const thesisHoldingIds = useLiveQuery(
    () => db.theses.where('status').equals('ACTIVE').toArray().then((rows) => new Set(rows.map((t) => t.holdingId))),
    [],
  );

  if (!valuations) {
    return (
      <div>
        <PageHeader title="ダッシュボード" />
        <div className="px-4 py-6 text-center text-sm text-slate-400">読み込み中…</div>
      </div>
    );
  }

  if (valuations.length === 0) {
    return (
      <div>
        <PageHeader title="ダッシュボード" />
        <div className="px-4 py-6">
          <EmptyState
            title="まだ保有銘柄が登録されていません"
            description="ポートフォリオタブから、口座と保有銘柄を登録して始めましょう。"
            action={
              <Link
                to="/portfolio"
                className="min-h-11 rounded-xl bg-teal-600 px-4 py-2.5 text-[15px] font-semibold text-white active:bg-teal-700"
              >
                ポートフォリオへ
              </Link>
            }
          />
        </div>
      </div>
    );
  }

  const allocation = computeAllocation(valuations);
  const totalCost = valuations.reduce((sum, v) => sum + v.costValue, 0);
  const totalGainLoss = allocation.totalValue - totalCost;
  const gainLossRatio = totalCost > 0 ? totalGainLoss / totalCost : 0;

  const missingThesisHoldings =
    thesisHoldingIds !== undefined
      ? valuations.filter((v) => v.holding.id !== undefined && !thesisHoldingIds.has(v.holding.id))
      : [];

  const reachYears =
    goal && allocation.totalValue > 0
      ? yearsToTarget(
          {
            principal: allocation.totalValue,
            monthlyContribution: goal.monthlyContribution,
            annualReturnPercent: goal.assumedReturn,
            years: goal.years,
          },
          goal.targetAmount,
        )
      : null;
  const goalProgress = goal ? Math.min(1, allocation.totalValue / goal.targetAmount) : 0;

  return (
    <div>
      <PageHeader title="ダッシュボード" />
      <div className="space-y-4 px-4 py-4">
        <BackupReminderBanner />

        <Card>
          <CardTitle>純資産評価額</CardTitle>
          <div className="text-3xl font-extrabold tabular-nums text-slate-900 dark:text-slate-50">
            {formatJPY(allocation.totalValue)}
          </div>
          <div className={`mt-1 text-[13px] font-semibold ${totalGainLoss >= 0 ? 'text-rose-500' : 'text-teal-600 dark:text-teal-400'}`}>
            {formatSigned(totalGainLoss)} （{formatSigned(gainLossRatio, (v) => formatPercent(v))}）
          </div>
        </Card>

        <Card>
          <CardTitle>コア：サテライト比率</CardTitle>
          <RatioGauge
            leftLabel="コア"
            rightLabel="サテライト"
            leftRatio={allocation.coreSatelliteRatio}
            leftValueLabel={formatJPYCompact(allocation.coreValue)}
            rightValueLabel={formatJPYCompact(allocation.satelliteValue)}
            leftColor="bg-teal-500"
            rightColor="bg-amber-400"
          />
          <p className="mt-2 text-[12px] text-slate-400">
            コア（インデックス積立）が資産の土台。サテライトは加速装置であって主役ではない。
          </p>
        </Card>

        {allocation.satelliteValue > 0 && (
          <Card>
            <CardTitle>サテライト内：守り：攻め比率</CardTitle>
            <RatioGauge
              leftLabel="守り"
              rightLabel="攻め"
              leftRatio={allocation.defenseOffenseRatio}
              leftValueLabel={formatJPYCompact(allocation.defenseValue)}
              rightValueLabel={formatJPYCompact(allocation.offenseValue)}
              leftColor="bg-sky-500"
              rightColor="bg-orange-500"
            />
          </Card>
        )}

        {goal && (
          <Card>
            <CardTitle>億り人ゲージ</CardTitle>
            <div className="mb-2 flex items-end justify-between">
              <StatTile label="目標" value={formatJPYCompact(goal.targetAmount)} />
              <StatTile
                label="到達見込み"
                value={reachYears !== null ? `約${reachYears}年後` : '試算中'}
              />
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-teal-500 to-amber-400 transition-all"
                style={{ width: `${goalProgress * 100}%` }}
              />
            </div>
            <div className="mt-1 text-right text-[12px] text-slate-400">{formatPercent(goalProgress, 1)} 達成</div>
            <Link to="/simulator" className="mt-3 inline-block text-[13px] font-semibold text-teal-600 dark:text-teal-400">
              シミュレーターで詳しく見る →
            </Link>
          </Card>
        )}

        {missingThesisHoldings.length > 0 && (
          <Alert tone="warning">
            <div className="font-semibold">投資ノート未記入の銘柄が{missingThesisHoldings.length}件あります</div>
            <div className="mt-0.5 text-[12px]">
              {missingThesisHoldings.map((v) => v.holding.name).join('・')}
            </div>
            <Link to="/notes" className="mt-1 inline-block font-semibold underline underline-offset-2">
              ノートを書く →
            </Link>
          </Alert>
        )}

        <Card>
          <CardTitle>トラック別評価額</CardTitle>
          <div className="space-y-2">
            {(['CORE', 'DEFENSE', 'OFFENSE'] as const).map((track) => {
              const value =
                track === 'CORE' ? allocation.coreValue : track === 'DEFENSE' ? allocation.defenseValue : allocation.offenseValue;
              if (value === 0) return null;
              return (
                <div key={track} className="flex items-center justify-between text-[14px]">
                  <span className="text-slate-500 dark:text-slate-400">{TRACK_LABEL[track]}</span>
                  <span className="font-semibold tabular-nums text-slate-800 dark:text-slate-100">{formatJPY(value)}</span>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}
