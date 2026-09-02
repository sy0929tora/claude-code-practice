import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert } from './common/Alert';
import { useAppSettings } from '../hooks/usePortfolio';
import { shouldShowBackupReminder, dismissBackupReminder } from '../lib/persist';
import { formatDate } from '../lib/format';

export function BackupReminderBanner() {
  const settings = useAppSettings();
  const [dismissed, setDismissed] = useState(false);
  if (!settings || dismissed) return null;
  if (!shouldShowBackupReminder(settings.lastExportedAt)) return null;

  return (
    <Alert tone="info">
      <div className="font-semibold">
        {settings.lastExportedAt ? `前回のバックアップ: ${formatDate(settings.lastExportedAt)}` : 'まだバックアップがありません'}
      </div>
      <div className="mt-0.5 text-[12px]">
        データは端末内にのみ保存されます。週1回、設定からJSONを書き出しておきましょう。
      </div>
      <div className="mt-1.5 flex gap-3">
        <Link to="/settings" className="font-semibold underline underline-offset-2">
          設定へ
        </Link>
        <button
          onClick={() => {
            dismissBackupReminder();
            setDismissed(true);
          }}
          className="text-slate-400 underline underline-offset-2"
        >
          後で
        </button>
      </div>
    </Alert>
  );
}
