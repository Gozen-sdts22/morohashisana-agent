"""
X (旧Twitter) 情報収集Agent
snscrapeを使用してツイートを収集する
"""
import json
import subprocess
from typing import List, Dict, Any
from datetime import datetime, timezone
import pytz

from .base_agent import BaseAgent


class TwitterAgent(BaseAgent):
    """
    X（旧Twitter）から諸橋沙夏さんに関する情報を収集するAgent
    """

    def __init__(self, prompt_manager, config: Dict[str, Any]):
        """
        初期化

        Args:
            prompt_manager: プロンプトマネージャー
            config: 設定辞書（config/sources.jsonのtwitter部分）
        """
        super().__init__('twitter', prompt_manager)
        self.config = config
        self.hashtags = config.get('hashtags', [])
        self.engagement_threshold = config.get('engagement_threshold', {})

    def collect(self) -> List[Dict[str, Any]]:
        """
        Xからツイートを収集

        Returns:
            収集したツイートのリスト
        """
        all_tweets = []

        # 各ハッシュタグで検索
        for hashtag in self.hashtags:
            try:
                tweets = self._search_by_hashtag(hashtag)
                all_tweets.extend(tweets)
            except Exception as e:
                print(f"[TwitterAgent] ハッシュタグ '{hashtag}' の検索でエラー: {e}")
                # 1つのハッシュタグで失敗しても続行

        # 重複を除去（URL単位）
        unique_tweets = self._remove_duplicates(all_tweets)

        return unique_tweets

    def _search_by_hashtag(self, hashtag: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        ハッシュタグでツイートを検索

        Args:
            hashtag: 検索するハッシュタグ
            max_results: 最大取得件数

        Returns:
            ツイートのリスト
        """
        # snscrapeコマンドを構築
        # 注: snscrapeは非公式ツールのため、動作しない可能性があります
        # その場合はダミーデータを返す設定も可能

        # ハッシュタグから#を除去
        search_query = hashtag.replace('#', '')

        try:
            # snscrapeを使用してツイート検索
            # --jsonl: JSON Lines形式で出力
            # --max-results: 最大取得件数
            cmd = [
                'snscrape',
                '--jsonl',
                '--max-results', str(max_results),
                'twitter-search', search_query
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            # JSON Lines形式をパース
            tweets = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    tweet_data = json.loads(line)
                    # フォーマット変換
                    formatted = self._format_tweet(tweet_data, hashtag)

                    # エンゲージメント条件でフィルタ
                    if self._meets_engagement_threshold(formatted):
                        tweets.append(formatted)
                except json.JSONDecodeError:
                    continue

            return tweets

        except subprocess.TimeoutExpired:
            raise Exception(f"ハッシュタグ '{hashtag}' の検索がタイムアウトしました")
        except subprocess.CalledProcessError as e:
            # snscrapeが利用できない場合はダミーデータを返す（開発用）
            print(f"[TwitterAgent] snscrape実行エラー: {e}")
            print(f"[TwitterAgent] ダミーデータを返します")
            return self._get_dummy_tweets(hashtag)
        except FileNotFoundError:
            # snscrapeがインストールされていない場合
            print(f"[TwitterAgent] snscrapeがインストールされていません")
            print(f"[TwitterAgent] ダミーデータを返します")
            return self._get_dummy_tweets(hashtag)

    def _format_tweet(self, tweet_data: Dict[str, Any], hashtag: str) -> Dict[str, Any]:
        """
        ツイートデータを統一フォーマットに変換

        Args:
            tweet_data: snscrapeから取得したツイートデータ
            hashtag: 検索に使用したハッシュタグ

        Returns:
            フォーマット済みツイートデータ
        """
        # 日時をISO 8601形式に変換
        published_at = tweet_data.get('date', datetime.now(timezone.utc).isoformat())
        if isinstance(published_at, str):
            # すでに文字列の場合はそのまま使用
            pass
        else:
            # datetimeオブジェクトの場合はISO形式に変換
            published_at = published_at.isoformat()

        return {
            "source": "twitter",
            "source_detail": f"hashtag:{hashtag}",
            "title": None,
            "content": tweet_data.get('content', ''),
            "url": tweet_data.get('url', ''),
            "published_at": published_at,
            "metrics": {
                "likes": tweet_data.get('likeCount', 0),
                "retweets": tweet_data.get('retweetCount', 0),
                "views": tweet_data.get('viewCount', 0)
            },
            "author": tweet_data.get('user', {}).get('displayname', ''),
            "author_account": tweet_data.get('user', {}).get('username', '')
        }

    def _meets_engagement_threshold(self, tweet: Dict[str, Any]) -> bool:
        """
        エンゲージメント条件を満たすかチェック

        Args:
            tweet: ツイートデータ

        Returns:
            条件を満たす場合True
        """
        metrics = tweet.get('metrics', {})
        likes = metrics.get('likes', 0)
        views = metrics.get('views', 0)

        min_likes = self.engagement_threshold.get('likes', 10000)
        min_views = self.engagement_threshold.get('views', 100000)

        # いいね1万以上 OR 表示数10万以上
        return likes >= min_likes or views >= min_views

    def _remove_duplicates(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        URL単位で重複を除去

        Args:
            tweets: ツイートのリスト

        Returns:
            重複除去後のツイートリスト
        """
        seen_urls = set()
        unique_tweets = []

        for tweet in tweets:
            url = tweet.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_tweets.append(tweet)

        return unique_tweets

    def _get_dummy_tweets(self, hashtag: str, count: int = 3) -> List[Dict[str, Any]]:
        """
        ダミーツイートデータを生成（開発・テスト用）

        Args:
            hashtag: ハッシュタグ
            count: 生成するダミーデータの件数

        Returns:
            ダミーツイートのリスト
        """
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst)

        dummy_tweets = []
        for i in range(count):
            dummy_tweets.append({
                "source": "twitter",
                "source_detail": f"hashtag:{hashtag}",
                "title": None,
                "content": f"諸橋沙夏さんに関するダミーツイート {i+1} {hashtag}",
                "url": f"https://twitter.com/dummy/status/{1000000 + i}",
                "published_at": now.isoformat(),
                "metrics": {
                    "likes": 15000 + i * 1000,
                    "retweets": 500 + i * 50,
                    "views": 150000 + i * 10000
                },
                "author": f"ダミーユーザー{i+1}",
                "author_account": f"dummy_user_{i+1}"
            })

        return dummy_tweets
