"""
データベース接続テストスクリプト
データベースへの接続を確認する
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.db_manager import get_db_manager
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


def main():
    """
    データベース接続をテスト
    """
    print("=" * 60)
    print("諸橋沙夏情報収集Agent - データベース接続テスト")
    print("=" * 60)

    try:
        # データベースマネージャーを取得
        db_manager = get_db_manager()

        # 環境情報を表示
        db_type = os.getenv('DB_TYPE', 'sqlite')
        print(f"\nデータベースタイプ: {db_type}")

        if db_type == 'sqlite':
            db_path = os.getenv('DB_PATH', 'data/natsu_dev.db')
            print(f"データベースパス: {db_path}")
        else:
            db_host = os.getenv('DB_HOST', 'N/A')
            db_name = os.getenv('DB_NAME', 'N/A')
            print(f"データベースホスト: {db_host}")
            print(f"データベース名: {db_name}")

        # 接続テスト
        print("\n接続テスト中...")
        if db_manager.test_connection():
            print("\n" + "=" * 60)
            print("✓ 接続テスト成功")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("✗ 接続テスト失敗")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
