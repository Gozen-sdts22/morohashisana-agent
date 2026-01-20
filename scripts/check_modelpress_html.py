"""
モデルプレスのHTML構造を確認するスクリプト
実際の検索結果ページと記事ページのHTML構造を確認して、実装に必要な情報を抽出する
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import sys
import io

# Windowsのコンソールエンコーディング問題を回避
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_search_page():
    """検索結果ページのHTML構造を確認"""
    output_lines = []
    
    def log(msg):
        print(msg)
        output_lines.append(msg)
    
    log("=" * 60)
    log("モデルプレス - 検索結果ページのHTML構造確認")
    log("=" * 60)
    
    search_keyword = "諸橋沙夏"
    search_url = f"https://mdpr.jp/search?q={quote(search_keyword)}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"\n検索URL: {search_url}")
        print("リクエスト送信中...")
        
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"ステータスコード: {response.status_code}")
        print(f"HTMLサイズ: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 記事リンクを探す（一般的なパターンを試す）
        print("\n" + "-" * 60)
        print("記事リンクの候補を探しています...")
        print("-" * 60)
        
        # パターン1: <a>タグでhrefに/news/を含むもの
        article_links = soup.find_all('a', href=lambda x: x and '/news/' in x)
        print(f"\n[パターン1] hrefに'/news/'を含む<a>タグ: {len(article_links)}件")
        if article_links:
            print("最初の3件:")
            for i, link in enumerate(article_links[:3], 1):
                href = link.get('href', '')
                text = link.get_text(strip=True)[:50]
                print(f"  {i}. href: {href}")
                print(f"     テキスト: {text}")
        
        # パターン2: 記事タイトルっぽい要素を探す
        print("\n[パターン2] 記事タイトルっぽい要素を探す...")
        # h2, h3, h4タグで記事タイトルっぽいもの
        headings = soup.find_all(['h2', 'h3', 'h4'])
        print(f"見出しタグ(h2/h3/h4): {len(headings)}件")
        if headings:
            print("最初の5件:")
            for i, h in enumerate(headings[:5], 1):
                text = h.get_text(strip=True)[:50]
                print(f"  {i}. {h.name}: {text}")
        
        # パターン3: 記事リストっぽいコンテナを探す
        print("\n[パターン3] 記事リストのコンテナを探す...")
        # class名にarticle, news, item, listなどが含まれる要素
        containers = soup.find_all(['div', 'ul', 'section'], 
                                  class_=lambda x: x and any(
                                      keyword in str(x).lower() 
                                      for keyword in ['article', 'news', 'item', 'list', 'search']
                                  ))
        print(f"記事コンテナ候補: {len(containers)}件")
        if containers:
            print("最初の3件のclass名:")
            for i, container in enumerate(containers[:3], 1):
                classes = container.get('class', [])
                print(f"  {i}. {container.name} class: {classes}")
        
        # HTMLの一部を保存（デバッグ用）
        print("\n" + "-" * 60)
        print("HTMLの一部を保存します（デバッグ用）...")
        print("-" * 60)
        
        # 最初の記事リンクが見つかった場合、その周辺のHTMLを保存
        if article_links:
            first_link = article_links[0]
            parent = first_link.parent
            if parent:
                html_snippet = str(parent)[:2000]  # 最初の2000文字
                with open('modelpress_search_snippet.html', 'w', encoding='utf-8') as f:
                    f.write(html_snippet)
                print("保存しました: modelpress_search_snippet.html")
        
        # 実際の記事URLを取得（最初の1件）
        if article_links:
            first_article_url = article_links[0].get('href', '')
            if first_article_url:
                if not first_article_url.startswith('http'):
                    first_article_url = f"https://mdpr.jp{first_article_url}"
                print(f"\n最初の記事URL: {first_article_url}")
                return first_article_url
        
        return None
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_article_page(article_url):
    """記事ページのHTML構造を確認"""
    if not article_url:
        print("\n記事URLが取得できませんでした。スキップします。")
        return
    
    print("\n" + "=" * 60)
    print("モデルプレス - 記事ページのHTML構造確認")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"\n記事URL: {article_url}")
        print("リクエスト送信中...")
        
        response = requests.get(article_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"ステータスコード: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # タイトルを探す
        print("\n" + "-" * 60)
        print("記事タイトルを探しています...")
        print("-" * 60)
        
        title = None
        # パターン1: <h1>タグ
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
            print(f"[パターン1] <h1>タグ: {title[:100]}")
        
        # パターン2: <title>タグ
        title_tag = soup.find('title')
        if title_tag:
            print(f"[パターン2] <title>タグ: {title_tag.get_text(strip=True)[:100]}")
        
        # 本文を探す
        print("\n" + "-" * 60)
        print("記事本文を探しています...")
        print("-" * 60)
        
        # パターン1: class名にarticle, body, contentなどが含まれる要素
        body_candidates = soup.find_all(['div', 'article', 'section'],
                                       class_=lambda x: x and any(
                                           keyword in str(x).lower()
                                           for keyword in ['article', 'body', 'content', 'text', 'main']
                                       ))
        print(f"本文候補: {len(body_candidates)}件")
        if body_candidates:
            print("最初の3件のclass名とテキストの一部:")
            for i, body in enumerate(body_candidates[:3], 1):
                classes = body.get('class', [])
                text_preview = body.get_text(strip=True)[:100]
                print(f"  {i}. {body.name} class: {classes}")
                print(f"     テキスト: {text_preview}")
        
        # 公開日時を探す
        print("\n" + "-" * 60)
        print("公開日時を探しています...")
        print("-" * 60)
        
        # パターン1: <time>タグ
        time_tags = soup.find_all('time')
        if time_tags:
            print(f"<time>タグ: {len(time_tags)}件")
            for i, time_tag in enumerate(time_tags[:3], 1):
                datetime_attr = time_tag.get('datetime', '')
                text = time_tag.get_text(strip=True)
                print(f"  {i}. datetime属性: {datetime_attr}")
                print(f"     テキスト: {text}")
        
        # パターン2: 日付っぽいテキストを含む要素
        date_keywords = ['年', '月', '日', '2026', '2025', '2024']
        date_elements = soup.find_all(string=lambda x: x and any(kw in x for kw in date_keywords))
        if date_elements:
            print(f"\n日付っぽいテキストを含む要素: {len(date_elements)}件")
            print("最初の5件:")
            for i, elem in enumerate(date_elements[:5], 1):
                text = str(elem).strip()[:50]
                parent = elem.parent if hasattr(elem, 'parent') else None
                parent_tag = parent.name if parent else 'N/A'
                print(f"  {i}. {parent_tag}: {text}")
        
        # HTMLの一部を保存
        print("\n" + "-" * 60)
        print("記事ページのHTMLの一部を保存します...")
        print("-" * 60)
        
        # タイトルと本文の周辺HTMLを保存
        html_parts = []
        if h1:
            html_parts.append(f"<h1>周辺:\n{str(h1.parent)[:1000]}\n")
        if body_candidates:
            html_parts.append(f"<本文候補>:\n{str(body_candidates[0])[:1000]}\n")
        
        if html_parts:
            with open('modelpress_article_snippet.html', 'w', encoding='utf-8') as f:
                f.write('\n'.join(html_parts))
            print("保存しました: modelpress_article_snippet.html")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


def main():
    """メイン関数"""
    # 出力をファイルにも保存
    output_file = 'modelpress_html_check_result.txt'
    
    class TeeOutput:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = TeeOutput(sys.stdout, f)
        
        try:
            print("\nモデルプレスのHTML構造確認を開始します...\n")
            
            # 検索結果ページを確認
            article_url = check_search_page()
            
            # 記事ページを確認
            if article_url:
                check_article_page(article_url)
            
            print("\n" + "=" * 60)
            print("確認完了！")
            print("=" * 60)
            print(f"\n結果は {output_file} にも保存されました")
            print("\n次のステップ:")
            print("1. 上記の出力を確認して、HTML構造を理解してください")
            print("2. 保存されたHTMLファイル（modelpress_*.html）も確認してください")
            print("3. 確認した内容を元に、実装を進めます")
        finally:
            sys.stdout = original_stdout


if __name__ == '__main__':
    main()
