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
import time

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
            # 本番ではダミーデータは返さず、空リストで上位に任せる
            return []

    def _search_news(self) -> List[Dict[str, Any]]:
        """
        Yahoo!ニュースで検索

        Returns:
            記事のリスト
        """
        # 検索URLを構築（キーワード検索）
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

            # 検索結果ページから記事候補を抽出
            candidates = self._parse_articles(soup)
            if not candidates:
                return []

            # 各記事ページから詳細を取得して整形
            articles: List[Dict[str, Any]] = []
            for cand in candidates:
                url = cand.get("url")
                if not url:
                    continue

                # アクセスし過ぎ防止（サイト負荷軽減）
                time.sleep(1)

                try:
                    detail = self._fetch_article_detail(url)
                except Exception as e:
                    print(f"[YahooAgent] 記事詳細取得エラー: {url} ({e})")
                    continue

                title = (detail.get("title") or cand.get("title") or "").strip()
                published_at = detail.get("published_at") or cand.get("published_at")
                content = detail.get("content") or cand.get("summary") or ""
                source = cand.get("source") or detail.get("source") or ""

                articles.append(
                    self._format_article(
                        title=title or None,
                        summary=content,
                        url=url,
                        source=source or None,
                        published_at=published_at,
                    )
                )

            return articles

        except requests.RequestException as e:
            raise Exception(f"Yahoo!ニュースへのリクエストに失敗しました: {e}")

    def _parse_articles(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        検索結果HTMLから記事情報を抽出

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            記事候補のリスト（詳細は記事ページで取得）

        Note:
            Yahoo!ニュースのHTML構造は変更される可能性があります。
        """
        candidates: List[Dict[str, Any]] = []

        # 代表的な構造: li.newsFeed_item の中に記事情報が入っているケース
        items = soup.select("li.newsFeed_item")
        for li in items[:10]:  # 上位10件に限定
            # URL
            link = li.select_one("a.newsFeed_item_link") or li.find(
                "a", href=lambda x: x and ("/articles/" in x or "/pickup/" in x)
            )
            if not link or not link.get("href"):
                continue
            href = link.get("href")
            url = href if href.startswith("http") else urljoin(self.base_url, href)

            # タイトル
            title_el = li.select_one(".newsFeed_item_title") or li.select_one(".newsFeed_title")
            title = (title_el.get_text(strip=True) if title_el else "").strip()

            # 概要
            summary_el = li.select_one(".newsFeed_item_text") or li.select_one(".newsFeed_text")
            summary = (summary_el.get_text(strip=True) if summary_el else "").strip()

            # 配信元
            source_el = li.select_one(".newsFeed_item_source") or li.select_one(".newsFeed_source")
            source = (source_el.get_text(strip=True) if source_el else "").strip()

            # 公開日時（一覧にはある場合もあるが、確実なのは記事ページなのでここではNoneのままでもOK）
            published_at = None

            candidates.append(
                {
                    "url": url,
                    "title": title,
                    "summary": summary,
                    "source": source,
                    "published_at": published_at,
                }
            )

        return candidates

    def _fetch_article_detail(self, url: str) -> Dict[str, Any]:
        """
        記事ページからタイトル/公開日時/本文を取得する

        Args:
            url: 記事URL

        Returns:
            dict: {\"title\", \"published_at\", \"content\", \"source\"}
        """
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # タイトル
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else None

        # 公開日時
        published_at_iso = None
        # 第一候補: <time datetime=\"...\">
        time_el = soup.find("time", attrs={"datetime": True})
        if time_el and time_el.get("datetime"):
            published_at_iso = self._parse_yahoo_datetime(time_el.get("datetime").strip())
        else:
            # 第二候補: datePublished などのメタ情報
            meta = soup.find(attrs={"itemprop": "datePublished"})
            if meta and meta.get("content"):
                published_at_iso = self._parse_yahoo_datetime(meta.get("content").strip())

        # 本文
        content = None
        # よくあるクラス名に articleBody / article_body などが含まれる
        body = soup.find(
            ["div", "article"],
            class_=lambda c: c
            and any(k in str(c).lower() for k in ["articlebody", "article_body", "article-body"]),
        )
        if body:
            paragraphs = [p.get_text(strip=True) for p in body.find_all("p")]
            text = " ".join(p for p in paragraphs if p)
            content = text or body.get_text(" ", strip=True)

        # 配信元（記事ページ上のメディア名があれば）
        source = None
        source_el = soup.find(attrs={"class": lambda c: c and "media" in str(c).lower()})
        if source_el:
            source = source_el.get_text(strip=True)

        return {
            "title": title,
            "published_at": published_at_iso,
            "content": content,
            "source": source,
        }

    def _parse_yahoo_datetime(self, raw: str) -> str:
        """
        Yahoo!ニュースの日時表記をISO 8601（JST）文字列に変換

        対応例:
        - \"2026-01-19T12:34:56+09:00\"
        - \"2026-01-19T12:34:56\"
        - \"2026/01/19 12:34\" など
        """
        jst = pytz.timezone("Asia/Tokyo")
        raw = (raw or "").strip()

        # すでにISO形式（timezone付き）の場合はそのまま返す
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = jst.localize(dt)
            return dt.isoformat()
        except ValueError:
            pass

        # よくあるフォーマットを試す
        for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(raw, fmt)
                dt = jst.localize(dt)
                return dt.isoformat()
            except ValueError:
                continue

        # 最後の手段: 現在時刻
        return datetime.now(jst).isoformat()

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
