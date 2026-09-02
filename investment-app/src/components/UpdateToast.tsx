import { useEffect } from 'react';
import { useRegisterSW } from 'virtual:pwa-register/react';

/**
 * PWAの新バージョンが利用可能になった時のみ表示する更新バナー。
 * 投資ノートはフォーム入力中のことが多いため、自動リロードはせず、
 * ユーザーが自分のタイミングで「更新する」を押した時だけリロードする。
 */
export function UpdateToast() {
  const {
    offlineReady: [offlineReady, setOfflineReady],
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(_url, registration) {
      // 1時間ごとに新バージョンがないか確認（開いたままにしている場合の取りこぼし防止）
      if (!registration) return;
      setInterval(() => registration.update(), 60 * 60 * 1000);
    },
  });

  // 「オフライン対応完了」は操作不要な通知なので数秒で自動的に消す。
  // （固定表示のままだと、画面下部にあるボタンをタップ判定が奪われてしまうのを防ぐ意図もある）
  useEffect(() => {
    if (!offlineReady) return;
    const timer = setTimeout(() => setOfflineReady(false), 4000);
    return () => clearTimeout(timer);
  }, [offlineReady, setOfflineReady]);

  if (!needRefresh && !offlineReady) return null;

  function close() {
    setOfflineReady(false);
    setNeedRefresh(false);
  }

  return (
    // 外側はpointer-events-noneにして、カード以外の透明な余白部分が
    // 下タブや画面下部のボタンのタップを奪わないようにする
    <div className="safe-bottom pointer-events-none fixed inset-x-0 bottom-16 z-40 mx-auto flex max-w-md justify-center px-4">
      <div className="pointer-events-auto flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-lg dark:border-slate-700 dark:bg-slate-800">
        <p className="text-[13px] font-medium text-slate-700 dark:text-slate-200">
          {needRefresh ? '新しいバージョンがあります' : 'オフラインでも使えるようになりました'}
        </p>
        <div className="flex shrink-0 items-center gap-2">
          {needRefresh && (
            <button
              onClick={() => updateServiceWorker(true)}
              className="rounded-lg bg-teal-600 px-3 py-1.5 text-[13px] font-semibold text-white active:bg-teal-700"
            >
              更新する
            </button>
          )}
          <button
            onClick={close}
            className="rounded-lg px-2 py-1.5 text-[13px] text-slate-400"
            aria-label="閉じる"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}
