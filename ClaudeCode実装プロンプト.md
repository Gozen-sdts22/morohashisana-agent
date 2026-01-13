# ClaudeCode実装プロンプト: 諸橋沙夏情報収集Agentシステム

## 概要
添付の要件定義書に基づいて、諸橋沙夏さんに関する情報を自動収集するAgentシステムを実装してください。

## 実装する内容

### フェーズ1: プロジェクト基盤構築
1. **ディレクトリ構造の作成**
   - 要件定義書「4.2 ディレクトリ構成」に従ってフォルダ・ファイルを作成
   - `.gitignore`の設定（.env、logs/、data/を除外）

2. **依存パッケージの定義**
   - `requirements.txt`を作成
   - 必要なパッケージ:
     - Flask（Webフレームワーク）
     - SQLAlchemy（ORM）
     - psycopg2-binary（PostgreSQLドライバ）
     - beautifulsoup4、requests（スクレイピング）
     - snscrape（X収集）
     - anthropic（Claude API）
     - python-dotenv（環境変数）
     - APScheduler（将来のスケジュール機能用）

3. **環境変数設定**
   - `.env.example`を作成（テンプレート）
   - 要件定義書「4.3 環境変数」の内容を反映

4. **設定ファイルの作成**
   - `config/settings.json`: 判定基準設定（要件定義書「2.2.2」参照）
   - `config/sources.json`: ダミーアカウント情報
   ```json
   {
     "twitter": {
       "personal_account": "@dummy_account",
       "official_accounts": ["@dummy_official1", "@dummy_official2"],
       "hashtags": ["#さなのいす", "諸橋沙夏"],
       "engagement_threshold": {
         "likes": 10000,
         "views": 100000
       }
     }
   }
   ```

5. **システムプロンプトの作成**
   - `config/prompts/`配下に各Agentのプロンプトファイルを作成
   - 要件定義書「2.1.3」の内容を各ファイルに記述

### フェーズ2: データベース層の実装
1. **データベース管理クラス**
   - `src/database/db_manager.py`: 環境に応じてSQLite/PostgreSQL切り替え
   - 要件定義書「4.3 環境変数」のDB_TYPEで判定

2. **SQLAlchemyモデル定義**
   - `src/database/models.py`
   - itemsテーブル、executionsテーブルのモデル作成
   - 要件定義書「2.5.2 テーブル設計」参照

3. **データベース初期化スクリプト**
   - `scripts/init_database.py`: テーブル作成、インデックス作成
   - `scripts/test_connection.py`: DB接続テスト

### フェーズ3: 情報収集Agent層の実装
1. **基底Agentクラス**
   - `src/agents/base_agent.py`
   - プロンプト読み込み機能
   - リトライロジック（最大2回、5秒間隔）
   - エラーハンドリング

2. **各専門Agent実装**
   - `src/agents/twitter_agent.py`: snscrapeを使用したX収集
   - `src/agents/yahoo_agent.py`: BeautifulSoupでYahoo!ニュース収集
   - `src/agents/modelpress_agent.py`: BeautifulSoupでモデルプレス収集
   - 各Agentは専用プロンプトを読み込んで動作
   - 統一されたJSON形式で出力

3. **プロンプト管理クラス**
   - `src/utils/prompt_manager.py`
   - プロンプトファイルの読み込み
   - settings.jsonの動的埋め込み（Judge Agent用）

### フェーズ4: Claude判定処理の実装
1. **Claude処理クラス**
   - `src/processors/claude_processor.py`
   - Judge Agentプロンプトを使用
   - 収集データを一括でClaude APIに送信
   - 関連性・重要度・カテゴリ・要約を判定
   - 要件定義書「2.2」の判定ロジック実装

2. **データ統合・重複排除**
   - URL単位での重複チェック
   - 各Agentからのデータを統合
   - 閾値以下のデータをフィルタリング

### フェーズ5: 実行制御の実装
1. **メイン実行ロジック**
   - `main.py`: エントリーポイント
   - 実行フロー:
     1. 各Agent順次実行（リトライ付き）
     2. 1つでも失敗したら中断
     3. データ統合
     4. Claude判定
     5. DB保存
     6. ログ記録

2. **ログ管理**
   - `src/utils/logger.py`
   - 実行状態、エラー詳細、各Agent結果を記録
   - 要件定義書「2.3.3 エラーハンドリング」参照

### フェーズ6: Web UIの実装
1. **Flaskアプリケーション**
   - `src/web/app.py`: Flaskアプリ初期化
   - `src/web/api.py`: APIエンドポイント実装
   - 要件定義書「6. APIエンドポイント仕様」参照

2. **APIエンドポイント**
   - GET `/api/items`: 情報一覧取得（フィルタ対応）
   - POST `/api/execute`: 情報収集実行
   - GET `/api/status`: 実行状態取得
   - GET `/api/logs`: 実行ログ取得

3. **フロントエンド**
   - `src/web/templates/index.html`: メインUI
   - `src/web/static/style.css`: スタイル
   - `src/web/static/main.js`: フロントエンドロジック
   - 要件定義書「2.4 Web閲覧機能」の画面構成を実装
   - シンプルでクリーンなデザイン

4. **UI機能**
   - 実行ボタン（実行中は無効化）
   - フィルタリング（期間、重要度、カテゴリ、キーワード）
   - ページネーション（20件/ページ）
   - 外部リンク（別タブで開く）

### フェーズ7: テスト・デバッグ
1. **ユニットテスト**
   - 各Agentの動作確認
   - Claude判定処理のテスト
   - DB操作のテスト

2. **統合テスト**
   - エンドツーエンドの実行フロー確認
   - エラーハンドリング確認
   - リトライ動作確認

3. **README作成**
   - セットアップ手順
   - 使用方法
   - トラブルシューティング

## 実装の優先順位

**最優先（MVPとして動作させる）**
1. データベース層（SQLite版のみ）
2. X Agent（snscrape使用）
3. Claude判定処理
4. 基本的なWeb UI（実行ボタン＋一覧表示のみ）

**次に実装**
5. Yahoo News Agent
6. Model Press Agent
7. フィルタリング機能
8. エラーハンドリング・リトライ

**最後に実装**
9. PostgreSQL対応
10. ログ機能の充実
11. UI の洗練

## 実装時の注意事項

### 開発環境
- まずはSQLiteで開発（DB_TYPE=sqlite）
- PostgreSQL対応は後回し
- ダミーアカウントで動作確認

### エラーハンドリング
- 各Agentで適切な例外処理
- リトライロジックの実装
- 詳細なエラーメッセージ

### セキュリティ
- `.env`ファイルは絶対にGitに含めない
- APIキーのハードコーディング禁止
- スクレイピング時のUser-Agent設定

### コード品質
- 各関数にdocstring
- 型ヒント（Type Hints）の使用
- PEP 8スタイルガイド準拠
- 適切なモジュール分割

### Claude API使用
- バッチ処理でトークン数を最適化
- レート制限に注意
- エラー時の適切なハンドリング

### スクレイピング
- robots.txt の確認
- 適切なリクエスト間隔
- User-Agentの設定
- 構造変更に対する柔軟性

## 動作確認項目

実装完了後、以下を確認してください：

### 基本動作
- [ ] データベース初期化が成功する
- [ ] 各Agentが個別に動作する
- [ ] Claude判定が正しく動作する
- [ ] データがDBに保存される
- [ ] Web UIが表示される
- [ ] 実行ボタンで収集が開始される

### エラーハンドリング
- [ ] Agent失敗時にリトライする
- [ ] 2回失敗後に処理が中断する
- [ ] 詳細なエラーメッセージが表示される
- [ ] 実行中はボタンが無効化される

### フィルタリング
- [ ] 期間フィルタが動作する
- [ ] 重要度フィルタが動作する
- [ ] カテゴリフィルタが動作する
- [ ] キーワード検索が動作する

### UI/UX
- [ ] 情報が見やすく表示される
- [ ] リンクが別タブで開く
- [ ] ページネーションが動作する
- [ ] レスポンシブデザイン（モバイル対応不要）

## 実装の進め方

1. **段階的な実装**
   - 一度に全てを実装せず、フェーズごとに動作確認
   - 各フェーズ完了後に動作テスト

2. **シンプルさ重視**
   - 最初は最小限の機能で動作させる
   - 動いてから機能を追加

3. **ログとデバッグ**
   - print文やloggingで動作を確認
   - 各段階でデータの中身を確認

4. **ドキュメント**
   - コードにコメントを残す
   - README に使い方を記載

## サンプルコードスニペット

### データベース接続（参考）
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self):
        db_type = os.getenv('DB_TYPE', 'sqlite')
        
        if db_type == 'postgresql':
            db_url = self._get_postgresql_url()
        else:
            db_url = "sqlite:///data/natsu_dev.db"
        
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
```

### Agent基底クラス（参考）
```python
import time
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name, prompt_manager):
        self.name = name
        self.prompt = prompt_manager.load_prompt(name)
        self.max_retries = 2
        self.retry_interval = 5
    
    def execute_with_retry(self):
        for attempt in range(self.max_retries + 1):
            try:
                result = self.collect()
                return {"status": "success", "data": result}
            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(self.retry_interval)
                    continue
                else:
                    return {
                        "status": "failed",
                        "error": str(e),
                        "agent": self.name
                    }
    
    @abstractmethod
    def collect(self):
        """各Agentで実装"""
        pass
```

## 質問・不明点があれば

実装中に以下のような判断が必要になった場合は、合理的な選択をしてください：
- ライブラリの選択
- エラーメッセージの文言
- UIの細かいデザイン
- ログの詳細レベル

基本的には要件定義書に従い、記載のない細部は開発者の判断で実装してOKです。

## 最終成果物

以下のファイル・機能が揃った状態を目指してください：

1. **動作するアプリケーション**
   - ローカルで起動できる
   - 情報収集が実行できる
   - Web UIで結果を確認できる

2. **ドキュメント**
   - README.md（セットアップ・使用方法）
   - コード内のコメント

3. **設定ファイル**
   - .env.example（テンプレート）
   - config配下の各種設定

4. **スクリプト**
   - データベース初期化
   - 接続テスト

頑張ってください！
