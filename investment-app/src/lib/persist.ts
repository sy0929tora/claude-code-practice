/**
 * iOSのSafari/PWAはIndexedDBを長期間未使用・空き容量逼迫時にまれに削除することがある。
 * navigator.storage.persist() で永続化をリクエストし、削除されにくくする。
 * （バックアップ機能を使うことが最終的な安全策であり、これは補助策）
 */
export async function requestPersistentStorage(): Promise<boolean> {
  try {
    if (navigator.storage && navigator.storage.persist) {
      const already = await navigator.storage.persisted?.();
      if (already) return true;
      return await navigator.storage.persist();
    }
  } catch {
    // Safari の一部バージョンでは例外を投げることがあるため無視
  }
  return false;
}

const LAST_EXPORT_KEY = 'investment-notebook:last-export-reminder-dismissed';

export function shouldShowBackupReminder(lastExportedAt: string | undefined): boolean {
  const dismissedAt = localStorage.getItem(LAST_EXPORT_KEY);
  const dismissedRecently = dismissedAt && Date.now() - Number(dismissedAt) < 24 * 60 * 60 * 1000;
  if (dismissedRecently) return false;
  if (!lastExportedAt) return true;
  const days = (Date.now() - new Date(lastExportedAt).getTime()) / (1000 * 60 * 60 * 24);
  return days >= 7;
}

export function dismissBackupReminder() {
  localStorage.setItem(LAST_EXPORT_KEY, String(Date.now()));
}
