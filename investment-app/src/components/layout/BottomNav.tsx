import { NavLink } from 'react-router-dom';
import { HomeIcon, PortfolioIcon, NoteIcon, LearnIcon, SettingsIcon } from '../icons';

const TABS = [
  { to: '/', label: 'ホーム', Icon: HomeIcon, end: true },
  { to: '/portfolio', label: 'ポート', Icon: PortfolioIcon, end: false },
  { to: '/notes', label: 'ノート', Icon: NoteIcon, end: false },
  { to: '/learn', label: '学ぶ', Icon: LearnIcon, end: false },
  { to: '/settings', label: '設定', Icon: SettingsIcon, end: false },
];

export function BottomNav() {
  return (
    <nav className="safe-bottom fixed bottom-0 left-0 right-0 z-30 border-t border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
      <div className="mx-auto flex max-w-md">
        {TABS.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium transition-colors ${
                isActive
                  ? 'text-teal-600 dark:text-teal-400'
                  : 'text-slate-400 dark:text-slate-500'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className="h-6 w-6" strokeWidth={isActive ? 2.1 : 1.8} />
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
