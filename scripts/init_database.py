"""
データベース初期化スクリプト
テーブルの作成とインデックスの設定を行う
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.db_manager import get_db_manager


def main():
    """
    データベースを初期化
    """
    print("=" * 60)
    print("諸橋沙夏情報収集Agent - データベース初期化")
    print("=" * 60)

    try:
        # データベースマネージャーを取得
        db_manager = get_db_manager()

        # 接続テスト
        print("\n[1/2] データベース接続テスト中...")
        if not db_manager.test_connection():
            print("\n✗ データベース接続に失敗しました")
            print("環境変数(.env)の設定を確認してください")
            return 1

        # テーブル作成
        print("\n[2/2] テーブル作成中...")
        db_manager.create_tables()

        print("\n" + "=" * 60)
        print("✓ データベース初期化が完了しました")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
