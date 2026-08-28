# bukken-pipeline

住宅購入（戸建）の物件探しを支援する、ローカルで動く再実行可能な採点パイプライン。
「ポータルの保存検索メール」または「手動入力」で集めた候補を、相場・ハザード・
二拠点通勤（横浜駅／高田馬場駅）で自動採点し、順位付けして `output.xlsx`（任意でGoogle Sheets）に出す。

このツールは**物件を探すこと自体は自動化しない**。判断（採点・順位付け）を
自動化するのが役割。網羅的な物件収集や、不動産ポータルのスクレイピングは行わない。

## 現在の実装状況（マイルストーン）

- [x] **M1** 手動CSV入力 → 採点 → `output.xlsx`
- [x] **M2** 国土地理院ジオコーディング + 不動産情報ライブラリ（相場・ハザード自動更新）
- [x] **M3** Google Maps Routes API（横浜・高田馬場の実測通勤時間）
- [x] **M4** Gmail API（保存検索メールからの自動intake、SUUMO・東急リバブル対応）
- [x] **M5** Google Sheets出力 + メール通知 + 毎朝自動実行（GitHub Actions）

全マイルストーン実装済みだが、**M2/M3/M4は「実APIへの到達を伴う検証」ができていない**
（下記「検証状況について」を必ず読んでから使うこと）。

## 検証状況について（重要）

このツールを構築した開発環境は、ネットワークポリシー上 reinfolib.mlit.go.jp /
msearch.gsi.go.jp / maps.googleapis.com 等の外部APIに到達できない（社内プロキシで
ブロックされる）。そのため各enrichモジュールは:

- **単体テスト**（`tests/test_enrich.py` 等）で、公開ドキュメント・実装解説記事から
  判明したレスポンス形式を模したモックに対して正しく解釈できることを確認済み。
- **失敗時のフォールバック経路**は実際にAPIキー無し/到達不能な状態で`run.py`を
  実行し、エラーを握りつぶさずログに警告を出しつつ、M1のseedベースのスコアが
  変わらず出力されることを確認済み（`python run.py --geocode --reinfolib --commute -v`）。
- 一方で、**実際のAPIレスポンスに対する「ハッピーパス」の動作は未検証**。特に以下は
  実キーを入手した利用者が最初の1回、必ず手元で確認してほしい:
  - `enrich_reinfolib.py`: XIT001のレスポンスの実際のキー名（`TradePrice`/`Area`/
    `NearestStation`/`Type`等）、ハザード・用途地域タイルAPIのID（`XKT026`/`XKT002`と
    推定）とプロパティ構造。ズレていればコード内のTODOコメント箇所を修正する。
  - `intake_gmail.py`: SUUMO・東急リバブルの実際の保存検索通知メールのHTML構造。
    正規表現ベースの抽出は一般的なメールテンプレートを仮定した推測実装であり、
    実メールで抽出漏れがあれば調整が要る（抽出できなかった項目は空のまま
    candidatesに入るので、パイプライン自体は壊れない）。

これは「動くはずのコードを書いたが実地検証は利用者側に委ねる」という意図的な
判断であり、時間をかけて未確認のまま「検証済み」と偽ることを避けるため。

## 絶対制約（この方針は変えない）

- **不動産ポータル（SUUMO / at home / LIFULL HOME'S 等）のWebページはスクレイピングしない。**
  各社の利用規約で原則禁止されており、bot対策で不安定なため。
- 物件情報の入力は次の2経路のみ。
  1. 利用者本人宛に届いた「保存検索」の通知メール（Gmail APIで自分の受信箱を読む＝合法）
  2. 手動入力（CSV。`data/candidates.csv` 参照）
- 相場・地価・ハザード・用途地域・通勤時間は公的/公式APIのみから取得する（下記参照）。
- APIキー・トークンは `.env`（`python-dotenv`）で管理し、**リポジトリにコミットしない**。
- パイプラインは冪等。同じ入力で何度実行しても壊れず、住所+価格でdedupeする。
- 出典が公的データの数値は、出力（`output.xlsx`の「相場出典」列など）に出典を残す。

## リポジトリの置き場所について（要検討事項）

このリポジトリ（`ailabo-inc.github.io`）は会社の公開GitHub Pagesサイトであり、
`data/candidates.csv` に入れる物件データはこのリポジトリの通常運用と同じく
**公開される**（`investment-alert-tool` 等、既存の個人ツールもここに置かれている
前例に倣った）。依頼書§8のサンプル5件は既にコミット済み。今後、実際に検討中の
物件の住所・価格などをここに書き込むと、それも公開リポジトリの履歴に残る点は
把握しておいてほしい。`data/output.xlsx` や `.env`、`secrets/` はコミット対象外に
してあるが、`data/candidates.csv` 自体はコミット対象なので、非公開にしたいデータは
このファイルに書かず、別途プライベートな場所（プライベートリポジトリやローカルのみ）
で運用することを推奨する。GitHub Actions（M5）のoutputはコミットではなく
ワークフローのArtifact（リポジトリの読み取り権限を持つ人だけが見られる）として
保存する設計にし、この点は配慮している。

## セットアップ

```bash
cd bukken-pipeline
python3 -m venv .venv
source .venv/bin/activate      # Windowsは .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # M1相当の動作はキー未設定でもOK
```

## 実行方法

```bash
# M1相当: CSV → 採点 → xlsx（APIキー不要）
python run.py --input data/candidates.csv --output data/output.xlsx

# フル機能（Gmail取り込み＋ジオコーディング＋相場/ハザード更新＋通勤実測＋Sheets出力＋通知）
python run.py --all

# 個別に有効化も可能
python run.py --geocode --reinfolib --commute
python run.py --gmail
python run.py --sheets
python run.py --notify
```

どのAPIも未設定・失敗時はログに警告を出し、seed値/スキップにフォールバックする
（パイプライン全体は止めない）。`-v`でデバッグログを表示できる。

`data/candidates.csv` の列:

| 列 | 説明 |
|---|---|
| id | 任意の識別子（空でも可） |
| name | 物件名・所在地の呼称 |
| station | 最寄駅（`config/reference_land.csv` / `reference_commute.csv` のキーと一致させる） |
| walk_min | 駅徒歩分 |
| price_man | 価格（万円） |
| land_sqm | 土地面積（㎡） |
| bldg_sqm | 建物面積（㎡） |
| layout | 間取り |
| built_year | 築年（西暦。新築は入居予定年） |
| zoning | 用途地域（任意。M2で自動補完可） |
| corner | 角地フラグ 0/1（現状スコアには未加点。下記「角地加点について」参照） |
| hazard_0_3 | ハザード懸念度 0(なし)〜3(強)。手動入力が優先され、0のままならM2で自動判定を試みる |
| redflag_0_3 | 資産性の赤信号（敷地面積最低限度・大きな2項道路セットバック等）0〜3。自動判定は無し（現地・重説で確認） |

`config/reference_land.csv`・`config/reference_commute.csv` はAPIが未設定/失敗のときの
フォールバック値（seed）。`--reinfolib`実行時、取得できた駅は`reference_land.csv`が
実データで上書きされる（取得できなかった駅はseedのまま残る）。通勤は
Candidate側に実測値が入るだけで、seedファイル自体は書き換えない。

### 角地加点について（設計判断）

依頼書§3は「所有権・整形地・角地を加点」としているが、§6のスコア数式には
角地を加点する項が定義されていない。**このツールは§6の数式を利用者のExcel
トラッカーと厳密一致させることを最優先しているため、数式を独断で拡張していない**。
`corner`列は取り込み・出力はするが、現時点ではスコアに影響しない。
角地加点をスコアに含めたい場合は、Excel側の数式を先に確定させた上で
`config/criteria.yaml`に重みを追加し、`src/score.py`と`tests/test_score.py`の
両方を更新すること。

### 出力

`data/output.xlsx` に、総合スコア降順で順位付きの一覧が出る（列は割安点・資産点・
通勤点・広さ点・築浅点・駅点・ハザ減・赤信号減の内訳つき）。`--sheets`でGoogle
Sheetsにも同じ内容を出力できる（`GOOGLE_SHEETS_SPREADSHEET_ID`未設定なら新規作成）。

### 通知（--notify）

前回の`output.xlsx`と今回の採点結果を比較し、新規に出現した候補のうち総合スコアが
`NOTIFY_SCORE_THRESHOLD`（既定75点）以上のものをGmail API経由でメール通知する。

LINE通知について: 依頼書ではLINE通知も選択肢だったが、**LINE Notifyは2025年3月31日に
サービス終了済み**（LINE社発表）。後継のMessaging APIは公式アカウント作成等の
追加セットアップが要るため、本ツールでは未実装（メール通知のみ）。

### テスト

```bash
pytest
```

`tests/test_score.py` は依頼書 §8 のサンプル5件の期待スコア（±1点）と順位を
回帰テストとして固定している。`tests/test_enrich.py` / `test_intake_gmail.py` /
`test_notify.py` はM2〜M5の各ロジックをHTTPモックで検証している（「検証状況について」
参照）。スコア数式（`src/score.py`）を変更する場合は、Excelトラッカー側の数式と
ズレていないか必ず突き合わせた上で、`test_score.py`の期待値も更新すること。

## スコアリング仕様

`src/score.py` が実装する数式は `config/criteria.yaml` の定数を使う。中間量・
各スコア・総合の計算式は依頼書 §6 に定義されている通りで、利用者が別途持っている
Excelトラッカーと**厳密に一致**させることを意図している。

### スコアの限界（重要）

**割安点は「土地面積×相場坪単価」ベースの簡易査定のため、駅近・築浅などの
プレミアムが乗った物件を「割高」と判定しやすい構造的な偏りがある。**
たとえば駅3分の狭小地・築浅の物件は、建物価値の残存率が高く土地も狭いため
「推定適正」が低く出て割安点が伸び悩む一方、駅点・築浅点では高評価になる。
**割安点は単独で見ず、必ず資産点・駅点と併読すること。** 総合点はこの
バイアスをある程度均すが、完全には相殺しない。

同様に、`reference_land.csv` のseed値やreinfolibの成約事例は駅単位の粗い相場であり、
同じ駅内でも角地・接道条件・高低差などで実勢は変動する。総合点はスクリーニング
用の一次選抜として使い、上位候補は現地確認・不動産業者への確認を必ず行うこと。

`enrich_reinfolib.py`のハザード自動判定は、現状「洪水浸水想定区域のタイルに
座標が含まれるか」の粗い二値判定（含まれれば`hazard_0_3=2`固定）であり、
浸水深のランク別の段階分けはできていない（コード内TODO参照）。手動でhazard_0_3を
設定済みの候補は自動判定で上書きしない。

## データソースとAPIキーの取得先

| 用途 | ソース | キー取得 |
|---|---|---|
| 取引価格・ハザード・用途地域 | 不動産情報ライブラリAPI（国交省） | https://www.reinfolib.mlit.go.jp/api/request/ （審査5営業日目安）。API仕様: https://www.reinfolib.mlit.go.jp/help/apiManual/ |
| 住所→緯度経度 | 国土地理院 ジオコーディング | キー不要（`https://msearch.gsi.go.jp/address-search/AddressSearch`） |
| 通勤時間（横浜・高田馬場） | Google Maps **Routes API**（`computeRoutes`） | https://console.cloud.google.com/apis/library/routes.googleapis.com で有効化。**旧Directions APIは2025年3月以降に作った新規プロジェクトでは有効化できないため使っていない**（下記「料金について」参照） |
| 保存検索メールの取得・メール通知・Sheets出力 | Gmail API / Google Sheets API（共通OAuthクライアント） | https://console.cloud.google.com/apis/credentials （OAuth 2.0クライアントID・デスクトップアプリを1つ作成し使い回す） |

取得したキー・トークンは `.env`（`.env.example`をコピー）に記入する。
`.gitignore`で `.env` と `secrets/` 配下はコミット対象外。

### 料金について

| サービス | 料金 | 課金アカウント登録 |
|---|---|---|
| 不動産情報ライブラリ | 完全無料 | 不要 |
| 国土地理院ジオコーディング | 完全無料 | 不要 |
| Gmail API / Sheets API | 個人利用の範囲では無料 | 不要 |
| Google Maps Routes API | Compute Routes・Essentials は**月10,000コールまで無料**、超過分は従量課金 | **必要**（有効化時にGoogle Cloudへ支払い方法の登録が要る） |

このツールの呼び出し量（1回の実行で候補×2駅）なら、毎日自動実行しても月10,000コールには
まず届かないため実質無料で使える見込みだが、有効化自体にはクレジットカード等の
登録が必要。心配な場合はGoogle Cloud側で低額の予算アラートを設定しておくとよい。

Gmail/Sheetsは初回実行時にブラウザでOAuth認可すると`secrets/gmail_token.json`に
トークンが保存され、以降は自動更新される（scopeを追加した場合はこのファイルを
削除して再認可が必要）。

## 毎朝の自動実行（GitHub Actions）

`.github/workflows/daily.yml` が毎朝（21:30 UTC = 6:30 JST）`python run.py --all`を
実行する。CI環境ではブラウザOAuth認可ができないため、**ローカルで一度
`python run.py --gmail`等を実行して`secrets/gmail_token.json`を生成し、その中身を
リポジトリシークレット`GMAIL_TOKEN_JSON`に登録**しておく必要がある（ワークフロー
ファイル冒頭のコメントに必要なシークレット一覧を記載）。出力はリポジトリに
コミットせず、ワークフローのArtifactとしてのみ保存する（上記「リポジトリの
置き場所について」参照）。

## 利用規約（ToS）方針

- 不動産ポータルのWebページを直接取得・解析することはしない（HTML/HTTPアクセス含む）。
- ポータルの情報は、利用者自身が保存検索登録し、自分宛に届いたメール（Gmail経由で
  自分の受信箱を読む）からのみ取り込む。これは各ポータルのメール配信機能を
  正規に利用しているだけであり、規約上のスクレイピング/クローリング禁止条項には
  該当しない、という理解に基づく。ただし各ポータルの最新の利用規約は変わりうる
  ため、定期的に確認すること。
- 公的データ（不動産情報ライブラリ、国土地理院）はオープンデータ/公式APIの
  範囲内で利用する。
- Google Maps Platform / Google Workspace APIは利用規約・料金体系に従い、
  APIキー・トークンは`.env`/`secrets/`で管理しリポジトリにコミットしない。

## ディレクトリ構成

```
bukken-pipeline/
  .env.example                 # 環境変数の雛形
  .gitignore
  README.md
  requirements.txt
  config/
    criteria.yaml               # 予算・面積下限・通勤先・スコア重み・定数
    reference_land.csv          # 駅→土地坪単価(万/坪) seed（--reinfolibで実データ上書き）
    reference_commute.csv       # 駅→横浜(分),高田馬場(分) seed
  data/
    candidates.csv               # 入力（手動 or --gmailが追加）
    output.xlsx                   # 出力（gitignore対象、実行で生成）
  src/
    models.py                     # Candidate / ScoredCandidate データクラス
    intake_manual.py               # CSV → candidates（M1）
    intake_gmail.py                 # Gmail API → candidates（M4、SUUMO・東急リバブル対応）
    enrich_geocode.py                # 国土地理院 住所→緯度経度（M2）
    enrich_reinfolib.py               # 不動産情報ライブラリ 相場・ハザード・用途地域（M2）
    enrich_commute.py                  # Google Maps Routes API 通勤実測（M3）
    google_auth.py                      # Gmail/Sheets共通OAuthヘルパー
    score.py                              # スコアリング本体（M1）
    output_sheet.py                        # xlsx / Google Sheets出力（M1・M5）
    notify.py                               # 高得点新着のメール通知（M5）
  run.py                          # 一括実行 CLI（--gmail/--geocode/--reinfolib/--commute/--sheets/--notify/--all）
  tests/
    test_score.py                 # §6の数式と§8のサンプル期待値の回帰テスト
    test_enrich.py                # M2/M3のHTTPモックテスト
    test_intake_gmail.py          # M4のHTML抽出テスト
    test_notify.py                # M5の差分検出テスト
  .github/workflows/daily.yml    # 毎朝実行（M5）
```
