import type { ReactNode } from 'react';
import { BottomNav } from './BottomNav';
import { UpdateToast } from '../UpdateToast';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto min-h-full max-w-md bg-slate-50 pb-20 dark:bg-slate-950">
      {children}
      <UpdateToast />
      <BottomNav />
    </div>
  );
}
