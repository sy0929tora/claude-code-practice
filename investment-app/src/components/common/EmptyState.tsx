import type { ReactNode } from 'react';

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-300 px-6 py-10 text-center dark:border-slate-700">
      <p className="font-semibold text-slate-600 dark:text-slate-300">{title}</p>
      {description && <p className="text-[13px] text-slate-400">{description}</p>}
      {action}
    </div>
  );
}
