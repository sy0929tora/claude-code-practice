export function RatioGauge({
  leftLabel,
  rightLabel,
  leftRatio,
  leftValueLabel,
  rightValueLabel,
  leftColor = 'bg-teal-500',
  rightColor = 'bg-amber-400',
}: {
  leftLabel: string;
  rightLabel: string;
  /** 0-1 */
  leftRatio: number;
  leftValueLabel: string;
  rightValueLabel: string;
  leftColor?: string;
  rightColor?: string;
}) {
  const pct = Math.max(0, Math.min(1, leftRatio)) * 100;
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-[13px]">
        <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-200">
          <span className={`h-2 w-2 rounded-full ${leftColor}`} />
          {leftLabel} <span className="font-normal text-slate-400">{leftValueLabel}</span>
        </span>
        <span className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-200">
          {rightLabel} <span className="font-normal text-slate-400">{rightValueLabel}</span>
          <span className={`h-2 w-2 rounded-full ${rightColor}`} />
        </span>
      </div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div className={`${leftColor} transition-all`} style={{ width: `${pct}%` }} />
        <div className={`${rightColor} flex-1 transition-all`} />
      </div>
      <div className="mt-1 text-center text-[12px] text-slate-400">
        {pct.toFixed(0)}% : {(100 - pct).toFixed(0)}%
      </div>
    </div>
  );
}
