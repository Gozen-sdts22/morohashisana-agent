"""
Claude判定処理クラス
Anthropic APIを使用して収集した情報の関連性・重要度を判定する
"""
import os
import json
import time
from typing import List, Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv

from src.utils.prompt_manager import PromptManager

# 環境変数を読み込み
load_dotenv()


class ClaudeProcessor:
    """
    Claude APIを使用して情報を判定するプロセッサー
    """

    def __init__(self, prompt_manager: PromptManager, settings_path: str = 'config/settings.json'):
        """
        初期化

        Args:
            prompt_manager: プロンプトマネージャー
            settings_path: 設定ファイルのパス
        """
        self.prompt_manager = prompt_manager
        self.settings_path = settings_path

        # Claude APIキーを取得
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            raise ValueError("CLAUDE_API_KEYが環境変数に設定されていません")

        # Anthropic クライアントを初期化
        self.client = Anthropic(api_key=api_key)

        # Judge Agentプロンプトを読み込み（設定埋め込み済み）
        self.judge_prompt = self.prompt_manager.load_judge_prompt_with_settings(
            settings_path
        )

        # 設定を読み込み
        with open(settings_path, 'r', encoding='utf-8') as f:
            self.settings = json.load(f)

        # フィルタリング条件
        self.filtering = self.settings.get('filtering', {})
        self.min_relevance_score = self.filtering.get('min_relevance_score', 30)
        self.min_importance_score = self.filtering.get('min_importance_score', 0)
        self.excluded_keywords = self.filtering.get('excluded_keywords', [])

    def judge_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        収集した情報を一括で判定

        Args:
            items: 収集した情報のリスト

        Returns:
            判定結果が追加された情報のリスト
            フィルタリング条件を満たさないものは除外される
        """
        if not items:
            print("[ClaudeProcessor] 判定対象のアイテムがありません")
            return []

        print(f"[ClaudeProcessor] {len(items)} 件のアイテムを判定中...")

        start_time = time.time()

        try:
            # Claude APIで判定
            judgments = self._call_claude_api(items)

            # 判定結果をアイテムにマージ
            judged_items = self._merge_judgments(items, judgments)

            # フィルタリング
            filtered_items = self._filter_items(judged_items)

            duration = time.time() - start_time

            print(f"[ClaudeProcessor] 判定完了: {len(items)} 件 -> {len(filtered_items)} 件（{duration:.2f}秒）")

            return filtered_items, duration

        except Exception as e:
            print(f"[ClaudeProcessor] 判定中にエラー: {e}")
            raise

    def _call_claude_api(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Claude APIを呼び出して判定を取得

        Args:
            items: 収集した情報のリスト

        Returns:
            判定結果のリスト
        """
        # アイテムをJSON形式で整形
        items_json = json.dumps(items, ensure_ascii=False, indent=2)

        # ユーザープロンプトを構築
        user_prompt = f"""
以下の情報について、関連性・重要度を判定してください。

【収集した情報】
{items_json}

各情報について、判定結果をJSON配列形式で返してください。
"""

        try:
            # Claude APIを呼び出し
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # 最新のSonnet 4モデル
                max_tokens=4096,
                system=self.judge_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            # レスポンスからテキストを取得
            response_text = message.content[0].text

            # JSONをパース
            judgments = self._parse_claude_response(response_text)

            return judgments

        except Exception as e:
            raise Exception(f"Claude API呼び出しに失敗しました: {e}")

    def _parse_claude_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Claudeのレスポンスから判定結果をパース

        Args:
            response_text: Claudeのレスポンステキスト

        Returns:
            判定結果のリスト
        """
        try:
            # JSON部分を抽出（```json ブロックがある場合を考慮）
            if '```json' in response_text:
                # コードブロックから抽出
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_text = response_text[start:end].strip()
            elif '```' in response_text:
                # シンプルなコードブロックから抽出
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                json_text = response_text[start:end].strip()
            else:
                # コードブロックがない場合はそのままパース
                json_text = response_text.strip()

            # JSONをパース
            judgments = json.loads(json_text)

            # リスト形式でない場合はリストに変換
            if isinstance(judgments, dict):
                judgments = [judgments]

            return judgments

        except json.JSONDecodeError as e:
            print(f"[ClaudeProcessor] JSON パースエラー: {e}")
            print(f"レスポンス: {response_text}")
            raise Exception(f"Claudeのレスポンスをパースできませんでした: {e}")

    def _merge_judgments(
        self,
        items: List[Dict[str, Any]],
        judgments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        アイテムと判定結果をマージ

        Args:
            items: 元のアイテムリスト
            judgments: 判定結果リスト

        Returns:
            判定結果がマージされたアイテムリスト
        """
        # URLをキーとした判定結果の辞書を作成
        judgment_dict = {}
        for judgment in judgments:
            url = judgment.get('url')
            if url:
                judgment_dict[url] = judgment

        # アイテムに判定結果を追加
        merged_items = []
        for item in items:
            url = item.get('url')
            if url and url in judgment_dict:
                judgment = judgment_dict[url]

                # 判定結果をアイテムに追加
                item['relevance_score'] = judgment.get('relevance_score')
                item['importance_score'] = judgment.get('importance_score')
                item['importance_level'] = judgment.get('importance_level')
                item['category'] = judgment.get('category')
                item['summary'] = judgment.get('summary')
                item['claude_reason'] = judgment.get('claude_reason')

                merged_items.append(item)
            else:
                # 判定結果がない場合はスキップ
                print(f"[ClaudeProcessor] 警告: {url} の判定結果が見つかりません")

        return merged_items

    def _filter_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        フィルタリング条件に基づいてアイテムをフィルタ

        Args:
            items: アイテムリスト

        Returns:
            フィルタ後のアイテムリスト
        """
        filtered_items = []

        for item in items:
            # 関連性スコアチェック
            relevance_score = item.get('relevance_score', 0)
            if relevance_score < self.min_relevance_score:
                continue

            # 重要度スコアチェック
            importance_score = item.get('importance_score', 0)
            if importance_score < self.min_importance_score:
                continue

            # 除外キーワードチェック
            content = item.get('content', '') or ''
            title = item.get('title', '') or ''
            full_text = f"{title} {content}"

            if any(keyword in full_text for keyword in self.excluded_keywords):
                print(f"[ClaudeProcessor] 除外キーワードを含むため除外: {item.get('url')}")
                continue

            # フィルタを通過
            filtered_items.append(item)

        return filtered_items
