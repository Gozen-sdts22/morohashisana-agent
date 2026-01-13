"""
SQLAlchemy models for the Natsu Agent database.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP,
    DECIMAL, JSON, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Item(Base):
    """
    Itemsテーブル: 収集した情報を格納
    """
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # twitter/yahoo_news/modelpress
    source_detail = Column(Text)  # ソース詳細
    title = Column(Text)  # タイトル
    content = Column(Text)  # 本文
    summary = Column(String(100))  # Claude生成要約（50文字）
    url = Column(Text, nullable=False, unique=True)  # 情報URL（重複チェック用）
    published_at = Column(TIMESTAMP(timezone=True), nullable=False)  # 公開日時
    relevance_score = Column(Integer)  # 関連性スコア（0-100）
    importance_score = Column(Integer)  # 重要度スコア（0-100）
    importance_level = Column(String(20))  # 重要度レベル（high/medium/low）
    category = Column(String(100))  # カテゴリ
    claude_reason = Column(Text)  # 判定理由
    metrics = Column(JSON)  # メトリクス（いいね数等）
    collected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())  # 収集日時
    execution_id = Column(String(50))  # 実行ID

    # インデックス
    __table_args__ = (
        Index('idx_published_at', 'published_at'),
        Index('idx_importance', 'importance_score'),
        Index('idx_category', 'category'),
        Index('idx_execution', 'execution_id'),
    )

    def __repr__(self):
        return f"<Item(id={self.id}, source={self.source}, title={self.title[:30] if self.title else 'N/A'}...)>"

    def to_dict(self):
        """モデルを辞書形式に変換"""
        return {
            'id': self.id,
            'source': self.source,
            'source_detail': self.source_detail,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'url': self.url,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'relevance_score': self.relevance_score,
            'importance_score': self.importance_score,
            'importance_level': self.importance_level,
            'category': self.category,
            'claude_reason': self.claude_reason,
            'metrics': self.metrics,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'execution_id': self.execution_id,
        }


class Execution(Base):
    """
    Executionsテーブル: 実行ログを格納
    """
    __tablename__ = 'executions'

    id = Column(String(50), primary_key=True)  # 実行ID（exec_YYYYMMDD_HHMMSS）
    started_at = Column(TIMESTAMP(timezone=True), nullable=False)  # 開始日時
    completed_at = Column(TIMESTAMP(timezone=True))  # 完了日時
    status = Column(String(20), nullable=False)  # ステータス（running/success/failed）
    total_collected = Column(Integer, default=0)  # 収集総数
    total_saved = Column(Integer, default=0)  # 保存総数
    error_message = Column(Text)  # エラーメッセージ
    agent_results = Column(JSON)  # 各Agent結果
    claude_processed = Column(Integer)  # Claude処理件数
    claude_duration_sec = Column(DECIMAL(10, 2))  # Claude処理時間

    # インデックス
    __table_args__ = (
        Index('idx_executions_started', 'started_at'),
    )

    def __repr__(self):
        return f"<Execution(id={self.id}, status={self.status}, total_saved={self.total_saved})>"

    def to_dict(self):
        """モデルを辞書形式に変換"""
        return {
            'id': self.id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'total_collected': self.total_collected,
            'total_saved': self.total_saved,
            'error_message': self.error_message,
            'agent_results': self.agent_results,
            'claude_processed': self.claude_processed,
            'claude_duration_sec': float(self.claude_duration_sec) if self.claude_duration_sec else None,
        }
