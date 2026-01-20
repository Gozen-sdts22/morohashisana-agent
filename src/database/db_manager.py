"""
Database Manager for Natsu Agent.
Handles database connections for both SQLite (development) and PostgreSQL (production).
"""
import os
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

from .models import Base

# Load environment variables
load_dotenv()


class DatabaseManager:
    """
    データベース接続を管理するクラス
    環境変数に基づいてSQLiteまたはPostgreSQLに接続する
    """

    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'sqlite')
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False  # コミット後も属性を保持し、Detachedエラーを避ける
        )

    def _create_engine(self):
        """
        環境変数に基づいてデータベースエンジンを作成
        """
        if self.db_type == 'postgresql':
            db_url = self._get_postgresql_url()
            # PostgreSQL用のエンジン設定
            return create_engine(
                db_url,
                pool_pre_ping=True,  # 接続の健全性チェック
                echo=False  # SQLログを出力しない（必要に応じてTrue）
            )
        else:
            # SQLite用のエンジン設定（開発環境）
            db_path = os.getenv('DB_PATH', 'data/natsu_dev.db')

            # dataディレクトリが存在しない場合は作成
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            db_url = f'sqlite:///{db_path}'
            return create_engine(
                db_url,
                connect_args={'check_same_thread': False},  # SQLiteでスレッド制限を解除
                poolclass=StaticPool,  # 開発環境ではStaticPool使用
                echo=False
            )

    def _get_postgresql_url(self) -> str:
        """
        PostgreSQL接続URLを環境変数から構築
        """
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_ssl_mode = os.getenv('DB_SSL_MODE', 'require')

        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError(
                "PostgreSQL接続に必要な環境変数が設定されていません。"
                "DB_HOST, DB_NAME, DB_USER, DB_PASSWORD を確認してください。"
            )

        # PostgreSQL接続URL構築
        url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

        if db_ssl_mode:
            url += f'?sslmode={db_ssl_mode}'

        return url

    def create_tables(self):
        """
        全テーブルを作成
        """
        Base.metadata.create_all(bind=self.engine)
        print(f"テーブルを作成しました（DB Type: {self.db_type}）")

    def drop_tables(self):
        """
        全テーブルを削除（注意: 本番環境では使用しないこと）
        """
        Base.metadata.drop_all(bind=self.engine)
        print(f"テーブルを削除しました（DB Type: {self.db_type}）")

    def get_session(self) -> Session:
        """
        データベースセッションを取得
        """
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """
        データベース接続をテスト
        """
        try:
            with self.engine.connect() as conn:
                # SQLAlchemy 2.x では text() を使って文字列クエリを実行する
                conn.execute(text("SELECT 1"))
            # Windows コンソールの文字コード環境でも問題が出ないよう、特殊記号は使わない
            print(f"[OK] データベース接続成功（{self.db_type}）")
            return True
        except Exception as e:
            print(f"[ERROR] データベース接続失敗: {e}")
            return False

    def close(self):
        """
        データベース接続を閉じる
        """
        self.engine.dispose()


# グローバルなデータベースマネージャーインスタンス
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    データベースマネージャーのシングルトンインスタンスを取得
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
