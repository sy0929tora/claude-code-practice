import type { ReactNode } from 'react';
import { AlertIcon } from '../icons';

const TONE_CLASS: Record<string, string> = {
  warning:
    'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300',
  danger:
    'border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300',
  info: 'border-teal-300 bg-teal-50 text-teal-800 dark:border-teal-900/60 dark:bg-teal-950/40 dark:text-teal-300',
};

export function Alert({
  tone = 'warning',
  children,
  action,
}: {
  tone?: 'warning' | 'danger' | 'info';
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className={`flex items-start gap-2 rounded-xl border px-3 py-2.5 text-[13px] ${TONE_CLASS[tone]}`}>
      <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">{children}</div>
      {action}
    </div>
  );
}
