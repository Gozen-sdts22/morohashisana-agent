"""
Yahoo!ニュース情報収集Agent
BeautifulSoupを使用してYahoo!ニュースから記事を収集する
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime, timezone
import pytz
from urllib.parse import urljoin, quote

from .base_agent import BaseAgent


class YahooAgent(BaseAgent):
    """
    Yahoo!ニュースから諸橋沙夏さんに関する記事を収集するAgent
    """

    def __init__(self, prompt_manager, config: Dict[str, Any]):
        """
        初期化

        Args:
            prompt_manager: プロンプトマネージャー
            config: 設定辞書（config/sources.jsonのyahoo_news部分）
        """
        super().__init__('yahoo', prompt_manager)
        self.config = config
        self.search_keyword = config.get('search_keyword', '諸橋沙夏')
        self.base_url = config.get('base_url', 'https://news.yahoo.co.jp/search')

        # User-Agent設定
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def collect(self) -> List[Dict[str, Any]]:
        """
        Yahoo!ニュースから記事を収集

        Returns:
            収集した記事のリスト
        """
        try:
            articles = self._search_news()
            return articles
        except Exception as e:
            print(f"[YahooAgent] 記事収集でエラー: {e}")
            # エラー時はダミーデータを返す
            print(f"[YahooAgent] ダミーデータを返します")
            return self._get_dummy_articles()

    def _search_news(self) -> List[Dict[str, Any]]:
        """
        Yahoo!ニュースで検索

        Returns:
            記事のリスト
        """
        # 検索URLを構築
        search_url = f"{self.base_url}?p={quote(self.search_keyword)}"

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
            raise Exception(f"Yahoo!ニュースへのリクエストに失敗しました: {e}")

    def _parse_articles(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        HTMLから記事情報を抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            記事のリスト

        Note:
            Yahoo!ニュースのHTML構造は変更される可能性があるため、
            実際の構造に合わせて調整が必要です。
            ここではダミーデータを返す実装としています。
        """
        # 注: Yahoo!ニュースのHTML構造は頻繁に変更されるため、
        # 実際の運用では定期的なメンテナンスが必要です。
        # この実装ではダミーデータを返します。

        print("[YahooAgent] HTML解析（実装未完了のためダミーデータ使用）")
        return self._get_dummy_articles()

    def _format_article(
        self,
        title: str,
        summary: str,
        url: str,
        source: str,
        published_at: str
    ) -> Dict[str, Any]:
        """
        記事データを統一フォーマットに変換

        Args:
            title: 記事タイトル
            summary: 記事要約
            url: 記事URL
            source: 配信元メディア
            published_at: 公開日時

        Returns:
            フォーマット済み記事データ
        """
        return {
            "source": "yahoo_news",
            "source_detail": source,
            "title": title,
            "content": summary,
            "url": url,
            "published_at": published_at,
            "metrics": None,
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
        sources = ["スポーツ報知", "デイリースポーツ", "モデルプレス"]

        for i in range(count):
            dummy_articles.append({
                "source": "yahoo_news",
                "source_detail": sources[i % len(sources)],
                "title": f"諸橋沙夏、新ドラマ出演決定 - ダミー記事 {i+1}",
                "content": f"人気アイドル諸橋沙夏さんが春ドラマに出演することが決定した。ダミー記事 {i+1}。",
                "url": f"https://news.yahoo.co.jp/articles/dummy{1000 + i}",
                "published_at": now.isoformat(),
                "metrics": None,
                "author": None,
                "author_account": None
            })

        return dummy_articles
