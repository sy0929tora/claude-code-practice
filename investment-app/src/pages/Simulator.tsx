import { useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { PageHeader } from '../components/layout/PageHeader';
import { Card, CardTitle } from '../components/common/Card';
import { NumberField } from '../components/common/Field';
import { Button } from '../components/common/Button';
import { StatTile } from '../components/common/StatTile';
import { useGoal, useHoldingValuations } from '../hooks/usePortfolio';
import { db } from '../db/db';
import { simulateCompoundGrowth, yearsToTarget } from '../lib/calc';
import { formatCompactNumber, formatJPYCompact } from '../lib/format';

export default function Simulator() {
  const goal = useGoal();
  const valuations = useHoldingValuations();
  const currentTotal = valuations?.reduce((s, v) => s + v.marketValue, 0) ?? 0;

  const [principal, setPrincipal] = useState<string | null>(null);
  const [monthly, setMonthly] = useState<string | null>(null);
  const [rate, setRate] = useState<string | null>(null);
  const [years, setYears] = useState<string | null>(null);
  const [target, setTarget] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  if (!goal) return null;

  const principalNum = principal !== null ? Number(principal) : currentTotal;
  const monthlyNum = monthly !== null ? Number(monthly) : goal.monthlyContribution;
  const rateNum = rate !== null ? Number(rate) : goal.assumedReturn;
  const yearsNum = years !== null ? Number(years) : goal.years;
  const targetNum = target !== null ? Number(target) : goal.targetAmount;

  const points = simulateCompoundGrowth({
    principal: principalNum,
    monthlyContribution: monthlyNum,
    annualReturnPercent: rateNum,
    years: yearsNum,
  });
  const finalBalance = points[points.length - 1]?.balance ?? 0;
  const reachYears = yearsToTarget(
    { principal: principalNum, monthlyContribution: monthlyNum, annualReturnPercent: rateNum, years: yearsNum },
    targetNum,
  );

  async function handleSave() {
    if (!goal?.id) return;
    await db.goals.update(goal.id, {
      monthlyContribution: monthlyNum,
      assumedReturn: rateNum,
      years: yearsNum,
      targetAmount: targetNum,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  return (
    <div>
      <PageHeader title="億り人シミュレーター" back />
      <div className="space-y-4 px-4 py-4">
        <Card>
          <CardTitle>資産推移の見込み</CardTitle>
          <div className="mb-2 grid grid-cols-2 gap-3">
            <StatTile label={`${yearsNum}年後の評価額`} value={formatJPYCompact(finalBalance)} />
            <StatTile label="目標到達" value={reachYears !== null ? `約${reachYears}年後` : '設定年数内では未到達'} />
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={points} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="balanceFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#14b8a6" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#14b8a6" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="year" tickFormatter={(v) => `${v}年`} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => formatCompactNumber(v)} tick={{ fontSize: 11, fill: '#94a3b8' }} width={44} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(value: unknown, key: unknown) => [
                    formatJPYCompact(Number(value)),
                    key === 'balance' ? '評価額' : '累計元本',
                  ]}
                  labelFormatter={(v) => `${v}年後`}
                />
                <Area type="monotone" dataKey="contributions" stroke="#94a3b8" fill="none" strokeDasharray="4 3" />
                <Area type="monotone" dataKey="balance" stroke="#0d9488" fill="url(#balanceFill)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">
            実線＝積立×複利での評価額の見込み ／ 破線＝積み立てた元本の累計。差が複利効果です。
          </p>
        </Card>

        <Card>
          <CardTitle>前提条件</CardTitle>
          <div className="space-y-3">
            <NumberField
              label="現在の資産（初期値）"
              hint="円 ・ 未入力ならポートフォリオの現在評価額"
              placeholder={String(currentTotal)}
              value={principal ?? ''}
              onChange={(e) => setPrincipal(e.target.value)}
            />
            <NumberField label="月次積立額" hint="円" value={monthly ?? String(goal.monthlyContribution)} onChange={(e) => setMonthly(e.target.value)} />
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="想定利回り" hint="年率 %" value={rate ?? String(goal.assumedReturn)} onChange={(e) => setRate(e.target.value)} />
              <NumberField label="運用年数" hint="年" value={years ?? String(goal.years)} onChange={(e) => setYears(e.target.value)} />
            </div>
            <NumberField label="目標金額" hint="円" value={target ?? String(goal.targetAmount)} onChange={(e) => setTarget(e.target.value)} />
          </div>
          <Button className="mt-4 w-full" variant={saved ? 'secondary' : 'primary'} onClick={handleSave}>
            {saved ? '保存しました' : 'この条件を保存'}
          </Button>
          <p className="mt-2 text-[11px] text-slate-400">
            主役は「積立×時間」です。個別株はこの複利エンジンを加速させる装置であって、一発逆転を狙う場ではありません。
          </p>
        </Card>
      </div>
    </div>
  );
}
