import type { HTMLAttributes, ReactNode } from 'react';

export function Card({
  children,
  className = '',
  ...rest
}: { children: ReactNode } & HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <h2 className={`mb-3 text-[13px] font-bold tracking-wide text-slate-500 dark:text-slate-400 ${className}`}>
      {children}
    </h2>
  );
}
