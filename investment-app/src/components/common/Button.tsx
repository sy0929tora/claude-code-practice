import type { ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

const VARIANT_CLASS: Record<Variant, string> = {
  primary: 'bg-teal-600 text-white active:bg-teal-700 disabled:bg-slate-300',
  secondary:
    'bg-slate-100 text-slate-700 active:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:active:bg-slate-700',
  danger: 'bg-rose-50 text-rose-600 active:bg-rose-100 dark:bg-rose-950/40 dark:text-rose-300',
  ghost: 'text-teal-600 active:bg-teal-50 dark:text-teal-400 dark:active:bg-teal-950/40',
};

export function Button({
  variant = 'primary',
  className = '',
  ...rest
}: { variant?: Variant } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={`min-h-11 rounded-xl px-4 py-2.5 text-[15px] font-semibold transition-colors disabled:cursor-not-allowed ${VARIANT_CLASS[variant]} ${className}`}
      {...rest}
    />
  );
}
