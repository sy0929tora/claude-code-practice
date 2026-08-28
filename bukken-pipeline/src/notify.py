"""[M5 未実装] 高得点の新着候補を通知する（任意機能）。

前回実行時の output と今回の output を比較し、新規に上位入りした候補（例:
総合スコアが閾値以上、かつ前回未出現）をメール/LINE等で通知する想定。

TODO(M5):
  - load_previous_output(path) -> list[ScoredCandidate] | None
  - diff_new_high_scorers(previous, current, threshold: float) -> list[ScoredCandidate]
  - notify_email(candidates, to: str) / notify_line(candidates, token: str)
  - .env: NOTIFY_EMAIL_TO / LINE_NOTIFY_TOKEN を使用
"""
from __future__ import annotations
