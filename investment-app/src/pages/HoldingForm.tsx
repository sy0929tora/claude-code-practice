import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { NumberField, SelectField, TextField } from '../components/common/Field';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { db, type Market, type Track } from '../db/db';
import { ACCOUNT_TYPE_LABEL, MARKET_LABEL, TRACK_LABEL } from '../lib/format';

export default function HoldingForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const accounts = useLiveQuery(() => db.accounts.toArray(), []);
  const existing = useLiveQuery(() => (id ? db.holdings.get(Number(id)) : undefined), [id]);

  const [accountId, setAccountId] = useState<number | ''>('');
  const [ticker, setTicker] = useState('');
  const [name, setName] = useState('');
  const [market, setMarket] = useState<Market>('JP');
  const [track, setTrack] = useState<Track>('CORE');
  const [shares, setShares] = useState('');
  const [avgCost, setAvgCost] = useState('');
  const [initialized, setInitialized] = useState(false);

  if (existing && !initialized) {
    setAccountId(existing.accountId);
    setTicker(existing.ticker);
    setName(existing.name);
    setMarket(existing.market);
    setTrack(existing.track);
    setShares(String(existing.shares));
    setAvgCost(String(existing.avgCost));
    setInitialized(true);
  }
  if (accounts && accounts.length > 0 && accountId === '' && !isEdit) {
    setAccountId(accounts[0].id!);
  }

  const valid = accountId !== '' && ticker.trim() && name.trim() && Number(shares) > 0 && Number(avgCost) >= 0;

  async function handleSubmit() {
    if (!valid) return;
    const payload = {
      accountId: Number(accountId),
      ticker: ticker.trim().toUpperCase(),
      name: name.trim(),
      market,
      track,
      shares: Number(shares),
      avgCost: Number(avgCost),
      currency: 'JPY' as const,
    };
    if (isEdit && id) {
      await db.holdings.update(Number(id), payload);
      navigate(`/portfolio/holdings/${id}`);
    } else {
      const newId = await db.holdings.add(payload);
      navigate(`/portfolio/holdings/${newId}`);
    }
  }

  if (accounts && accounts.length === 0) {
    return (
      <div>
        <PageHeader title="銘柄を追加" back />
        <div className="px-4 py-6">
          <EmptyState title="先に口座を登録してください" description="銘柄はいずれかの口座に紐づけて登録します。" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={isEdit ? '銘柄を編集' : '銘柄を追加'} back />
      <div className="space-y-4 px-4 py-4">
        <SelectField label="口座" value={accountId} onChange={(e) => setAccountId(Number(e.target.value))}>
          {accounts?.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}（{ACCOUNT_TYPE_LABEL[a.type]}）
            </option>
          ))}
        </SelectField>
        <TextField
          label="ティッカー・コード"
          placeholder="例：VOO / 2914 / eMAXIS Slim S&P500"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
        />
        <TextField label="銘柄名" placeholder="例：バンガードS&P500 ETF" value={name} onChange={(e) => setName(e.target.value)} />
        <div className="grid grid-cols-2 gap-3">
          <SelectField label="市場" value={market} onChange={(e) => setMarket(e.target.value as Market)}>
            {(['JP', 'US'] as const).map((m) => (
              <option key={m} value={m}>
                {MARKET_LABEL[m]}
              </option>
            ))}
          </SelectField>
          <SelectField label="トラック" value={track} onChange={(e) => setTrack(e.target.value as Track)}>
            {(['CORE', 'DEFENSE', 'OFFENSE'] as const).map((t) => (
              <option key={t} value={t}>
                {TRACK_LABEL[t]}
              </option>
            ))}
          </SelectField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <NumberField label="保有数量" placeholder="100" value={shares} onChange={(e) => setShares(e.target.value)} />
          <NumberField
            label="平均取得単価"
            hint="円"
            placeholder="5000"
            value={avgCost}
            onChange={(e) => setAvgCost(e.target.value)}
          />
        </div>
        <p className="text-[12px] text-slate-400">
          取引履歴がなくても、今の保有数量と平均取得単価だけで登録できます。履歴は後から追加可能です。
        </p>
        <Button className="w-full" disabled={!valid} onClick={handleSubmit}>
          保存
        </Button>
      </div>
    </div>
  );
}
