"""
Flask Webアプリケーション
諸橋沙夏情報収集AgentのWebインターフェース
"""
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask, render_template
from flask_cors import CORS
from src.utils.logger import get_logger

# ロガーを取得
logger = get_logger()


def create_app():
    """
    Flaskアプリケーションを作成

    Returns:
        Flaskアプリケーション
    """
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False  # 日本語のJSONレスポンス対応

    # CORSを有効化
    CORS(app)

    # APIルートを登録
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # メインページ
    @app.route('/')
    def index():
        """メインページを表示"""
        return render_template('index.html')

    # エラーハンドラー
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not Found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal Server Error: {error}")
        return {'error': 'Internal Server Error'}, 500

    logger.info("Flaskアプリケーションを初期化しました")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
