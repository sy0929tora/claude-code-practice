const jpy = new Intl.NumberFormat('ja-JP', {
  style: 'currency',
  currency: 'JPY',
  maximumFractionDigits: 0,
});

const jpyCompact = new Intl.NumberFormat('ja-JP', {
  style: 'currency',
  currency: 'JPY',
  notation: 'compact',
  maximumFractionDigits: 1,
});

export function formatJPY(value: number): string {
  if (!Number.isFinite(value)) return '¥0';
  return jpy.format(Math.round(value));
}

export function formatJPYCompact(value: number): string {
  if (!Number.isFinite(value)) return '¥0';
  return jpyCompact.format(value);
}

const numCompact = new Intl.NumberFormat('ja-JP', { notation: 'compact', maximumFractionDigits: 1 });

/** グラフの軸ラベルなど、通貨記号なしで短く表示したい場合に使う */
export function formatCompactNumber(value: number): string {
  if (!Number.isFinite(value)) return '0';
  return numCompact.format(value);
}

export function formatPercent(value: number, digits = 1): string {
  if (!Number.isFinite(value)) return '0%';
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatSigned(value: number, formatter: (v: number) => string = formatJPY): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatter(value)}`;
}

export function formatDate(iso: string | undefined): string {
  if (!iso) return '-';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export const TRACK_LABEL: Record<string, string> = {
  CORE: 'コア',
  DEFENSE: '守り',
  OFFENSE: '攻め',
};

export const ACCOUNT_TYPE_LABEL: Record<string, string> = {
  NISA_GROWTH: 'NISA成長投資枠',
  NISA_TSUMITATE: 'NISAつみたて投資枠',
  TAXABLE: '課税口座',
  SPOUSE: '世帯（配偶者）',
};

export const MARKET_LABEL: Record<string, string> = {
  JP: '国内',
  US: '米国',
};

export const VERDICT_LABEL: Record<string, string> = {
  ON_TRACK: '想定通り',
  OFF_TRACK: '想定と乖離',
  EXIT: '撤退',
};

export const DECISION_LABEL: Record<string, string> = {
  WATCH: '監視',
  PASS: '見送り',
  CONSIDER: '購入検討',
};
