import type { ReactNode } from 'react';

export function StatTile({
  label,
  value,
  sub,
  tone = 'neutral',
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  /** 日本の相場慣習に合わせ、含み益=赤(gain)・含み損=青緑(loss) で表示 */
  tone?: 'neutral' | 'gain' | 'loss';
}) {
  const toneClass =
    tone === 'gain'
      ? 'text-rose-500'
      : tone === 'loss'
        ? 'text-teal-600 dark:text-teal-400'
        : 'text-slate-900 dark:text-slate-50';
  return (
    <div>
      <div className="text-[12px] text-slate-400">{label}</div>
      <div className={`text-xl font-bold tabular-nums ${toneClass}`}>{value}</div>
      {sub && <div className="text-[12px] text-slate-400">{sub}</div>}
    </div>
  );
}
