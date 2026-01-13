"""
API エンドポイント
諸橋沙夏情報収集AgentのREST API
"""
import threading
from datetime import datetime, timedelta
import pytz
from flask import Blueprint, request, jsonify
from sqlalchemy import desc, or_

from src.database.db_manager import get_db_manager
from src.database.models import Item, Execution
from src.utils.logger import get_logger
from main import NatsuAgentExecutor

# Blueprint作成
api_bp = Blueprint('api', __name__)

# ロガー
logger = get_logger()

# 実行状態を管理
execution_state = {
    'is_running': False,
    'current_execution_id': None,
    'started_at': None
}


@api_bp.route('/items', methods=['GET'])
def get_items():
    """
    GET /api/items
    収集した情報の一覧を取得

    Query Parameters:
        period: 期間（24h, 7d, 30d, all）
        importance: 重要度（all, high, medium_up）
        category: カテゴリ（all, またはカテゴリ名）
        keyword: キーワード検索
        page: ページ番号（デフォルト: 1）
        per_page: 1ページあたり件数（デフォルト: 20）

    Returns:
        JSON:
        {
            "items": [...],
            "total": 総件数,
            "page": ページ番号,
            "per_page": 1ページあたり件数,
            "has_next": 次ページがあるか
        }
    """
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()

        # クエリパラメータを取得
        period = request.args.get('period', '7d')
        importance = request.args.get('importance', 'all')
        category = request.args.get('category', 'all')
        keyword = request.args.get('keyword', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # ベースクエリ
        query = session.query(Item)

        # 期間フィルタ
        if period != 'all':
            jst = pytz.timezone('Asia/Tokyo')
            now = datetime.now(jst)

            if period == '24h':
                cutoff = now - timedelta(hours=24)
            elif period == '7d':
                cutoff = now - timedelta(days=7)
            elif period == '30d':
                cutoff = now - timedelta(days=30)
            else:
                cutoff = None

            if cutoff:
                query = query.filter(Item.published_at >= cutoff)

        # 重要度フィルタ
        if importance == 'high':
            query = query.filter(Item.importance_level == 'high')
        elif importance == 'medium_up':
            query = query.filter(Item.importance_level.in_(['high', 'medium']))

        # カテゴリフィルタ
        if category != 'all':
            query = query.filter(Item.category == category)

        # キーワード検索
        if keyword:
            search_pattern = f'%{keyword}%'
            query = query.filter(
                or_(
                    Item.title.like(search_pattern),
                    Item.content.like(search_pattern),
                    Item.summary.like(search_pattern)
                )
            )

        # 総件数を取得
        total = query.count()

        # ソート: 重要度スコア降順 -> 公開日時降順
        query = query.order_by(
            desc(Item.importance_score),
            desc(Item.published_at)
        )

        # ページネーション
        offset = (page - 1) * per_page
        items = query.limit(per_page).offset(offset).all()

        # 次ページがあるかチェック
        has_next = (offset + per_page) < total

        # レスポンスを構築
        response = {
            'items': [item.to_dict() for item in items],
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_next': has_next
        }

        session.close()
        return jsonify(response)

    except Exception as e:
        logger.error(f"GET /api/items エラー: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/execute', methods=['POST'])
def execute_collection():
    """
    POST /api/execute
    情報収集を実行

    Returns:
        JSON:
        {
            "status": "started" or "already_running",
            "execution_id": 実行ID,
            "message": メッセージ
        }
    """
    global execution_state

    try:
        # すでに実行中の場合
        if execution_state['is_running']:
            return jsonify({
                'status': 'already_running',
                'execution_id': execution_state['current_execution_id'],
                'message': 'すでに実行中です'
            }), 409

        # バックグラウンドで実行
        def run_executor():
            global execution_state
            try:
                executor = NatsuAgentExecutor()
                result = executor.execute()
                logger.info(f"バックグラウンド実行完了: {result}")
            except Exception as e:
                logger.error(f"バックグラウンド実行エラー: {e}", exc_info=True)
            finally:
                execution_state['is_running'] = False
                execution_state['current_execution_id'] = None
                execution_state['started_at'] = None

        # 実行状態を更新
        jst = pytz.timezone('Asia/Tokyo')
        execution_id = datetime.now(jst).strftime('exec_%Y%m%d_%H%M%S')
        execution_state['is_running'] = True
        execution_state['current_execution_id'] = execution_id
        execution_state['started_at'] = datetime.now(jst).isoformat()

        # スレッドで実行
        thread = threading.Thread(target=run_executor, daemon=True)
        thread.start()

        return jsonify({
            'status': 'started',
            'execution_id': execution_id,
            'message': '情報収集を開始しました'
        })

    except Exception as e:
        logger.error(f"POST /api/execute エラー: {e}", exc_info=True)
        execution_state['is_running'] = False
        return jsonify({'error': str(e)}), 500


@api_bp.route('/status', methods=['GET'])
def get_status():
    """
    GET /api/status
    現在の実行状態を取得

    Returns:
        JSON:
        {
            "is_running": true/false,
            "execution_id": 実行ID,
            "started_at": 開始日時
        }
    """
    return jsonify(execution_state)


@api_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    GET /api/logs
    過去の実行ログを取得

    Query Parameters:
        limit: 取得件数（デフォルト: 10）

    Returns:
        JSON:
        {
            "logs": [...]
        }
    """
    try:
        limit = int(request.args.get('limit', 10))

        db_manager = get_db_manager()
        session = db_manager.get_session()

        # 最新の実行ログを取得
        executions = session.query(Execution).order_by(
            desc(Execution.started_at)
        ).limit(limit).all()

        response = {
            'logs': [execution.to_dict() for execution in executions]
        }

        session.close()
        return jsonify(response)

    except Exception as e:
        logger.error(f"GET /api/logs エラー: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    GET /api/categories
    利用可能なカテゴリ一覧を取得

    Returns:
        JSON:
        {
            "categories": [...]
        }
    """
    try:
        import json
        with open('config/settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)

        categories = settings.get('judgment_criteria', {}).get('categories', [])

        return jsonify({
            'categories': categories
        })

    except Exception as e:
        logger.error(f"GET /api/categories エラー: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
