import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

function Label({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <label className="mb-1 block text-[13px] font-semibold text-slate-600 dark:text-slate-300">
      {children}
      {hint && <span className="ml-1.5 font-normal text-slate-400">{hint}</span>}
    </label>
  );
}

const inputClass =
  'w-full min-h-11 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-[15px] text-slate-900 outline-none placeholder:text-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50 dark:placeholder:text-slate-600 dark:focus:ring-teal-900/40';

export function TextField({
  label,
  hint,
  ...rest
}: { label: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <Label hint={hint}>{label}</Label>
      <input type="text" className={inputClass} {...rest} />
    </div>
  );
}

/** 数値入力。iPhoneでテンキーが出るよう inputmode="decimal" を既定にする */
export function NumberField({
  label,
  hint,
  ...rest
}: { label: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <Label hint={hint}>{label}</Label>
      <input type="number" inputMode="decimal" step="any" className={`${inputClass} tabular-nums`} {...rest} />
    </div>
  );
}

export function DateField({
  label,
  hint,
  ...rest
}: { label: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <Label hint={hint}>{label}</Label>
      <input type="date" className={inputClass} {...rest} />
    </div>
  );
}

export function SelectField({
  label,
  hint,
  children,
  ...rest
}: { label: string; hint?: string; children: ReactNode } & SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div>
      <Label hint={hint}>{label}</Label>
      <select className={inputClass} {...rest}>
        {children}
      </select>
    </div>
  );
}

export function TextAreaField({
  label,
  hint,
  ...rest
}: { label: string; hint?: string } & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <div>
      <Label hint={hint}>{label}</Label>
      <textarea className={`${inputClass} min-h-24 resize-y`} {...rest} />
    </div>
  );
}
