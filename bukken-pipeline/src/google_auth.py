"""Gmail / Sheets 共通の Google OAuth ヘルパー。

デスクトップアプリ用 OAuthクライアント（.envの GMAIL_OAUTH_CLIENT_SECRET_PATH）を
使い、初回はブラウザでユーザー本人が認可し、トークンを GMAIL_TOKEN_PATH に保存する。
2回目以降はそのトークンを使い回す（期限切れ時は自動リフレッシュ）。

Gmail読み取り・送信、Sheets書き込みで別々にトークンファイルを持つと管理が煩雑なため、
必要なscopeをすべて一つのトークンに含めて認可する設計にしている
（scopeを追加した場合はトークンファイルを一度削除して再認可が必要）。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

# Gmail読み取り・送信・Sheets書き込みをまとめて1トークンで扱う。
# notify.py がメール送信するために gmail.send も含む。
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials(scopes: Sequence[str] = DEFAULT_SCOPES):
    """OAuth2 Credentials を返す。未認可なら初回のみブラウザ認可フローを起動する。

    必要な環境変数（.env）:
      GMAIL_OAUTH_CLIENT_SECRET_PATH: GCPでダウンロードしたOAuthクライアントのjson
      GMAIL_TOKEN_PATH: 認可後のトークン保存先（.gitignore対象）
    """
    # 遅延importにして、このモジュールを読み込むだけならgoogle-authが未インストールでも
    # score.py 等のコア機能に影響しないようにする。
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_secret_path = os.environ.get(
        "GMAIL_OAUTH_CLIENT_SECRET_PATH", "./secrets/gmail_client_secret.json"
    )
    token_path = Path(os.environ.get("GMAIL_TOKEN_PATH", "./secrets/gmail_token.json"))

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(client_secret_path).exists():
                raise FileNotFoundError(
                    f"OAuthクライアントのjsonが見つかりません: {client_secret_path}\n"
                    "GCPコンソールでOAuthクライアントID(デスクトップアプリ)を作成し、"
                    ".envのGMAIL_OAUTH_CLIENT_SECRET_PATHにパスを設定してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds
