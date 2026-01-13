"""
ログ管理クラス
アプリケーションのログを設定・管理する
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


def setup_logger(name: str = 'natsu_agent', log_file: str = 'logs/app.log') -> logging.Logger:
    """
    ロガーをセットアップ

    Args:
        name: ロガー名
        log_file: ログファイルのパス

    Returns:
        設定済みのロガー
    """
    # ログディレクトリが存在しない場合は作成
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # ロガーを取得
    logger = logging.getLogger(name)

    # すでに設定済みの場合はそのまま返す
    if logger.handlers:
        return logger

    # ログレベルを環境変数から取得
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # フォーマッターを作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ファイルハンドラー（ローテーション付き）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ハンドラーを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# グローバルロガー
_global_logger = None


def get_logger() -> logging.Logger:
    """
    グローバルロガーを取得

    Returns:
        設定済みのロガー
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger()
    return _global_logger
