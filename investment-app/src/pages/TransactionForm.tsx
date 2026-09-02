import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { DateField, NumberField, SelectField } from '../components/common/Field';
import { Button } from '../components/common/Button';
import { db, type TxType } from '../db/db';
import { todayISO } from '../lib/format';

export default function TransactionForm() {
  const { id: holdingIdParam } = useParams();
  const holdingId = Number(holdingIdParam);
  const navigate = useNavigate();
  const holding = useLiveQuery(() => db.holdings.get(holdingId), [holdingId]);

  const [type, setType] = useState<TxType>('BUY');
  const [date, setDate] = useState(todayISO());
  const [price, setPrice] = useState('');
  const [qty, setQty] = useState('');
  const [fee, setFee] = useState('0');
  const [tax, setTax] = useState('0');

  const isDividend = type === 'DIVIDEND';
  const valid = date && Number(price) >= 0 && (isDividend || Number(qty) > 0);

  async function handleSubmit() {
    if (!valid) return;
    await db.transactions.add({
      holdingId,
      type,
      date,
      price: Number(price),
      qty: isDividend ? 0 : Number(qty),
      fee: Number(fee) || 0,
      tax: Number(tax) || 0,
    });
    navigate(`/portfolio/holdings/${holdingId}`);
  }

  return (
    <div>
      <PageHeader title={`取引を記録${holding ? `（${holding.name}）` : ''}`} back />
      <div className="space-y-4 px-4 py-4">
        <SelectField label="種別" value={type} onChange={(e) => setType(e.target.value as TxType)}>
          <option value="BUY">買い</option>
          <option value="SELL">売り</option>
          <option value="DIVIDEND">配当</option>
        </SelectField>
        <DateField label="日付" value={date} onChange={(e) => setDate(e.target.value)} />
        <div className="grid grid-cols-2 gap-3">
          <NumberField
            label={isDividend ? '受取配当金額' : '単価'}
            hint="円"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
          {!isDividend && (
            <NumberField label="数量" value={qty} onChange={(e) => setQty(e.target.value)} />
          )}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <NumberField label="手数料" hint="円" value={fee} onChange={(e) => setFee(e.target.value)} />
          <NumberField label="税額" hint="円" value={tax} onChange={(e) => setTax(e.target.value)} />
        </div>
        {isDividend && (
          <p className="text-[12px] text-slate-400">
            課税口座の場合、税引前の受取額を入力してください（概算税率 約20.315%として手取りを試算します）。
          </p>
        )}
        <Button className="w-full" disabled={!valid} onClick={handleSubmit}>
          保存
        </Button>
      </div>
    </div>
  );
}
