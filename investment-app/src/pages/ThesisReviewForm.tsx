import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PageHeader } from '../components/layout/PageHeader';
import { DateField, SelectField, TextAreaField } from '../components/common/Field';
import { Button } from '../components/common/Button';
import { db, type ReviewVerdict } from '../db/db';
import { VERDICT_LABEL, todayISO } from '../lib/format';

export default function ThesisReviewForm() {
  const { id } = useParams();
  const thesisId = Number(id);
  const navigate = useNavigate();

  const [earningsDate, setEarningsDate] = useState(todayISO());
  const [note, setNote] = useState('');
  const [verdict, setVerdict] = useState<ReviewVerdict>('ON_TRACK');

  const valid = note.trim().length > 0;

  async function handleSubmit() {
    if (!valid) return;
    await db.thesisReviews.add({ thesisId, earningsDate, note, verdict, createdAt: new Date().toISOString() });
    if (verdict === 'EXIT') {
      await db.theses.update(thesisId, { status: 'CLOSED' });
    }
    navigate(`/notes/${thesisId}`);
  }

  return (
    <div>
      <PageHeader title="決算レビューを記録" back />
      <div className="space-y-4 px-4 py-4">
        <DateField label="決算日" value={earningsDate} onChange={(e) => setEarningsDate(e.target.value)} />
        <SelectField label="判定" value={verdict} onChange={(e) => setVerdict(e.target.value as ReviewVerdict)}>
          {(['ON_TRACK', 'OFF_TRACK', 'EXIT'] as const).map((v) => (
            <option key={v} value={v}>
              {VERDICT_LABEL[v]}
            </option>
          ))}
        </SelectField>
        <TextAreaField
          label="振り返りメモ"
          placeholder="買う前のシナリオと実際の決算を比べて、何が当たり・何が外れたか"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        {verdict === 'EXIT' && (
          <p className="text-[12px] text-amber-600 dark:text-amber-400">
            「撤退」を選ぶと、このノートは自動的にクローズ済みになります。
          </p>
        )}
        <Button className="w-full" disabled={!valid} onClick={handleSubmit}>
          保存
        </Button>
      </div>
    </div>
  );
}
