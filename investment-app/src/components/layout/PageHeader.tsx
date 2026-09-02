import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeftIcon } from '../icons';

export function PageHeader({
  title,
  back,
  action,
}: {
  title: string;
  back?: boolean;
  action?: ReactNode;
}) {
  const navigate = useNavigate();
  return (
    <header className="safe-top sticky top-0 z-20 flex items-center gap-2 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
      {back && (
        <button
          onClick={() => navigate(-1)}
          aria-label="戻る"
          className="-ml-2 flex h-9 w-9 items-center justify-center rounded-full text-slate-500 active:bg-slate-100 dark:text-slate-400 dark:active:bg-slate-800"
        >
          <ChevronLeftIcon className="h-5 w-5" />
        </button>
      )}
      <h1 className="flex-1 truncate text-[17px] font-bold text-slate-900 dark:text-slate-50">{title}</h1>
      {action}
    </header>
  );
}
