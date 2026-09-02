import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { Card, CardTitle } from '../components/common/Card';
import { NumberField, TextAreaField, TextField, DateField } from '../components/common/Field';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { db } from '../db/db';
import { formatDate, todayISO } from '../lib/format';

export default function Learn() {
  const signals = useLiveQuery(
    () => db.hiringSignals.toArray().then((rows) => rows.sort((a, b) => b.date.localeCompare(a.date))),
    [],
  );

  const [sector, setSector] = useState('');
  const [company, setCompany] = useState('');
  const [observation, setObservation] = useState('');
  const [strength, setStrength] = useState('3');
  const [date, setDate] = useState(todayISO());

  const valid = sector.trim().length > 0 && observation.trim().length > 0;

  async function handleAdd() {
    if (!valid) return;
    await db.hiringSignals.add({
      sector: sector.trim(),
      company: company.trim() || undefined,
      observation: observation.trim(),
      strength: Number(strength) as 1 | 2 | 3 | 4 | 5,
      date,
    });
    setSector('');
    setCompany('');
    setObservation('');
    setStrength('3');
  }

  return (
    <div>
      <PageHeader title="学ぶ" />
      <div className="space-y-4 px-4 py-4">
        <Card>
          <CardTitle>採用シグナル・ボード</CardTitle>
          <p className="mb-3 text-[13px] text-slate-500 dark:text-slate-400">
            IT×人材の仕事で得た「この領域は採用が増えている＝伸びている」という一次情報を、投資アイデアの種として書き残します。
          </p>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <TextField label="領域・業界" placeholder="例：生成AIインフラ" value={sector} onChange={(e) => setSector(e.target.value)} />
              <TextField label="関連企業（任意）" placeholder="例：〇〇株式会社" value={company} onChange={(e) => setCompany(e.target.value)} />
            </div>
            <TextAreaField
              label="観察内容"
              placeholder="求人数・求人内容の変化、報酬水準、応募状況など"
              value={observation}
              onChange={(e) => setObservation(e.target.value)}
            />
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="シグナルの強さ" hint="1〜5" min={1} max={5} value={strength} onChange={(e) => setStrength(e.target.value)} />
              <DateField label="日付" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <Button className="w-full" disabled={!valid} onClick={handleAdd}>
              記録する
            </Button>
          </div>
        </Card>

        <div>
          <h2 className="mb-1.5 px-1 text-[13px] font-bold text-slate-500 dark:text-slate-400">記録一覧</h2>
          {!signals || signals.length === 0 ? (
            <EmptyState title="まだ記録がありません" />
          ) : (
            <div className="space-y-2">
              {signals.map((s) => (
                <Card key={s.id}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-slate-50">{s.sector}</span>
                    <span className="text-[11px] text-slate-400">{formatDate(s.date)}</span>
                  </div>
                  {s.company && <div className="mb-1 text-[12px] text-slate-400">{s.company}</div>}
                  <p className="text-[13px] text-slate-600 dark:text-slate-300">{s.observation}</p>
                  <div className="mt-1 text-[11px] text-amber-500">{'★'.repeat(s.strength)}{'☆'.repeat(5 - s.strength)}</div>
                </Card>
              ))}
            </div>
          )}
        </div>

        <Card className="border-dashed">
          <CardTitle>今後追加予定（Phase 3）</CardTitle>
          <ul className="list-disc space-y-1 pl-4 text-[13px] text-slate-500 dark:text-slate-400">
            <li>指標解説・ノート添削・決算サマリーを、最適なプロンプトとしてコピーしてClaudeアプリに貼るだけで使える機能</li>
            <li>直近で扱った内容からのクイズ出題</li>
            <li>レッスン・用語集</li>
          </ul>
          <p className="mt-2 text-[12px] text-slate-400">
            API課金なしで使えるよう、あえてコピー&ペースト方式で設計する予定です。
          </p>
        </Card>
      </div>
    </div>
  );
}
