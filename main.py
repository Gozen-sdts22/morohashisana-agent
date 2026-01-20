"""
諸橋沙夏情報収集Agent - メイン実行スクリプト
情報収集、判定、データベース保存の全体フローを制御
"""
import os
import sys
import json
from datetime import datetime
import pytz

from src.utils.logger import get_logger
from src.utils.prompt_manager import PromptManager
from src.database.db_manager import get_db_manager
from src.database.models import Item, Execution
from src.agents.twitter_agent import TwitterAgent
from src.agents.yahoo_agent import YahooAgent
from src.agents.modelpress_agent import ModelpressAgent
from src.processors.claude_processor import ClaudeProcessor

# ロガーを取得
logger = get_logger()


class NatsuAgentExecutor:
    """
    諸橋沙夏情報収集Agentのメイン実行クラス
    """

    def __init__(self):
        """
        初期化
        """
        # プロンプトマネージャー
        self.prompt_manager = PromptManager()

        # データベースマネージャー
        self.db_manager = get_db_manager()

        # 設定を読み込み
        with open('config/sources.json', 'r', encoding='utf-8') as f:
            self.sources_config = json.load(f)

        # 各Agentを初期化
        self.agents = [
            TwitterAgent(self.prompt_manager, self.sources_config.get('twitter', {})),
            YahooAgent(self.prompt_manager, self.sources_config.get('yahoo_news', {})),
            ModelpressAgent(self.prompt_manager, self.sources_config.get('modelpress', {}))
        ]

        # Claude プロセッサー
        self.claude_processor = ClaudeProcessor(self.prompt_manager)

    def execute(self) -> dict:
        """
        情報収集を実行

        Returns:
            実行結果の辞書
        """
        # 実行IDを生成
        jst = pytz.timezone('Asia/Tokyo')
        started_at = datetime.now(jst)
        execution_id = started_at.strftime('exec_%Y%m%d_%H%M%S')

        logger.info("=" * 60)
        logger.info(f"情報収集開始: {execution_id}")
        logger.info("=" * 60)

        # 実行ログをDBに記録
        execution = self._create_execution_record(execution_id, started_at)

        try:
            # 1. 各Agentで情報収集
            logger.info("[1/4] 各Agentで情報収集中...")
            all_items, agent_results = self._collect_from_agents()

            if not all_items:
                logger.warning("収集されたアイテムがありません")
                self._update_execution_record(
                    execution,
                    status='success',
                    total_collected=0,
                    total_saved=0,
                    agent_results=agent_results
                )
                return {
                    'status': 'success',
                    'execution_id': execution_id,
                    'total_collected': 0,
                    'total_saved': 0,
                    'message': '収集されたアイテムがありませんでした'
                }

            logger.info(f"合計 {len(all_items)} 件のアイテムを収集")

            # 2. データ統合（重複排除）
            logger.info("[2/4] データ統合・重複排除中...")
            unique_items = self._remove_duplicates(all_items)
            logger.info(f"重複排除後: {len(unique_items)} 件")

            # 3. Claude判定
            logger.info("[3/4] Claude判定中...")
            judged_items, claude_duration = self.claude_processor.judge_items(unique_items)
            logger.info(f"判定完了: {len(judged_items)} 件が基準を満たしました")

            # 4. データベースに保存
            logger.info("[4/4] データベースに保存中...")
            saved_count = self._save_to_database(judged_items, execution_id)
            logger.info(f"保存完了: {saved_count} 件")

            # 実行ログを更新
            self._update_execution_record(
                execution,
                status='success',
                total_collected=len(all_items),
                total_saved=saved_count,
                agent_results=agent_results,
                claude_processed=len(judged_items),
                claude_duration=claude_duration
            )

            logger.info("=" * 60)
            logger.info(f"情報収集完了: {execution_id}")
            logger.info(f"収集: {len(all_items)} 件 -> 保存: {saved_count} 件")
            logger.info("=" * 60)

            return {
                'status': 'success',
                'execution_id': execution_id,
                'total_collected': len(all_items),
                'total_saved': saved_count,
                'message': f'{saved_count} 件の情報を保存しました'
            }

        except Exception as e:
            logger.error(f"実行中にエラーが発生しました: {e}", exc_info=True)

            # 実行ログにエラーを記録
            self._update_execution_record(
                execution,
                status='failed',
                error_message=str(e)
            )

            return {
                'status': 'failed',
                'execution_id': execution_id,
                'error': str(e),
                'message': '情報収集に失敗しました'
            }

    def _collect_from_agents(self):
        """
        各Agentで情報収集

        Returns:
            (全アイテムリスト, Agent結果辞書)

        Raises:
            Exception: いずれかのAgentが失敗した場合
        """
        all_items = []
        agent_results = {}

        for agent in self.agents:
            result = agent.execute_with_retry()
            agent_results[agent.name] = {
                'status': result['status'],
                'attempts': result.get('attempts', 0),
                'count': result.get('count', 0)
            }

            if result['status'] == 'failed':
                # 1つでもAgentが失敗したら中断
                error_msg = f"{agent.name} Agent が失敗しました: {result.get('error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 成功したデータを追加
            all_items.extend(result.get('data', []))

        return all_items, agent_results

    def _remove_duplicates(self, items):
        """
        URL単位で重複を排除

        Args:
            items: アイテムリスト

        Returns:
            重複排除後のアイテムリスト
        """
        seen_urls = set()
        unique_items = []

        for item in items:
            url = item.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_items.append(item)

        return unique_items

    def _save_to_database(self, items, execution_id):
        """
        アイテムをデータベースに保存

        Args:
            items: 保存するアイテムリスト
            execution_id: 実行ID

        Returns:
            保存した件数
        """
        session = self.db_manager.get_session()
        saved_count = 0

        try:
            for item in items:
                # published_at を datetime オブジェクトに変換（文字列の場合）
                published_at = item.get('published_at')
                if isinstance(published_at, str):
                    try:
                        # ISO 8601 文字列を datetime に変換
                        published_at = datetime.fromisoformat(published_at)
                    except ValueError:
                        # 変換できない場合は現在時刻で代替
                        published_at = datetime.now(pytz.timezone('Asia/Tokyo'))
                item['published_at'] = published_at

                # URLで既存チェック
                existing = session.query(Item).filter_by(url=item['url']).first()
                if existing:
                    logger.debug(f"重複スキップ: {item['url']}")
                    continue

                # 新規アイテムを作成
                new_item = Item(
                    source=item.get('source'),
                    source_detail=item.get('source_detail'),
                    title=item.get('title'),
                    content=item.get('content'),
                    summary=item.get('summary'),
                    url=item.get('url'),
                    published_at=item.get('published_at'),
                    relevance_score=item.get('relevance_score'),
                    importance_score=item.get('importance_score'),
                    importance_level=item.get('importance_level'),
                    category=item.get('category'),
                    claude_reason=item.get('claude_reason'),
                    metrics=item.get('metrics'),
                    execution_id=execution_id
                )
                session.add(new_item)
                saved_count += 1

            session.commit()
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"データベース保存エラー: {e}")
            raise
        finally:
            session.close()

    def _create_execution_record(self, execution_id, started_at):
        """
        実行レコードを作成

        Args:
            execution_id: 実行ID
            started_at: 開始日時

        Returns:
            Executionオブジェクト
        """
        session = self.db_manager.get_session()
        try:
            execution = Execution(
                id=execution_id,
                started_at=started_at,
                status='running'
            )
            session.add(execution)
            session.commit()
            return execution
        finally:
            session.close()

    def _update_execution_record(self, execution, **kwargs):
        """
        実行レコードを更新

        Args:
            execution: Executionオブジェクト
            **kwargs: 更新する項目
        """
        session = self.db_manager.get_session()
        try:
            exec_record = session.query(Execution).filter_by(id=execution.id).first()
            if exec_record:
                # 完了日時を設定
                jst = pytz.timezone('Asia/Tokyo')
                exec_record.completed_at = datetime.now(jst)

                # その他のフィールドを更新
                for key, value in kwargs.items():
                    setattr(exec_record, key, value)

                session.commit()
        finally:
            session.close()


def main():
    """
    メイン関数
    """
    try:
        executor = NatsuAgentExecutor()
        result = executor.execute()

        # 結果を表示
        print("\n" + "=" * 60)
        if result['status'] == 'success':
            print("[OK] 実行成功")
            print(f"実行ID: {result['execution_id']}")
            print(f"収集: {result.get('total_collected', 0)} 件")
            print(f"保存: {result.get('total_saved', 0)} 件")
        else:
            print("[ERROR] 実行失敗")
            print(f"エラー: {result.get('error', 'Unknown error')}")
        print("=" * 60)

        return 0 if result['status'] == 'success' else 1

    except KeyboardInterrupt:
        print("\n\n中断されました")
        return 130
    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
