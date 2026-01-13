"""
プロンプト管理クラス
config/prompts/ 配下のプロンプトファイルを読み込み、管理する
"""
import os
import json
from typing import Dict, Any


class PromptManager:
    """
    プロンプトファイルを読み込み、管理するクラス
    """

    def __init__(self, prompts_dir: str = 'config/prompts'):
        """
        初期化

        Args:
            prompts_dir: プロンプトファイルが格納されているディレクトリパス
        """
        self.prompts_dir = prompts_dir
        self._prompts_cache: Dict[str, str] = {}

    def load_prompt(self, agent_name: str) -> str:
        """
        指定されたAgentのプロンプトを読み込む

        Args:
            agent_name: Agent名（twitter, yahoo, modelpress, judge）

        Returns:
            プロンプト文字列

        Raises:
            FileNotFoundError: プロンプトファイルが見つからない場合
        """
        # キャッシュに存在する場合はキャッシュから返す
        if agent_name in self._prompts_cache:
            return self._prompts_cache[agent_name]

        # プロンプトファイルのパスを構築
        prompt_file = os.path.join(self.prompts_dir, f'{agent_name}_agent_prompt.txt')

        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {prompt_file}")

        # ファイルを読み込み
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()

        # キャッシュに保存
        self._prompts_cache[agent_name] = prompt

        return prompt

    def load_judge_prompt_with_settings(self, settings_path: str = 'config/settings.json') -> str:
        """
        Judge Agentプロンプトを読み込み、設定ファイルの内容を埋め込む

        Args:
            settings_path: 設定ファイルのパス

        Returns:
            設定が埋め込まれたプロンプト文字列
        """
        # 基本プロンプトを読み込み
        prompt = self.load_prompt('judge')

        # 設定ファイルを読み込み
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        # 判定基準を取得
        criteria = settings.get('judgment_criteria', {})
        importance_levels = criteria.get('importance_levels', {})
        categories = criteria.get('categories', [])
        filtering = settings.get('filtering', {})

        # プロンプトにデータを埋め込み
        # High keywords
        high_keywords = importance_levels.get('high', {}).get('keywords', [])
        prompt = prompt.replace('{HIGH_KEYWORDS}', ', '.join(high_keywords))

        # Medium keywords
        medium_keywords = importance_levels.get('medium', {}).get('keywords', [])
        prompt = prompt.replace('{MEDIUM_KEYWORDS}', ', '.join(medium_keywords))

        # Low keywords
        low_keywords = importance_levels.get('low', {}).get('keywords', [])
        prompt = prompt.replace('{LOW_KEYWORDS}', ', '.join(low_keywords))

        # Categories
        categories_str = '\n'.join([f'- {cat}' for cat in categories])
        prompt = prompt.replace('{CATEGORIES}', categories_str)

        # Excluded keywords
        excluded_keywords = filtering.get('excluded_keywords', [])
        prompt = prompt.replace('{EXCLUDED_KEYWORDS}', ', '.join(excluded_keywords))

        return prompt

    def clear_cache(self):
        """
        キャッシュをクリア
        """
        self._prompts_cache.clear()
