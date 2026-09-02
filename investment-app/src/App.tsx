import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import HoldingDetail from './pages/HoldingDetail';
import HoldingForm from './pages/HoldingForm';
import AccountForm from './pages/AccountForm';
import TransactionForm from './pages/TransactionForm';
import PriceUpdate from './pages/PriceUpdate';
import Notes from './pages/Notes';
import ThesisForm from './pages/ThesisForm';
import ThesisDetail from './pages/ThesisDetail';
import ThesisReviewForm from './pages/ThesisReviewForm';
import Learn from './pages/Learn';
import Settings from './pages/Settings';

// グラフ描画（recharts）はバンドルが大きいため、シミュレーター画面のみ遅延読み込みする
const Simulator = lazy(() => import('./pages/Simulator'));

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Dashboard />} />

        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/portfolio/accounts/new" element={<AccountForm />} />
        <Route path="/portfolio/accounts/:id/edit" element={<AccountForm />} />
        <Route path="/portfolio/holdings/new" element={<HoldingForm />} />
        <Route path="/portfolio/holdings/:id" element={<HoldingDetail />} />
        <Route path="/portfolio/holdings/:id/edit" element={<HoldingForm />} />
        <Route path="/portfolio/holdings/:id/transactions/new" element={<TransactionForm />} />
        <Route path="/portfolio/prices" element={<PriceUpdate />} />

        <Route path="/notes" element={<Notes />} />
        <Route path="/notes/new" element={<ThesisForm />} />
        <Route path="/notes/:id" element={<ThesisDetail />} />
        <Route path="/notes/:id/edit" element={<ThesisForm />} />
        <Route path="/notes/:id/reviews/new" element={<ThesisReviewForm />} />

        <Route
          path="/simulator"
          element={
            <Suspense fallback={<div className="px-4 py-6 text-center text-sm text-slate-400">読み込み中…</div>}>
              <Simulator />
            </Suspense>
          }
        />
        <Route path="/learn" element={<Learn />} />
        <Route path="/settings" element={<Settings />} />

        <Route path="*" element={<Dashboard />} />
      </Routes>
    </AppShell>
  );
}
