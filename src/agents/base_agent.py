"""
Agent基底クラス
全ての情報収集Agentの基底となる抽象クラス
"""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.utils.prompt_manager import PromptManager


class BaseAgent(ABC):
    """
    情報収集Agentの基底クラス
    """

    def __init__(
        self,
        name: str,
        prompt_manager: PromptManager,
        max_retries: int = 2,
        retry_interval: int = 5
    ):
        """
        初期化

        Args:
            name: Agent名
            prompt_manager: プロンプトマネージャー
            max_retries: 最大リトライ回数
            retry_interval: リトライ間隔（秒）
        """
        self.name = name
        self.prompt_manager = prompt_manager
        self.max_retries = max_retries
        self.retry_interval = retry_interval

        # プロンプトを読み込み
        try:
            self.prompt = self.prompt_manager.load_prompt(name)
        except FileNotFoundError:
            self.prompt = None
            print(f"警告: {name} のプロンプトファイルが見つかりません")

    def execute_with_retry(self) -> Dict[str, Any]:
        """
        リトライロジック付きで収集を実行

        Returns:
            実行結果の辞書
            {
                "status": "success" or "failed",
                "data": 収集したデータのリスト (成功時),
                "error": エラーメッセージ (失敗時),
                "agent": Agent名,
                "attempts": 試行回数
            }
        """
        for attempt in range(self.max_retries + 1):
            try:
                print(f"[{self.name}] 収集開始 (試行 {attempt + 1}/{self.max_retries + 1})")

                # 実際の収集処理を実行
                result = self.collect()

                print(f"[{self.name}] 収集成功: {len(result)} 件")

                return {
                    "status": "success",
                    "data": result,
                    "agent": self.name,
                    "attempts": attempt + 1,
                    "count": len(result)
                }

            except Exception as e:
                error_msg = str(e)
                print(f"[{self.name}] エラー発生 (試行 {attempt + 1}/{self.max_retries + 1}): {error_msg}")

                # 最後の試行でもない場合はリトライ
                if attempt < self.max_retries:
                    print(f"[{self.name}] {self.retry_interval}秒後にリトライします...")
                    time.sleep(self.retry_interval)
                    continue
                else:
                    # 全ての試行が失敗した場合
                    print(f"[{self.name}] 全ての試行が失敗しました")
                    return {
                        "status": "failed",
                        "error": error_msg,
                        "agent": self.name,
                        "attempts": attempt + 1
                    }

    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """
        情報収集の実装（各Agentでオーバーライド）

        Returns:
            収集したデータのリスト
            各データは以下の形式:
            {
                "source": ソース種別,
                "source_detail": ソース詳細,
                "title": タイトル,
                "content": 本文,
                "url": URL,
                "published_at": 公開日時（ISO 8601形式）,
                "metrics": メトリクス辞書,
                "author": 著者名,
                "author_account": 著者アカウント
            }

        Raises:
            Exception: 収集に失敗した場合
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}(name={self.name})>"
