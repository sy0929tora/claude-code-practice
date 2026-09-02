import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { SelectField, TextField } from '../components/common/Field';
import { Button } from '../components/common/Button';
import { db, type AccountType } from '../db/db';
import { ACCOUNT_TYPE_LABEL } from '../lib/format';

const TYPES: AccountType[] = ['NISA_GROWTH', 'NISA_TSUMITATE', 'TAXABLE', 'SPOUSE'];

export default function AccountForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const existing = useLiveQuery(() => (id ? db.accounts.get(Number(id)) : undefined), [id]);

  const [name, setName] = useState('');
  const [type, setType] = useState<AccountType>('TAXABLE');
  const [initialized, setInitialized] = useState(false);

  if (existing && !initialized) {
    setName(existing.name);
    setType(existing.type);
    setInitialized(true);
  }

  async function handleSubmit() {
    if (!name.trim()) return;
    if (isEdit && id) {
      await db.accounts.update(Number(id), { name: name.trim(), type });
    } else {
      await db.accounts.add({ name: name.trim(), type, currency: 'JPY' });
    }
    navigate('/portfolio');
  }

  return (
    <div>
      <PageHeader title={isEdit ? '口座を編集' : '口座を追加'} back />
      <div className="space-y-4 px-4 py-4">
        <TextField
          label="口座名"
          placeholder="例：楽天証券 課税口座"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <SelectField label="種別" value={type} onChange={(e) => setType(e.target.value as AccountType)}>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {ACCOUNT_TYPE_LABEL[t]}
            </option>
          ))}
        </SelectField>
        <p className="text-[12px] text-slate-400">
          MVPは円建て統一のため、通貨は自動的に円（JPY）になります。
        </p>
        <Button className="w-full" disabled={!name.trim()} onClick={handleSubmit}>
          保存
        </Button>
      </div>
    </div>
  );
}
