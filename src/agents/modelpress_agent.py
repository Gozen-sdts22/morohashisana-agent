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
import time
from urllib.parse import urljoin

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
        # モデルプレスの検索は /search?keyword=... が基本（ページ内スクリプトの遷移先と一致）
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
            # 本番ではダミーデータは返さず、空リストで上位に任せる
            return []

    def _search_news(self) -> List[Dict[str, Any]]:
        """
        モデルプレスで検索

        Returns:
            記事のリスト
        """
        # 検索URLを構築
        # 例: https://mdpr.jp/search?type=article&keyword=諸橋沙夏
        search_url = f"{self.base_url}?type=article&keyword={quote(self.search_keyword)}"

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

            # 検索結果ページから記事の候補を抽出
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
                    print(f"[ModelpressAgent] 記事詳細取得エラー: {url} ({e})")
                    continue

                # 候補情報（検索結果側）と記事詳細をマージ
                title = (detail.get("title") or cand.get("title") or "").strip()
                published_at = detail.get("published_at") or cand.get("published_at")

                # 本文は「本文抽出 > 検索結果の説明文」の優先順位
                content = detail.get("content") or cand.get("content") or ""

                thumbnail_url = cand.get("thumbnail_url") or detail.get("thumbnail_url")

                articles.append(
                    self._format_article(
                        title=title or None,
                        summary=content,
                        url=url,
                        published_at=published_at,
                        thumbnail_url=thumbnail_url,
                    )
                )

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
            モデルプレスのHTML構造は変更される可能性があります。
            取得できない場合は空リストを返します（上位層でダミーにフォールバック可能）。
        """
        candidates: List[Dict[str, Any]] = []

        # 検索結果のメイン枠（確認済みの構造）
        items = soup.select("li.p-topHeadlineList__main")
        if not items:
            # フォールバック: /news/ を含むリンクを拾う
            links = soup.find_all("a", href=lambda x: x and "/news/" in x)
            for a in links[:10]:
                href = a.get("href")
                if not href:
                    continue
                url = href if href.startswith("http") else urljoin("https://mdpr.jp", href)
                text = (a.get_text(strip=True) or "").strip()
                if not text:
                    continue
                candidates.append(
                    {
                        "url": url,
                        "title": text,
                        "content": "",
                        "thumbnail_url": None,
                        "published_at": None,
                    }
                )
            return candidates

        for li in items[:10]:
            # URL
            a = li.find("a", href=True)
            if not a:
                continue
            href = a.get("href")
            if not href:
                continue
            url = href if href.startswith("http") else urljoin("https://mdpr.jp", href)

            # タイトル
            title_el = li.select_one("p.p-topHeadlineList__mainTitle")
            title = (title_el.get_text(strip=True) if title_el else "") or ""

            # 検索結果の説明文（本文が取れない場合の代替として使える）
            desc_el = li.select_one("p.p-topHeadlineList__mainDescription")
            desc = (desc_el.get_text(strip=True) if desc_el else "") or ""

            # サムネ
            img = li.select_one("img.p-topHeadlineList__mainImage")
            thumbnail_url = img.get("src") if img else None

            candidates.append(
                {
                    "url": url,
                    "title": title,
                    "content": desc,
                    "thumbnail_url": thumbnail_url,
                    "published_at": None,
                }
            )

        return candidates

    def _fetch_article_detail(self, url: str) -> Dict[str, Any]:
        """
        記事ページからタイトル/公開日時/本文を取得する

        Args:
            url: 記事URL（絶対URL）

        Returns:
            dict: {"title": str|None, "published_at": str|None, "content": str|None}
        """
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # タイトル（確認済み: h1.p-articleHeader__title）
        title_el = soup.select_one("h1.p-articleHeader__title")
        if title_el:
            title = title_el.get_text(strip=True)
        else:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else None

        # 公開日時（第一候補: time[datetime] 例: 2026-01-19 19:00）
        published_at_iso = None
        time_el = soup.select_one("time[datetime]")
        if time_el and time_el.get("datetime"):
            dt_raw = time_el.get("datetime").strip()
            published_at_iso = self._parse_modelpress_datetime(dt_raw)
        else:
            # 第二候補: span.p-articleHeader__infoPublished 例: 2026.01.19 19:17
            info_el = soup.select_one("span.p-articleHeader__infoPublished")
            if info_el:
                dt_raw = info_el.get_text(strip=True)
                published_at_iso = self._parse_modelpress_datetime(dt_raw)

        # 本文（ユーザー確認: div.pg-articleDetail__body 配下の a.moki-inline-link.moki-text-link）
        content = None
        body = soup.select_one("div.pg-articleDetail__body")
        if body:
            links = body.select("a.moki-inline-link.moki-text-link")
            parts = []
            for a in links:
                t = a.get_text(strip=True)
                if t:
                    parts.append(t)
            content = " ".join(parts).strip() if parts else body.get_text(" ", strip=True)

        return {
            "title": title,
            "published_at": published_at_iso,
            "content": content,
            "thumbnail_url": None,
        }

    def _parse_modelpress_datetime(self, raw: str) -> str:
        """
        モデルプレスの日時表記をISO 8601（JST）に変換する

        対応例:
        - "2026-01-19 19:00"
        - "2026.01.19 19:17"
        - "2026.01.19 19:17"（余計な文字が混ざる場合は前処理で落とす）
        """
        jst = pytz.timezone("Asia/Tokyo")
        raw = (raw or "").strip()

        # よくある形式を順に試す
        for fmt in ("%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S"):
            try:
                dt = datetime.strptime(raw, fmt)
                dt = jst.localize(dt)
                return dt.isoformat()
            except ValueError:
                continue

        # "2026.01.19 19:17" の前後に文字が混ざるケースを想定して正規化
        cleaned = (
            raw.replace("年", ".")
            .replace("月", ".")
            .replace("日", "")
            .replace("/", ".")
        )
        cleaned = " ".join(cleaned.split())
        for fmt in ("%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M"):
            try:
                dt = datetime.strptime(cleaned, fmt)
                dt = jst.localize(dt)
                return dt.isoformat()
            except ValueError:
                continue

        # 最後の手段: 現在時刻（JST）
        return datetime.now(jst).isoformat()

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
