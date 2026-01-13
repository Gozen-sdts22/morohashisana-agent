# 諸橋沙夏情報収集Agentシステム 要件定義書

**バージョン**: 1.0  
**作成日**: 2025-01-13  
**ステータス**: 確定

---

## 1. システム概要

### 1.1 目的
諸橋沙夏さんに関する情報を複数のソースから自動収集し、Claude APIを活用して重要度を判定・分類し、Webインターフェースで閲覧できるシステムを構築する。

### 1.2 システムの特徴
- **複数ソース対応**: X（旧Twitter）、Yahoo!ニュース、モデルプレスから情報収集
- **AI判定**: Claude APIによる高精度な関連性・重要度判定
- **専門Agent設計**: 各収集ソースに特化したAgent（専用プロンプト付き）
- **柔軟な設定**: JSON設定ファイルによる判定基準のカスタマイズ
- **クラウドDB**: AWS RDS PostgreSQLによるデータ管理

### 1.3 想定ユーザー
- 諸橋沙夏さんのファン
- 情報を効率的に収集・整理したい個人ユーザー

---

## 2. 機能要件

### 2.1 情報収集機能

#### 2.1.1 アーキテクチャ

```
[各種ソース] 
    ↓
[専門Agent層] - 各Agent専用のシステムプロンプトで動作
├─ X Agent
├─ Yahoo News Agent
└─ Model Press Agent
    ↓
[取りまとめAgent]
- 重複排除
- データ正規化
    ↓
[Judge Agent] - Claude APIで一括判定
- 関連性判定
- 重要度評価
- カテゴリ分類
- 要約生成
    ↓
[データストレージ (PostgreSQL)]
```

#### 2.1.2 対象ソース

##### X (旧Twitter)
- **収集対象**
  - 本人アカウント（ダミー設定、今後実装）
  - 公式アカウント（ダミー設定、今後実装）
  - ハッシュタグ検索
    - `#さなのいす`
    - `諸橋沙夏`
    - フィルタ条件: いいね1万以上 OR 表示数10万以上

- **収集方法**: snscrape（無料、非公式）
- **取得情報**
  - ツイートID
  - 投稿者名・アカウント
  - 本文
  - URL
  - 投稿日時
  - いいね数、リツイート数、表示数

##### Yahoo!ニュース
- **収集対象**: "諸橋沙夏" キーワード検索結果
- **収集方法**: Webスクレイピング（BeautifulSoup4）
- **取得情報**
  - 記事タイトル
  - 記事要約
  - URL
  - 配信元メディア
  - 公開日時

##### モデルプレス
- **収集対象**: "諸橋沙夏" キーワード検索結果
- **収集方法**: Webスクレイピング（BeautifulSoup4）
- **取得情報**
  - 記事タイトル
  - 記事要約
  - URL
  - 公開日時
  - サムネイル画像URL（ある場合）

#### 2.1.3 各Agent専用システムプロンプト

各Agentは専用のシステムプロンプトを持ち、役割を明確化する。

**配置場所**: `config/prompts/`
- `twitter_agent_prompt.txt`
- `yahoo_agent_prompt.txt`
- `modelpress_agent_prompt.txt`
- `judge_agent_prompt.txt`

**プロンプトの役割**
- データの構造化
- 初期フィルタリング（明らかなノイズ除去）
- 品質チェック
- 統一フォーマットでの出力

#### 2.1.4 収集データのフロー

1. **各専門Agentが生データを収集**
   - 各Agentは専用プロンプトに基づいて動作
   - JSON形式で統一フォーマット出力

2. **取りまとめAgentでデータ統合**
   - URL重複チェック
   - データ正規化
   - 日時フォーマット統一

3. **Judge AgentでClaude判定**
   - 関連性スコア（0-100）
   - 重要度スコア（0-100）
   - カテゴリ分類
   - 50文字要約
   - 判定理由

4. **データベース保存**
   - 閾値以上のデータのみ保存
   - 重複データは除外

---

### 2.2 重要度判定機能

#### 2.2.1 判定プロセス

Judge Agentが`config/settings.json`の基準に基づいて判定を実行。

#### 2.2.2 設定ファイル構造

```json
{
  "judgment_criteria": {
    "importance_levels": {
      "high": {
        "score_range": [80, 100],
        "description": "メディア出演、新曲リリース、重大発表、ライブ告知",
        "keywords": ["出演決定", "発売", "リリース", "ライブ", "公演", "主演"]
      },
      "medium": {
        "score_range": [50, 79],
        "description": "イベント告知、インタビュー記事、配信更新",
        "keywords": ["イベント", "インタビュー", "配信", "更新", "公開"]
      },
      "low": {
        "score_range": [0, 49],
        "description": "日常的なSNS投稿、過去の出来事の言及",
        "keywords": ["投稿", "ツイート", "でした", "ありがとう"]
      }
    },
    "relevance_threshold": 30,
    "categories": [
      "メディア出演（TV/ラジオ/雑誌）",
      "音楽活動（新曲/MV/ライブ）",
      "イベント",
      "SNS投稿",
      "インタビュー/記事",
      "その他"
    ]
  },
  "filtering": {
    "min_relevance_score": 30,
    "min_importance_score": 0,
    "excluded_keywords": ["炎上", "アンチ"]
  }
}
```

#### 2.2.3 判定項目

| 項目 | 説明 | 値の範囲 |
|------|------|----------|
| 関連性スコア | 諸橋沙夏さん本人への関連度 | 0-100 |
| 重要度スコア | ファンにとっての重要度 | 0-100 |
| 重要度レベル | 3段階分類 | high / medium / low |
| カテゴリ | 情報の種別 | 設定ファイルから選択 |
| 要約 | 50文字以内の要約文 | テキスト |
| 判定理由 | 重要度判定の根拠 | テキスト |

#### 2.2.4 フィルタリング

- 関連性スコア30未満: データベースに保存しない
- 除外キーワードを含む: データベースに保存しない

---

### 2.3 実行スケジュール機能

#### 2.3.1 実行方式

**現行**: 手動実行（Web UIボタン）  
**将来対応**: スケジュール自動実行（設定で有効化可能）

#### 2.3.2 実行フロー

```
[Web UI: 実行ボタン押下]
    ↓
[ボタン無効化（実行中は再押下不可）]
    ↓
[実行開始]
    ↓
[各Agent順次実行] ← 各Agentで最大2回リトライ
├─ X Agent (リトライ2回、間隔5秒)
├─ Yahoo News Agent (リトライ2回、間隔5秒)
└─ Model Press Agent (リトライ2回、間隔5秒)
    ↓
    ├─ 全Agent成功 → [データ統合へ]
    └─ 1つでも失敗 → [詳細エラー表示・処理中断]
    ↓
[データ統合]
    ↓
[Judge Agent: Claude一括判定]
    ↓
[DB保存]
    ↓
[完了通知・結果表示]
    ↓
[ボタン有効化]
```

#### 2.3.3 エラーハンドリング

**リトライ仕様**
- 最大リトライ回数: 2回
- リトライ間隔: 5秒
- 各Agentごとに独立してリトライ

**失敗時の動作**
- 1つのAgentでも最終的に失敗した場合、全体を中断
- 詳細エラーメッセージを表示
  - 例: "X Agent: 接続タイムアウト（30秒）"
  - 失敗したAgent名、エラー内容、試行回数を含む

**実行ログ**
- 実行ID（例: exec_20250113_143000）
- 開始・終了日時
- 各Agentのステータス・試行回数・取得件数
- Claude処理結果
- エラー詳細（失敗時）

#### 2.3.4 将来対応（スケジュール実行）

設定ファイルで制御可能：

```json
{
  "schedule": {
    "enabled": false,
    "time": "08:00",
    "timezone": "Asia/Tokyo",
    "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
  }
}
```

---

### 2.4 Web閲覧機能

#### 2.4.1 画面構成

```
┌────────────────────────────────────────────────┐
│ 諸橋沙夏情報収集システム                        │
├────────────────────────────────────────────────┤
│ [情報を収集する] ← 実行中は無効化               │
│ 最終実行: 2025-01-13 14:30 (45件取得)         │
├────────────────────────────────────────────────┤
│ フィルター:                                     │
│ 期間: [過去7日▼] 重要度: [全て▼]              │
│ カテゴリ: [全て▼] 検索: [＿＿＿＿＿]           │
│ [フィルター適用]                                │
├────────────────────────────────────────────────┤
│ ┌──────────────────────────────────┐          │
│ │ 🔴 重要 | メディア出演              │          │
│ │ 2025-01-13 10:30 | Yahoo!ニュース  │          │
│ │ 諸橋沙夏、新ドラマ「〇〇」に出演決定 │          │
│ │ [記事を開く ↗]                     │          │
│ └──────────────────────────────────┘          │
│ 表示: 1-20 / 45件                              │
│ [もっと見る]                                    │
└────────────────────────────────────────────────┘
```

#### 2.4.2 表示項目

各情報アイテムに表示する内容：
- 重要度アイコン（🔴高 🟡中 ⚪低）
- カテゴリ
- 日時
- ソース名（X、Yahoo!ニュース、モデルプレス）
- 要約文（Claude生成、50文字）
- エンゲージメント（X投稿の場合: いいね数、表示数）
- リンクボタン（別タブで開く）

#### 2.4.3 フィルタリング機能

| フィルタ項目 | 選択肢 | デフォルト |
|-------------|--------|-----------|
| 期間 | 過去24時間 / 過去7日 / 過去30日 / 全期間 | 過去7日 |
| 重要度 | 全て / 高のみ / 中以上 | 全て |
| カテゴリ | 全て / 各カテゴリ | 全て |
| キーワード検索 | 自由入力（タイトル・本文検索） | - |

#### 2.4.4 ソート・ページネーション

**ソート**
- デフォルト固定: 重要度高 → 新しい順
- カスタムソート機能: 将来対応予定

**ページネーション**
- 1ページ20件表示
- 「もっと見る」ボタンで追加読み込み
- 表示件数/全件数を表示

#### 2.4.5 実装しない機能（将来対応）

以下の機能は現バージョンでは実装せず、将来対応とする：
- 詳細表示モーダル（リンク先で確認する想定）
- 統計情報ダッシュボード
- カスタムソート機能

---

### 2.5 データ管理機能

#### 2.5.1 データベース仕様

**本番環境**: Amazon RDS PostgreSQL  
**開発環境**: SQLite（ローカル）

#### 2.5.2 テーブル設計

##### itemsテーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | SERIAL | PRIMARY KEY | 自動採番ID |
| source | VARCHAR(50) | NOT NULL | ソース種別（twitter/yahoo_news/modelpress） |
| source_detail | TEXT | - | ソース詳細（本人/公式/ハッシュタグ等） |
| title | TEXT | - | タイトル |
| content | TEXT | - | 本文 |
| summary | VARCHAR(100) | - | Claude生成要約（50文字） |
| url | TEXT | NOT NULL, UNIQUE | 情報URL（重複チェック用） |
| published_at | TIMESTAMP WITH TIME ZONE | NOT NULL | 公開日時 |
| relevance_score | INTEGER | - | 関連性スコア（0-100） |
| importance_score | INTEGER | - | 重要度スコア（0-100） |
| importance_level | VARCHAR(20) | - | 重要度レベル（high/medium/low） |
| category | VARCHAR(100) | - | カテゴリ |
| claude_reason | TEXT | - | 判定理由 |
| metrics | JSONB | - | メトリクス（いいね数等） |
| collected_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | 収集日時 |
| execution_id | VARCHAR(50) | - | 実行ID |

**インデックス**
- `idx_published_at`: published_at DESC
- `idx_importance`: importance_score DESC
- `idx_category`: category
- `idx_execution`: execution_id

##### executionsテーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | VARCHAR(50) | PRIMARY KEY | 実行ID（exec_YYYYMMDD_HHMMSS） |
| started_at | TIMESTAMP WITH TIME ZONE | NOT NULL | 開始日時 |
| completed_at | TIMESTAMP WITH TIME ZONE | - | 完了日時 |
| status | VARCHAR(20) | NOT NULL | ステータス（running/success/failed） |
| total_collected | INTEGER | DEFAULT 0 | 収集総数 |
| total_saved | INTEGER | DEFAULT 0 | 保存総数 |
| error_message | TEXT | - | エラーメッセージ |
| agent_results | JSONB | - | 各Agent結果 |
| claude_processed | INTEGER | - | Claude処理件数 |
| claude_duration_sec | DECIMAL(10,2) | - | Claude処理時間 |

**インデックス**
- `idx_executions_started`: started_at DESC

#### 2.5.3 データ保持期間

```json
{
  "data_retention": {
    "days": 90,
    "auto_cleanup": true,
    "cleanup_schedule": "weekly"
  }
}
```

- 90日以上前のデータを自動削除
- 毎週クリーンアップ実行

#### 2.5.4 重複排除

- URL単位で重複チェック
- 同一URLの情報は保存しない
- 重複時はログに記録

---

## 3. 非機能要件

### 3.1 パフォーマンス

- 1回の実行で50-100件程度のデータ収集を想定
- 実行時間: 3-5分以内（Claude API処理含む）
- Web UI応答時間: 2秒以内

### 3.2 セキュリティ

#### 3.2.1 認証情報管理
- APIキー・DB認証情報は`.env`ファイルで管理
- `.env`は`.gitignore`に追加（Git管理外）

#### 3.2.2 データベースセキュリティ
- RDS接続はSSL/TLS必須
- Security Groupで接続元IP制限
- 自宅IPのみアクセス許可

#### 3.2.3 API制限
- Claude API: レート制限に準拠
- スクレイピング: robots.txt遵守、適切な間隔

### 3.3 可用性

- ローカル環境での稼働想定（個人利用）
- 将来的にクラウドデプロイ可能な設計

### 3.4 保守性

- 設定ファイル（JSON）による柔軟なカスタマイズ
- ログ記録による障害調査
- モジュール化された設計

### 3.5 拡張性

以下の拡張を想定した設計：
- 新しい情報ソースの追加
- 新しいカテゴリの追加
- スケジュール実行機能
- 通知機能
- 統計ダッシュボード

---

## 4. 技術要件

### 4.1 技術スタック

#### 4.1.1 バックエンド
- **言語**: Python 3.10+
- **Webフレームワーク**: Flask
- **ORM**: SQLAlchemy
- **データベースドライバ**: psycopg2（PostgreSQL）
- **スケジューラ**: APScheduler（将来対応）

#### 4.1.2 情報収集
- **X収集**: snscrape（無料、非公式ツール）
- **スクレイピング**: BeautifulSoup4 + requests
- **AI判定**: Claude API（Sonnet 4）

#### 4.1.3 フロントエンド
- **マークアップ**: HTML5 + CSS3
- **スクリプト**: Vanilla JavaScript
- **CSSフレームワーク**: 検討中（Bootstrap等）

#### 4.1.4 インフラ
- **本番DB**: Amazon RDS PostgreSQL（db.t3.micro）
- **開発DB**: SQLite
- **実行環境**: ローカルPC（将来的にクラウド移行可能）

#### 4.1.5 その他
- **環境変数管理**: python-dotenv
- **ログ**: Python標準logging

### 4.2 ディレクトリ構成

```
natsu-agent/
├── config/
│   ├── settings.json          # 判定基準、フィルタ設定
│   ├── sources.json           # アカウント情報（ダミー含む）
│   └── prompts/               # 各Agent専用プロンプト
│       ├── twitter_agent_prompt.txt
│       ├── yahoo_agent_prompt.txt
│       ├── modelpress_agent_prompt.txt
│       └── judge_agent_prompt.txt
├── src/
│   ├── agents/
│   │   ├── base_agent.py      # Agent基底クラス
│   │   ├── twitter_agent.py   # X収集Agent
│   │   ├── yahoo_agent.py     # Yahoo News収集Agent
│   │   └── modelpress_agent.py # Model Press収集Agent
│   ├── processors/
│   │   └── claude_processor.py # Claude判定処理
│   ├── database/
│   │   ├── db_manager.py      # DB接続管理
│   │   └── models.py          # SQLAlchemyモデル
│   ├── utils/
│   │   ├── prompt_manager.py  # プロンプト読み込み
│   │   └── logger.py          # ログ設定
│   └── web/
│       ├── app.py             # Flaskアプリ
│       ├── api.py             # APIエンドポイント
│       ├── static/            # CSS/JS
│       │   ├── style.css
│       │   └── main.js
│       └── templates/
│           └── index.html     # メインUI
├── scripts/
│   ├── init_database.py       # DB初期化スクリプト
│   └── test_connection.py     # DB接続テスト
├── data/
│   └── natsu_dev.db           # 開発用SQLite（本番RDS）
├── logs/
│   └── app.log                # アプリケーションログ
├── requirements.txt           # Python依存パッケージ
├── .env                       # 環境変数（Git管理外）
├── .gitignore
├── README.md
└── main.py                    # エントリーポイント
```

### 4.3 環境変数

`.env`ファイル内容：

```bash
# Claude API
CLAUDE_API_KEY=sk-ant-xxxxx

# Database - Production (RDS)
DB_TYPE=postgresql
DB_HOST=natsu-agent-db.xxxxx.ap-northeast-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=natsu_agent_db
DB_USER=postgres
DB_PASSWORD=your_master_password
DB_SSL_MODE=require

# Database - Development (SQLite)
# DB_TYPE=sqlite
# DB_PATH=data/natsu_dev.db

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development  # or 'production'
```

---

## 5. AWS構成要件

### 5.1 AWS RDS PostgreSQL仕様

#### 5.1.1 インスタンス設定

| 項目 | 値 | 備考 |
|------|-----|------|
| エンジン | PostgreSQL 15.x | 最新安定版 |
| インスタンスクラス | db.t3.micro | 無料枠対象 |
| ストレージタイプ | 汎用SSD (gp3) | - |
| ストレージ容量 | 20GB | 無料枠上限 |
| マルチAZ | 無効 | 無料枠対象外のため |
| パブリックアクセス | 有効 | ローカルからの接続用 |
| 暗号化 | 有効 | デフォルト有効 |

#### 5.1.2 バックアップ設定

| 項目 | 値 | 備考 |
|------|-----|------|
| 自動バックアップ | 有効 | - |
| 保持期間 | 1日 | 無料枠内で最小化 |
| バックアップウィンドウ | デフォルト | - |

#### 5.1.3 セキュリティグループ

**インバウンドルール**
```
タイプ: PostgreSQL
プロトコル: TCP
ポート: 5432
ソース: [自宅IP]/32
説明: Local development access
```

### 5.2 データ容量試算

```
1件あたり: 約2KB
- title: 100文字 = 200B
- content: 500文字 = 1KB
- summary: 50文字 = 100B
- その他メタデータ: 700B

収集見込み:
- 1日: 50件 = 100KB
- 1ヶ月: 1,500件 = 3MB
- 1年: 18,000件 = 36MB

→ 20GBストレージで十分
```

### 5.3 コスト試算

**無料枠（12ヶ月間）**
- db.t3.micro: 750時間/月（24時間×31日）
- ストレージ: 20GB
- バックアップ: 20GB
- **月額: $0**

**無料枠終了後**
- db.t3.micro: 約$15/月
- ストレージ（20GB）: 約$2.3/月
- **合計: 約$17-20/月**

### 5.4 AWS セットアップ手順概要

1. RDSインスタンス作成
2. セキュリティグループ設定
3. ローカル環境`.env`設定
4. 接続テスト実行
5. テーブル初期化

詳細手順は別途セットアップガイドを参照。

---

## 6. APIエンドポイント仕様

### 6.1 エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/items` | 情報一覧取得（フィルタ対応） |
| POST | `/api/execute` | 情報収集実行 |
| GET | `/api/status` | 実行状態取得 |
| GET | `/api/logs` | 実行ログ取得 |

### 6.2 詳細仕様

#### 6.2.1 GET /api/items

**説明**: 収集した情報の一覧を取得

**クエリパラメータ**
```
period: 期間（24h, 7d, 30d, all）
importance: 重要度（all, high, medium_up）
category: カテゴリ（all, または各カテゴリ名）
keyword: キーワード検索
page: ページ番号（デフォルト: 1）
per_page: 1ページあたり件数（デフォルト: 20）
```

**レスポンス例**
```json
{
  "items": [
    {
      "id": 1,
      "source": "yahoo_news",
      "title": "諸橋沙夏、新ドラマ出演決定",
      "summary": "人気アイドル諸橋沙夏が春ドラマに出演することが決定",
      "url": "https://...",
      "published_at": "2025-01-13T10:30:00+09:00",
      "importance_score": 85,
      "importance_level": "high",
      "category": "メディア出演",
      "metrics": null
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "has_next": true
}
```

#### 6.2.2 POST /api/execute

**説明**: 情報収集を実行

**リクエストボディ**: なし

**レスポンス例**
```json
{
  "status": "started",
  "execution_id": "exec_20250113_143000",
  "message": "情報収集を開始しました"
}
```

#### 6.2.3 GET /api/status

**説明**: 現在の実行状態を取得

**レスポンス例**
```json
{
  "is_running": true,
  "execution_id": "exec_20250113_143000",
  "started_at": "2025-01-13T14:30:00+09:00",
  "current_agent": "twitter",
  "progress": "2/3 agents completed"
}
```

#### 6.2.4 GET /api/logs

**説明**: 過去の実行ログを取得

**クエリパラメータ**
```
limit: 取得件数（デフォルト: 10）
```

**レスポンス例**
```json
{
  "logs": [
    {
      "id": "exec_20250113_143000",
      "started_at": "2025-01-13T14:30:00+09:00",
      "completed_at": "2025-01-13T14:32:15+09:00",
      "status": "success",
      "total_collected": 45,
      "total_saved": 38
    }
  ]
}
```

---

## 7. 開発・運用要件

### 7.1 開発環境

- **OS**: Windows / macOS / Linux
- **Python**: 3.10以上
- **エディタ**: 任意（VSCode推奨）
- **ブラウザ**: Chrome / Firefox / Safari（最新版）

### 7.2 デプロイ手順

#### 開発環境
1. リポジトリクローン
2. 仮想環境作成・有効化
3. `pip install -r requirements.txt`
4. `.env`ファイル作成（DB_TYPE=sqlite）
5. `python scripts/init_database.py`実行
6. `python main.py`でアプリ起動

#### 本番環境
1. AWS RDSセットアップ
2. `.env`ファイル更新（DB_TYPE=postgresql）
3. `ENVIRONMENT=production python scripts/init_database.py`
4. アプリケーション起動

### 7.3 監視・メンテナンス

#### 7.3.1 ログ監視
- アプリケーションログ: `logs/app.log`
- エラー発生時の詳細記録
- 日次ローテーション推奨

#### 7.3.2 データベース監視
- AWS RDS無料枠使用状況確認
- ストレージ使用量チェック
- バックアップ状態確認

#### 7.3.3 コスト監視
- AWS Budgetsでアラート設定
- 月次$1予算、80%でアラート

#### 7.3.4 定期メンテナンス
- 週次: 古いデータクリーンアップ
- 月次: ログファイルアーカイブ
- 必要に応じて設定ファイル調整

---

## 8. 制約事項・前提条件

### 8.1 制約事項

1. **X API利用**: 無料の非公式ツール（snscrape）使用のため、不安定な可能性あり
2. **スクレイピング**: 対象サイトの構造変更により動作しなくなる可能性あり
3. **Claude API**: レート制限・コストに依存
4. **AWS無料枠**: 12ヶ月後に有料化（約$17-20/月）

### 8.2 前提条件

1. **ネットワーク**: インターネット接続必須
2. **APIキー**: Claude APIキー取得済み
3. **AWSアカウント**: 既存アカウント使用
4. **ローカル環境**: Python 3.10+実行可能

### 8.3 利用規約遵守

- 各サービスの利用規約を遵守
- スクレイピングは適切な間隔で実行
- 個人利用目的に限定

---

## 9. 将来対応機能（本バージョンでは未実装）

以下の機能は将来的に実装を検討：

### 9.1 スケジュール自動実行
- 設定した時刻に自動実行
- 曜日指定実行

### 9.2 通知機能
- 重要情報発見時のメール通知
- Slack/Discord連携

### 9.3 Web UI拡張
- カスタムソート機能
- 詳細表示モーダル
- 統計ダッシュボード
- グラフ・チャート表示

### 9.4 情報ソース追加
- Google検索結果
- Instagram
- YouTube
- TikTok
- その他SNS

### 9.5 AI機能強化
- トレンド分析
- センチメント分析
- 自動タグ付け
- 関連情報推薦

### 9.6 エクスポート機能
- CSV出力
- PDF レポート生成
- データバックアップ

---

## 10. 付録

### 10.1 用語集

| 用語 | 説明 |
|------|------|
| Agent | 特定の情報ソースから データを収集する専門モジュール |
| Judge Agent | Claude APIを使用して情報を判定するモジュール |
| 関連性スコア | 諸橋沙夏さん本人への関連度（0-100） |
| 重要度スコア | ファンにとっての重要度（0-100） |
| システムプロンプト | 各Agentの動作を定義するテキスト指示 |

### 10.2 参考資料

- Claude API Documentation: https://docs.anthropic.com/
- AWS RDS Documentation: https://docs.aws.amazon.com/rds/
- snscrape GitHub: https://github.com/JustAnotherArchivist/snscrape
- BeautifulSoup Documentation: https://www.crummy.com/software/BeautifulSoup/

### 10.3 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0 | 2025-01-13 | 初版作成 | - |

---

**以上**
