import Dexie, { type EntityTable } from 'dexie';

// ---------------------------------------------------------------------------
// 型定義（design/investment-app-spec.md セクション7のデータモデルに準拠）
// ---------------------------------------------------------------------------

export type AccountType = 'NISA_GROWTH' | 'NISA_TSUMITATE' | 'TAXABLE' | 'SPOUSE';
export type Market = 'JP' | 'US';
export type Track = 'CORE' | 'DEFENSE' | 'OFFENSE';
export type TxType = 'BUY' | 'SELL' | 'DIVIDEND';
export type ThesisStatus = 'ACTIVE' | 'CLOSED';
export type ReviewVerdict = 'ON_TRACK' | 'OFF_TRACK' | 'EXIT';
export type CandidateDecision = 'WATCH' | 'PASS' | 'CONSIDER';

export interface Account {
  id?: number;
  name: string;
  type: AccountType;
  /** MVPは円建て統一。将来の多通貨対応に備えてフィールドのみ保持。 */
  currency: 'JPY' | 'USD';
}

export interface Holding {
  id?: number;
  accountId: number;
  ticker: string;
  name: string;
  market: Market;
  track: Track;
  shares: number;
  /** 平均取得単価（円建て） */
  avgCost: number;
  currency: 'JPY' | 'USD';
}

export interface Transaction {
  id?: number;
  holdingId: number;
  type: TxType;
  date: string; // ISO yyyy-mm-dd
  price: number;
  qty: number;
  fee: number;
  tax: number;
}

export interface Thesis {
  id?: number;
  holdingId?: number;
  candidateId?: number;
  whyBuy: string;
  bullCase: string;
  baseCase: string;
  bearCase: string;
  entryRationale: string;
  exitConditions: string;
  status: ThesisStatus;
  createdAt: string; // ISO datetime
}

export interface ThesisReview {
  id?: number;
  thesisId: number;
  earningsDate: string;
  note: string;
  verdict: ReviewVerdict;
  createdAt: string;
}

export interface Candidate {
  id?: number;
  ticker: string;
  name: string;
  market: Market;
  track: Track;
  decision: CandidateDecision;
}

export interface Scorecard {
  id?: number;
  holdingId?: number;
  candidateId?: number;
  track: Track;
  metricsJson: string;
  totalScore: number;
}

export interface PriceSnapshot {
  id?: number;
  ticker: string;
  price: number;
  date: string; // ISO yyyy-mm-dd
}

export interface HiringSignal {
  id?: number;
  sector: string;
  company?: string;
  observation: string;
  strength: 1 | 2 | 3 | 4 | 5;
  linkedCandidateId?: number;
  date: string;
}

export interface Goal {
  id?: number;
  targetAmount: number;
  monthlyContribution: number;
  assumedReturn: number; // 年率 %
  years: number;
}

export interface Lesson {
  id?: number;
  title: string;
  body: string;
  track?: Track;
  order: number;
}

export interface LearningProgress {
  id?: number;
  lessonId: number;
  completedAt?: string;
  quizScore?: number;
}

/** 設定（1銘柄あたり上限比率など、単一レコードのアプリ設定） */
export interface AppSettings {
  id?: number;
  maxPositionRatio: number; // 例: 0.2 = 20%
  lastExportedAt?: string;
}

// ---------------------------------------------------------------------------
// Dexie DB
// ---------------------------------------------------------------------------

class InvestmentDB extends Dexie {
  accounts!: EntityTable<Account, 'id'>;
  holdings!: EntityTable<Holding, 'id'>;
  transactions!: EntityTable<Transaction, 'id'>;
  theses!: EntityTable<Thesis, 'id'>;
  thesisReviews!: EntityTable<ThesisReview, 'id'>;
  candidates!: EntityTable<Candidate, 'id'>;
  scorecards!: EntityTable<Scorecard, 'id'>;
  priceSnapshots!: EntityTable<PriceSnapshot, 'id'>;
  hiringSignals!: EntityTable<HiringSignal, 'id'>;
  goals!: EntityTable<Goal, 'id'>;
  lessons!: EntityTable<Lesson, 'id'>;
  learningProgress!: EntityTable<LearningProgress, 'id'>;
  appSettings!: EntityTable<AppSettings, 'id'>;

  constructor() {
    super('investment-notebook');
    this.version(1).stores({
      accounts: '++id, type',
      holdings: '++id, accountId, ticker, track, market',
      transactions: '++id, holdingId, type, date',
      theses: '++id, holdingId, candidateId, status',
      thesisReviews: '++id, thesisId, earningsDate',
      candidates: '++id, ticker, track, decision',
      scorecards: '++id, holdingId, candidateId, track',
      priceSnapshots: '++id, ticker, date',
      hiringSignals: '++id, sector, date',
      goals: '++id',
      lessons: '++id, order, track',
      learningProgress: '++id, lessonId',
      appSettings: '++id',
    });
  }
}

export const db = new InvestmentDB();

/** 全テーブル名（エクスポート/インポートで使用） */
export const ALL_TABLES = [
  'accounts',
  'holdings',
  'transactions',
  'theses',
  'thesisReviews',
  'candidates',
  'scorecards',
  'priceSnapshots',
  'hiringSignals',
  'goals',
  'lessons',
  'learningProgress',
  'appSettings',
] as const;

export async function ensureDefaultSettings() {
  const count = await db.appSettings.count();
  if (count === 0) {
    await db.appSettings.add({ maxPositionRatio: 0.2 });
  }
}

export async function ensureDefaultGoal() {
  const count = await db.goals.count();
  if (count === 0) {
    await db.goals.add({
      targetAmount: 100_000_000,
      monthlyContribution: 200_000,
      assumedReturn: 5,
      years: 25,
    });
  }
}
