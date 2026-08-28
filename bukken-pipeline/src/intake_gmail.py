"""[M4 未実装] Gmail API から保存検索メールを取得し candidates 化する。

絶対制約: ポータルのWebページはスクレイピングしない。ここで読むのは
利用者本人の受信箱に届いたメールのみ（Gmail APIでOAuth認可の上、読み取る）。

- ラベル `bukken`（.env の GMAIL_LABEL）の新着メールを取得
- 本文HTMLから物件サマリ（価格/所在地/駅/徒歩/築年/面積/URL）を抽出
- ポータルごとに書式が違うため、ポータル別パーサを用意する
  （まず SUUMO・東急リバブルの2種。TODO: 他ポータル追加時はここにパーサを足す）
- 取れない項目は空でよい（後で手動補完）

TODO(M4):
  - get_gmail_service() -> googleapiclient.discovery.Resource （OAuthフロー、
    GMAIL_OAUTH_CLIENT_SECRET_PATH / GMAIL_TOKEN_PATH を使用）
  - list_label_messages(service, label: str) -> list[dict]
  - parse_suumo(html: str) -> dict
  - parse_livable(html: str) -> dict      # 東急リバブル
  - messages_to_candidates(messages) -> list[Candidate]  (intake_source="gmail:<portal>")
"""
from __future__ import annotations
