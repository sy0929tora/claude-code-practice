# bukken-pipeline

住宅購入（戸建）の物件探しを支援する、ローカルで動く再実行可能な採点パイプライン。
「ポータルの保存検索メール」または「手動入力」で集めた候補を、相場・ハザード・
二拠点通勤（横浜駅／高田馬場駅）で自動採点し、順位付けして `output.xlsx` に出す。

このツールは**物件を探すこと自体は自動化しない**。判断（採点・順位付け）を
自動化するのが役割。網羅的な物件収集や、不動産ポータルのスクレイピングは行わない。

## 現在の実装状況（マイルストーン）

- [x] **M1** 手動CSV入力 → 採点 → `output.xlsx`（このREADMEの内容）
- [ ] M2 国土地理院ジオコーディング + 不動産情報ライブラリ（相場・ハザード自動更新）
- [ ] M3 Google Directions（横浜・高田馬場の実測通勤時間）
- [ ] M4 Gmail API（保存検索メールからの自動intake）
- [ ] M5 Google Sheets出力 + 通知 + 毎朝自動実行（GitHub Actions）

M2以降のモジュール（`enrich_geocode.py` 等）はインターフェースのみ用意されており、
未実装です。実装時は `src/score.py` の `ScoringContext` / `Candidate` の
`land_price_source` / `commute_*_min` フィールドに実測値を書き込む形で接続します。

## 絶対制約（この方針は変えない）

- **不動産ポータル（SUUMO / at home / LIFULL HOME'S 等）のWebページはスクレイピングしない。**
  各社の利用規約で原則禁止されており、bot対策で不安定なため。
- 物件情報の入力は次の2経路のみ。
  1. 利用者本人宛に届いた「保存検索」の通知メール（Gmail APIで自分の受信箱を読む＝合法。M4で実装）
  2. 手動入力（CSV。§`data/candidates.csv` 参照）
- 相場・地価・ハザード・用途地域・通勤時間は公的/公式APIのみから取得する（下記参照）。
- APIキー・トークンは `.env`（`python-dotenv`）で管理し、**リポジトリにコミットしない**。
- パイプラインは冪等。同じ入力で何度実行しても壊れず、住所+価格でdedupeする。
- 出典が公的データの数値は、出力（`output.xlsx`の「相場出典」列など）に出典を残す。

## セットアップ

```bash
cd bukken-pipeline
python3 -m venv .venv
source .venv/bin/activate      # Windowsは .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # 現時点(M1)ではキー未設定でも動く
```

## 実行方法（M1: 手動CSV → 採点 → xlsx）

```bash
python run.py --input data/candidates.csv --output data/output.xlsx
```

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
| zoning | 用途地域（任意） |
| corner | 角地フラグ 0/1（現状スコアには未加点。TODO: §3「角地は加点」の反映） |
| hazard_0_3 | ハザード懸念度 0(なし)〜3(強)。M2で不動産情報ライブラリの自動判定に置き換え予定 |
| redflag_0_3 | 資産性の赤信号（敷地面積最低限度・大きな2項道路セットバック等）0〜3 |

`config/reference_land.csv`・`config/reference_commute.csv` はAPIが未設定/失敗のときの
フォールバック値（seed）。M2/M3でAPIが実測できた駅は自動更新されます（未実装）。

### 出力

`data/output.xlsx` に、総合スコア降順で順位付きの一覧が出ます（列は割安点・資産点・
通勤点・広さ点・築浅点・駅点・ハザ減・赤信号減の内訳つき）。`.gitignore`で
`data/output.xlsx` はコミット対象外にしています（個人の物件情報のため）。

### テスト

```bash
pytest
```

`tests/test_score.py` は依頼書 §8 のサンプル5件の期待スコア（±1点）と順位を
回帰テストとして固定しています。スコア数式（`src/score.py`）を変更する場合は、
Excelトラッカー側の数式とズレていないか必ず突き合わせた上で、このテストの
期待値も更新してください。

## スコアリング仕様

`src/score.py` が実装する数式は `config/criteria.yaml` の定数を使う。中間量・
各スコア・総合の計算式は依頼書 §6 に定義されている通りで、利用者が別途持っている
Excelトラッカーと**厳密に一致**させることを意図しています。

### スコアの限界（重要）

**割安点は「土地面積×相場坪単価」ベースの簡易査定のため、駅近・築浅などの
プレミアムが乗った物件を「割高」と判定しやすい構造的な偏りがあります。**
たとえば駅3分の狭小地・築浅の物件は、建物価値の残存率が高く土地も狭いため
「推定適正」が低く出て割安点が伸び悩む一方、駅点・築浅点では高評価になります。
**割安点は単独で見ず、必ず資産点・駅点と併読してください。** 総合点はこの
バイアスをある程度均しますが、完全には相殺しません。

同様に、`reference_land.csv` のseed値やreinfolibの成約事例は駅単位の粗い相場であり、
同じ駅内でも角地・接道条件・高低差などで実勢は変動します。総合点はスクリーニング
用の一次選抜として使い、上位候補は現地確認・不動産業者への確認を必ず行ってください。

## データソースとAPIキーの取得先

| 用途 | ソース | キー取得 |
|---|---|---|
| 取引価格・ハザード・用途地域 | 不動産情報ライブラリAPI（国交省） | https://www.reinfolib.mlit.go.jp/api/request/ （審査5営業日目安）。API仕様: https://www.reinfolib.mlit.go.jp/help/apiManual/ |
| 住所→緯度経度 | 国土地理院 ジオコーディング | キー不要（`https://msearch.gsi.go.jp/address-search/AddressSearch`） |
| 通勤時間（横浜・高田馬場） | Google Maps Directions API | https://console.cloud.google.com/apis/credentials （無料枠＋従量課金） |
| 保存検索メールの取得 | Gmail API | https://console.cloud.google.com/apis/credentials （OAuthクライアント、デスクトップアプリ） |
| 出力（任意） | Google Sheets API | 同上のGCPプロジェクトでSheets APIを有効化 |

取得したキー・トークンは `.env`（`.env.example`をコピー）に記入してください。
`.gitignore`で `.env` と `secrets/` 配下はコミット対象外です。

## 利用規約（ToS）方針

- 不動産ポータルのWebページを直接取得・解析することはしません（HTML/HTTPアクセス含む）。
- ポータルの情報は、利用者自身が保存検索登録し、自分宛に届いたメール（Gmail経由で
  自分の受信箱を読む）からのみ取り込みます。これは各ポータルのメール配信機能を
  正規に利用しているだけであり、規約上のスクレイピング/クローリング禁止条項には
  該当しない、という理解に基づきます。ただし各ポータルの最新の利用規約は変わりうる
  ため、定期的に確認してください。
- 公的データ（不動産情報ライブラリ、国土地理院）はオープンデータ/公式APIの
  範囲内で利用します。
- Google Maps Platform は利用規約・料金体系に従い、APIキーは`.env`で管理し
  リポジトリにコミットしません。

## ディレクトリ構成

```
bukken-pipeline/
  .env.example              # 環境変数の雛形
  .gitignore
  README.md
  requirements.txt
  config/
    criteria.yaml           # 予算・面積下限・通勤先・スコア重み・定数
    reference_land.csv      # 駅→土地坪単価(万/坪) seed
    reference_commute.csv   # 駅→横浜(分),高田馬場(分) seed
  data/
    candidates.csv          # 入力（手動 or 将来intakeが生成）
    output.xlsx              # 出力（gitignore対象、実行で生成）
  src/
    models.py               # Candidate / ScoredCandidate データクラス
    intake_manual.py         # CSV → candidates（M1）
    intake_gmail.py           # Gmail API → candidates（M4・未実装）
    enrich_geocode.py          # 国土地理院 住所→緯度経度（M2・未実装）
    enrich_reinfolib.py         # 不動産情報ライブラリ 相場・ハザード（M2・未実装）
    enrich_commute.py            # Google Directions 通勤実測（M3・未実装）
    score.py                      # スコアリング本体（M1実装済み）
    output_sheet.py                # xlsx出力（M1実装済み）
    notify.py                       # 高得点新着の通知（M5・未実装）
  run.py                     # 一括実行 CLI
  tests/
    test_score.py            # §6の数式と§8のサンプル期待値の回帰テスト
  .github/workflows/daily.yml  # 毎朝実行（M5・未実装）
```
