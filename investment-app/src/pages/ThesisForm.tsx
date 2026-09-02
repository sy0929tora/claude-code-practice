import { useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { PageHeader } from '../components/layout/PageHeader';
import { TextAreaField } from '../components/common/Field';
import { Button } from '../components/common/Button';
import { db } from '../db/db';

export default function ThesisForm() {
  const { id } = useParams(); // thesis id when editing
  const [searchParams] = useSearchParams();
  const holdingIdParam = searchParams.get('holdingId');
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const holding = useLiveQuery(
    () => (holdingIdParam ? db.holdings.get(Number(holdingIdParam)) : undefined),
    [holdingIdParam],
  );
  const existing = useLiveQuery(() => (id ? db.theses.get(Number(id)) : undefined), [id]);

  const [whyBuy, setWhyBuy] = useState('');
  const [bullCase, setBullCase] = useState('');
  const [baseCase, setBaseCase] = useState('');
  const [bearCase, setBearCase] = useState('');
  const [entryRationale, setEntryRationale] = useState('');
  const [exitConditions, setExitConditions] = useState('');
  const [initialized, setInitialized] = useState(false);

  if (existing && !initialized) {
    setWhyBuy(existing.whyBuy);
    setBullCase(existing.bullCase);
    setBaseCase(existing.baseCase);
    setBearCase(existing.bearCase);
    setEntryRationale(existing.entryRationale);
    setExitConditions(existing.exitConditions);
    setInitialized(true);
  }

  const valid = whyBuy.trim().length > 0 && exitConditions.trim().length > 0;

  async function handleSubmit() {
    if (!valid) return;
    const payload = { whyBuy, bullCase, baseCase, bearCase, entryRationale, exitConditions };
    if (isEdit && id) {
      await db.theses.update(Number(id), payload);
      navigate(`/notes/${id}`);
    } else {
      const newId = await db.theses.add({
        ...payload,
        holdingId: holdingIdParam ? Number(holdingIdParam) : undefined,
        status: 'ACTIVE',
        createdAt: new Date().toISOString(),
      });
      navigate(`/notes/${newId}`);
    }
  }

  return (
    <div>
      <PageHeader title={isEdit ? 'ノートを編集' : `ノートを書く${holding ? `（${holding.name}）` : ''}`} back />
      <div className="space-y-4 px-4 py-4">
        <TextAreaField
          label="① なぜ買うか"
          placeholder="この銘柄に投資する理由。あなたの一次情報（採用動向など）も含めて。"
          value={whyBuy}
          onChange={(e) => setWhyBuy(e.target.value)}
        />
        <TextAreaField
          label="② シナリオ - 強気"
          placeholder="うまくいけばどうなるか"
          value={bullCase}
          onChange={(e) => setBullCase(e.target.value)}
        />
        <TextAreaField
          label="② シナリオ - 基本"
          placeholder="最も蓋然性が高いシナリオ"
          value={baseCase}
          onChange={(e) => setBaseCase(e.target.value)}
        />
        <TextAreaField
          label="② シナリオ - 弱気"
          placeholder="外れた場合、何が起きるか"
          value={bearCase}
          onChange={(e) => setBearCase(e.target.value)}
        />
        <TextAreaField
          label="③ エントリー根拠"
          placeholder="なぜ今のタイミング・この値段で買うのか"
          value={entryRationale}
          onChange={(e) => setEntryRationale(e.target.value)}
        />
        <TextAreaField
          label="④ 撤退条件"
          placeholder="どうなったら手放すか。数値・事実で書く（例：営業利益率が2四半期連続で悪化したら撤退）"
          value={exitConditions}
          onChange={(e) => setExitConditions(e.target.value)}
        />
        <Button className="w-full" disabled={!valid} onClick={handleSubmit}>
          保存
        </Button>
      </div>
    </div>
  );
}
