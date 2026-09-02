import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      // 'autoUpdate' は新しいService Workerが有効化されると自動でページをリロードする。
      // 投資ノートはフォーム入力中のことが多く、入力内容が消えてしまうため 'prompt' にして
      // ユーザーが自分のタイミングで更新できるようにする（UpdateToast コンポーネント参照）。
      registerType: 'prompt',
      includeAssets: ['icons/*.png', 'splash/*.png'],
      manifest: {
        id: '/',
        name: '投資ノート',
        short_name: '投資ノート',
        description: 'コア・サテライト戦略を学びながら管理する、あなた専用の投資ノート',
        start_url: '.',
        scope: '.',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#0f172a',
        theme_color: '#0f172a',
        lang: 'ja',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,png,svg,ico,woff2}'],
        // データはIndexedDB側で管理するのでAPI通信のキャッシュ戦略は不要（外部通信なし）
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
});
