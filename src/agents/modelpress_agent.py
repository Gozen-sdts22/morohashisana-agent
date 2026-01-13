"""
モデルプレス情報収集Agent
BeautifulSoupを使用してモデルプレスから記事を収集する
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timezone
import pytz
from urllib.parse import quote

from .base_agent import BaseAgent


class ModelpressAgent(BaseAgent):
    """
    モデルプレスから諸橋沙夏さんに関する記事を収集するAgent
    """

    def __init__(self, prompt_manager, config: Dict[str, Any]):
        """
        初期化

        Args:
            prompt_manager: プロンプトマネージャー
            config: 設定辞書（config/sources.jsonのmodelpress部分）
        """
        super().__init__('modelpress', prompt_manager)
        self.config = config
        self.search_keyword = config.get('search_keyword', '諸橋沙夏')
        self.base_url = config.get('base_url', 'https://mdpr.jp/search')

        # User-Agent設定
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def collect(self) -> List[Dict[str, Any]]:
        """
        モデルプレスから記事を収集

        Returns:
            収集した記事のリスト
        """
        try:
            articles = self._search_news()
            return articles
        except Exception as e:
            print(f"[ModelpressAgent] 記事収集でエラー: {e}")
            # エラー時はダミーデータを返す
            print(f"[ModelpressAgent] ダミーデータを返します")
            return self._get_dummy_articles()

    def _search_news(self) -> List[Dict[str, Any]]:
        """
        モデルプレスで検索

        Returns:
            記事のリスト
        """
        # 検索URLを構築
        search_url = f"{self.base_url}?q={quote(self.search_keyword)}"

        try:
            # リクエスト送信
            response = requests.get(
                search_url,
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()

            # HTMLをパース
            soup = BeautifulSoup(response.content, 'html.parser')

            # 記事を抽出（実際のHTML構造に合わせて調整が必要）
            articles = self._parse_articles(soup)

            return articles

        except requests.RequestException as e:
            raise Exception(f"モデルプレスへのリクエストに失敗しました: {e}")

    def _parse_articles(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        HTMLから記事情報を抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            記事のリスト

        Note:
            モデルプレスのHTML構造は変更される可能性があるため、
            実際の構造に合わせて調整が必要です。
            ここではダミーデータを返す実装としています。
        """
        # 注: モデルプレスのHTML構造は変更される可能性があるため、
        # 実際の運用では定期的なメンテナンスが必要です。
        # この実装ではダミーデータを返します。

        print("[ModelpressAgent] HTML解析（実装未完了のためダミーデータ使用）")
        return self._get_dummy_articles()

    def _format_article(
        self,
        title: str,
        summary: str,
        url: str,
        published_at: str,
        thumbnail_url: str = None
    ) -> Dict[str, Any]:
        """
        記事データを統一フォーマットに変換

        Args:
            title: 記事タイトル
            summary: 記事要約
            url: 記事URL
            published_at: 公開日時
            thumbnail_url: サムネイル画像URL

        Returns:
            フォーマット済み記事データ
        """
        return {
            "source": "modelpress",
            "source_detail": "モデルプレス",
            "title": title,
            "content": summary,
            "url": url,
            "published_at": published_at,
            "metrics": {
                "thumbnail_url": thumbnail_url
            } if thumbnail_url else None,
            "author": None,
            "author_account": None
        }

    def _get_dummy_articles(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        ダミー記事データを生成（開発・テスト用）

        Args:
            count: 生成するダミーデータの件数

        Returns:
            ダミー記事のリスト
        """
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)

        dummy_articles = []

        for i in range(count):
            dummy_articles.append({
                "source": "modelpress",
                "source_detail": "モデルプレス",
                "title": f"諸橋沙夏、最新グラビア公開 - ダミー記事 {i+1}",
                "content": f"人気アイドル諸橋沙夏さんの最新グラビアが公開された。ダミー記事 {i+1}。",
                "url": f"https://mdpr.jp/news/dummy{2000 + i}",
                "published_at": now.isoformat(),
                "metrics": {
                    "thumbnail_url": f"https://mdpr.jp/images/dummy{i+1}.jpg"
                },
                "author": None,
                "author_account": None
            })

        return dummy_articles
