import { ALL_TABLES, db } from '../db/db';

export interface ExportPayload {
  app: 'investment-notebook';
  version: 1;
  exportedAt: string;
  data: Record<string, unknown[]>;
}

export async function exportAllData(): Promise<ExportPayload> {
  const data: Record<string, unknown[]> = {};
  for (const table of ALL_TABLES) {
    data[table] = await db.table(table).toArray();
  }
  return {
    app: 'investment-notebook',
    version: 1,
    exportedAt: new Date().toISOString(),
    data,
  };
}

export function downloadExport(payload: ExportPayload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const stamp = payload.exportedAt.slice(0, 10);
  a.href = url;
  a.download = `investment-notebook-backup-${stamp}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function exportAndDownload() {
  const payload = await exportAllData();
  downloadExport(payload);
  const settings = await db.appSettings.toCollection().first();
  if (settings?.id) {
    await db.appSettings.update(settings.id, { lastExportedAt: payload.exportedAt });
  }
  return payload;
}

export class ImportValidationError extends Error {}

export async function importAllData(json: unknown, mode: 'replace' | 'merge' = 'replace') {
  if (typeof json !== 'object' || json === null) {
    throw new ImportValidationError('不正なファイル形式です');
  }
  const payload = json as Partial<ExportPayload>;
  if (payload.app !== 'investment-notebook' || !payload.data) {
    throw new ImportValidationError('このアプリのバックアップファイルではありません');
  }

  await db.transaction('rw', db.tables, async () => {
    for (const table of ALL_TABLES) {
      const rows = payload.data?.[table];
      if (!Array.isArray(rows)) continue;
      if (mode === 'replace') {
        await db.table(table).clear();
      }
      if (rows.length > 0) {
        await db.table(table).bulkPut(rows);
      }
    }
  });
}

export function readFileAsJSON(file: File): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        resolve(JSON.parse(String(reader.result)));
      } catch {
        reject(new ImportValidationError('JSONの解析に失敗しました'));
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file, 'utf-8');
  });
}
