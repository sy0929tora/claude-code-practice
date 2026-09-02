import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/layout/PageHeader';
import { Card, CardTitle } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { NumberField } from '../components/common/Field';
import { Alert } from '../components/common/Alert';
import { db } from '../db/db';
import { useAccounts, useAppSettings } from '../hooks/usePortfolio';
import { ACCOUNT_TYPE_LABEL, formatDate } from '../lib/format';
import { exportAndDownload, importAllData, readFileAsJSON, ImportValidationError } from '../lib/exportImport';
import { getStoredTheme, setTheme, type ThemeMode } from '../lib/theme';
import { CheckIcon, TrashIcon } from '../components/icons';

export default function Settings() {
  const accounts = useAccounts();
  const settings = useAppSettings();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [ratioDraft, setRatioDraft] = useState<string | null>(null);
  const [ratioSaved, setRatioSaved] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [theme, setThemeState] = useState<ThemeMode>(getStoredTheme());

  async function handleDeleteAccount(id: number, name: string) {
    if (!confirm(`口座「${name}」を削除しますか？この口座の銘柄・ノート・取引記録もすべて削除されます。`)) return;
    await db.transaction('rw', db.tables, async () => {
      const holdings = await db.holdings.where({ accountId: id }).toArray();
      for (const h of holdings) {
        if (!h.id) continue;
        const theses = await db.theses.where({ holdingId: h.id }).toArray();
        for (const t of theses) {
          if (t.id) await db.thesisReviews.where({ thesisId: t.id }).delete();
        }
        await db.theses.where({ holdingId: h.id }).delete();
        await db.transactions.where({ holdingId: h.id }).delete();
      }
      await db.holdings.where({ accountId: id }).delete();
      await db.accounts.delete(id);
    });
  }

  async function saveRatio() {
    if (!settings?.id || ratioDraft === null) return;
    const pct = Number(ratioDraft);
    if (!Number.isFinite(pct) || pct <= 0) return;
    await db.appSettings.update(settings.id, { maxPositionRatio: pct / 100 });
    setRatioSaved(true);
    setTimeout(() => setRatioSaved(false), 1500);
  }

  async function handleExport() {
    await exportAndDownload();
    setExportMsg('バックアップファイルをダウンロードしました。iCloud Driveなど分かりやすい場所に保存してください。');
    setTimeout(() => setExportMsg(null), 4000);
  }

  async function handleImportFile(file: File) {
    setImportError(null);
    setImportMsg(null);
    try {
      const json = await readFileAsJSON(file);
      if (!confirm('現在のデータをすべて置き換えてインポートします。よろしいですか？')) return;
      await importAllData(json, 'replace');
      setImportMsg('インポートが完了しました。');
    } catch (e) {
      setImportError(e instanceof ImportValidationError ? e.message : 'インポートに失敗しました。');
    }
  }

  return (
    <div>
      <PageHeader title="設定" />
      <div className="space-y-4 px-4 py-4">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <CardTitle className="mb-0">口座</CardTitle>
            <Link to="/portfolio/accounts/new" className="text-[13px] font-semibold text-teal-600 dark:text-teal-400">
              追加
            </Link>
          </div>
          {accounts && accounts.length > 0 ? (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {accounts.map((a) => (
                <div key={a.id} className="flex items-center justify-between py-2">
                  <div>
                    <div className="text-[14px] font-semibold text-slate-800 dark:text-slate-100">{a.name}</div>
                    <div className="text-[12px] text-slate-400">{ACCOUNT_TYPE_LABEL[a.type]}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Link to={`/portfolio/accounts/${a.id}/edit`} className="text-[12px] font-semibold text-teal-600 dark:text-teal-400">
                      編集
                    </Link>
                    <button onClick={() => a.id && handleDeleteAccount(a.id, a.name)} aria-label="削除">
                      <TrashIcon className="h-4 w-4 text-rose-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[13px] text-slate-400">口座が未登録です。</p>
          )}
        </Card>

        <Card>
          <CardTitle>リスク・ガードレール</CardTitle>
          <NumberField
            label="1銘柄あたりの上限比率"
            hint="% ・ 総資産に対する比率"
            placeholder={settings ? String(Math.round(settings.maxPositionRatio * 100)) : ''}
            value={ratioDraft ?? (settings ? String(Math.round(settings.maxPositionRatio * 100)) : '')}
            onChange={(e) => setRatioDraft(e.target.value)}
          />
          <p className="mt-1.5 text-[12px] text-slate-400">
            超過するとポートフォリオ画面で警告バッジが表示されます。
          </p>
          <Button variant={ratioSaved ? 'secondary' : 'primary'} className="mt-3 w-full" onClick={saveRatio}>
            {ratioSaved ? '保存しました' : '保存'}
          </Button>
        </Card>

        <Link to="/simulator">
          <Card className="active:bg-slate-50 dark:active:bg-slate-800">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800 dark:text-slate-100">億り人シミュレーターの前提条件</span>
              <span className="text-[13px] text-teal-600 dark:text-teal-400">開く →</span>
            </div>
          </Card>
        </Link>

        <Card>
          <CardTitle>表示テーマ</CardTitle>
          <div className="flex gap-2">
            {(['system', 'light', 'dark'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => {
                  setTheme(mode);
                  setThemeState(mode);
                }}
                className={`flex-1 rounded-xl border py-2 text-[13px] font-semibold ${
                  theme === mode
                    ? 'border-teal-500 bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300'
                    : 'border-slate-200 text-slate-500 dark:border-slate-700 dark:text-slate-400'
                }`}
              >
                {mode === 'system' ? '端末に合わせる' : mode === 'light' ? 'ライト' : 'ダーク'}
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <CardTitle>バックアップ（エクスポート / インポート）</CardTitle>
          <p className="mb-3 text-[13px] text-slate-500 dark:text-slate-400">
            データはこの端末のIndexedDBにのみ保存されます。iOSは長期間未使用の場合などにデータを消去することがあるため、
            週1回を目安にJSONを書き出し、iCloud Driveなど端末外にも保存することを強くおすすめします。
          </p>
          {settings?.lastExportedAt && (
            <p className="mb-3 text-[12px] text-slate-400">前回のバックアップ: {formatDate(settings.lastExportedAt)}</p>
          )}
          <div className="flex gap-2">
            <Button className="flex-1" onClick={handleExport}>
              JSONを書き出す
            </Button>
            <Button variant="secondary" className="flex-1" onClick={() => fileInputRef.current?.click()}>
              JSONを読み込む
            </Button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleImportFile(file);
              e.target.value = '';
            }}
          />
          {exportMsg && (
            <Alert tone="info">
              <span className="flex items-center gap-1">
                <CheckIcon className="h-4 w-4" /> {exportMsg}
              </span>
            </Alert>
          )}
          {importMsg && (
            <div className="mt-2">
              <Alert tone="info">{importMsg}</Alert>
            </div>
          )}
          {importError && (
            <div className="mt-2">
              <Alert tone="danger">{importError}</Alert>
            </div>
          )}
        </Card>

        <InstallGuideCard />

        <p className="px-1 text-center text-[11px] text-slate-300 dark:text-slate-600">
          投資ノート ・ データは常にこの端末内のみに保存されます
        </p>
      </div>
    </div>
  );
}

function InstallGuideCard() {
  const isStandalone =
    typeof window !== 'undefined' &&
    (window.matchMedia?.('(display-mode: standalone)').matches || (window.navigator as { standalone?: boolean }).standalone);

  if (isStandalone) return null;

  return (
    <Card>
      <CardTitle>ホーム画面に追加する</CardTitle>
      <ol className="list-decimal space-y-1.5 pl-4 text-[13px] text-slate-600 dark:text-slate-300">
        <li>Safariの下部にある「共有」ボタン（□に↑のアイコン）をタップ</li>
        <li>メニューから「ホーム画面に追加」を選択</li>
        <li>右上の「追加」をタップ</li>
      </ol>
      <p className="mt-2 text-[12px] text-slate-400">
        ホーム画面のアイコンから起動すると、ネイティブアプリのように全画面で使えます。
      </p>
    </Card>
  );
}
