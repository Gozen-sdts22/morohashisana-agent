# 諸橋沙夏情報収集Agent

諸橋沙夏さんに関する情報を複数のソースから自動収集し、Claude APIを活用して重要度を判定・分類し、Webインターフェースで閲覧できるシステムです。

## 特徴

- **複数ソース対応**: Yahoo!ニュース、モデルプレスから情報収集（今後Xを追加する予定）
- **AI判定**: Claude APIによる高精度な関連性・重要度判定
- **専門Agent設計**: 各収集ソースに特化したAgent（専用プロンプト付き）
- **柔軟な設定**: JSON設定ファイルによる判定基準のカスタマイズ
- **Webインターフェース**: 収集した情報を見やすく表示

## 技術スタック

- **言語**: Python 3.10+
- **Webフレームワーク**: Flask
- **ORM**: SQLAlchemy
- **データベース**: SQLite（開発）/ PostgreSQL（本番）
- **AI**: Claude API (Sonnet 4)
- **スクレイピング**: BeautifulSoup4, requests, snscrape

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd morohashisana-agent
```

### 2. 仮想環境の作成と有効化

```bash
# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、必要な情報を設定してください。

```bash
cp .env.example .env
```

`.env`ファイルを編集:

```bash
# Claude API Key（必須）
CLAUDE_API_KEY=sk-ant-xxxxx

# データベース（開発環境）
DB_TYPE=sqlite
DB_PATH=data/natsu_dev.db

# ログレベル
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 5. データベースの初期化

```bash
python scripts/init_database.py
```

### 6. データベース接続テスト（任意）

```bash
python scripts/test_connection.py
```

## 使用方法

### コマンドラインから実行

情報収集を手動で実行する場合:

```bash
python main.py
```

### Webインターフェースから実行

1. Flaskアプリケーションを起動:

```bash
python src/web/app.py
```

2. ブラウザで `http://localhost:5000` にアクセス

3. 「情報を収集する」ボタンをクリックして収集開始

4. フィルタを使用して情報を絞り込み

## プロジェクト構成

```
morohashisana-agent/
├── config/
│   ├── settings.json          # 判定基準、フィルタ設定
│   ├── sources.json           # アカウント情報（ダミー含む）
│   └── prompts/               # 各Agent専用プロンプト
│       ├── twitter_agent_prompt.txt
│       ├── yahoo_agent_prompt.txt
│       ├── modelpress_agent_prompt.txt
│       └── judge_agent_prompt.txt
├── src/
│   ├── agents/                # 情報収集Agent
│   │   ├── base_agent.py
│   │   ├── twitter_agent.py
│   │   ├── yahoo_agent.py
│   │   └── modelpress_agent.py
│   ├── processors/            # Claude判定処理
│   │   └── claude_processor.py
│   ├── database/              # データベース管理
│   │   ├── db_manager.py
│   │   └── models.py
│   ├── utils/                 # ユーティリティ
│   │   ├── prompt_manager.py
│   │   └── logger.py
│   └── web/                   # Webインターフェース
│       ├── app.py
│       ├── api.py
│       ├── static/
│       │   ├── style.css
│       │   └── main.js
│       └── templates/
│           └── index.html
├── scripts/                   # スクリプト
│   ├── init_database.py
│   └── test_connection.py
├── data/                      # データベース（開発用）
├── logs/                      # ログファイル
├── main.py                    # メイン実行スクリプト
├── requirements.txt           # 依存パッケージ
├── .env.example               # 環境変数テンプレート
└── README.md                  # このファイル
```

## 設定

### 判定基準のカスタマイズ

`config/settings.json`を編集して、重要度判定の基準をカスタマイズできます:

```json
{
  "judgment_criteria": {
    "importance_levels": {
      "high": {
        "score_range": [80, 100],
        "keywords": ["出演決定", "発売", "リリース", ...]
      },
      ...
    },
    "categories": [
      "メディア出演（TV/ラジオ/雑誌）",
      ...
    ]
  },
  "filtering": {
    "min_relevance_score": 30,
    "excluded_keywords": ["炎上", "アンチ"]
  }
}
```

### 情報ソースの設定

`config/sources.json`を編集して、収集対象を変更できます:

```json
{
  "twitter": {
    "hashtags": ["#さなのいす", "諸橋沙夏"],
    "engagement_threshold": {
      "likes": 10000,
      "views": 100000
    }
  }
}
```

## トラブルシューティング

### snscrapeが動作しない

snscrapeは非公式ツールのため、動作しない可能性があります。その場合、システムは自動的にダミーデータを返します。

### Claude APIエラー

- `CLAUDE_API_KEY`が正しく設定されているか確認してください
- APIキーの利用制限・レート制限を確認してください

### データベース接続エラー

- `.env`ファイルの設定を確認してください
- `python scripts/test_connection.py`で接続をテストしてください

## 本番環境（PostgreSQL）への移行

本番環境でPostgreSQLを使用する場合:

1. AWS RDS PostgreSQLインスタンスをセットアップ

2. `.env`ファイルを更新:

```bash
DB_TYPE=postgresql
DB_HOST=your-rds-endpoint.ap-northeast-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=natsu_agent_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_SSL_MODE=require
```

3. データベースを初期化:

```bash
ENVIRONMENT=production python scripts/init_database.py
```

## ライセンス

個人利用目的のプロジェクトです。

## 注意事項

- スクレイピングは各サービスの利用規約を遵守してください
- 適切なリクエスト間隔を設けてください
- 個人利用目的に限定してください

## 開発者向け

### ログの確認

ログは`logs/app.log`に記録されます:

```bash
tail -f logs/app.log
```

### データベースの確認（SQLite）

```bash
sqlite3 data/natsu_dev.db
```

```sql
-- アイテムの確認
SELECT * FROM items ORDER BY collected_at DESC LIMIT 10;

-- 実行ログの確認
SELECT * FROM executions ORDER BY started_at DESC;
```

## サポート

質問や問題がある場合は、Issueを作成してください。
