from flask import Flask, request, jsonify
from config import Config
import logging
from database.init_db import init_database
from services.line_bot import handle_webhook
from services.zoom_api import test_zoom_connection
from services.google_calendar import test_google_calendar_connection
import os

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Flask アプリケーション初期化
app = Flask(__name__)
app.config.from_object(Config)

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    try:
        # データベース接続確認
        from database.init_db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "database": "connected",
            "services": {
                "zoom_api": "configured",
                "google_calendar": "configured",
                "line_bot": "configured"
            }
        }
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "error": str(e)
        }, 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """LINE Bot Webhook"""
    try:
        return handle_webhook(request)
    except Exception as e:
        logger.error(f"Webhook処理エラー: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/test/zoom')
def test_zoom():
    """Zoom API テスト"""
    try:
        if test_zoom_connection():
            return jsonify({"status": "success", "message": "Zoom API接続成功"})
        else:
            return jsonify({"status": "error", "message": "Zoom API接続失敗"}), 500
    except Exception as e:
        logger.error(f"Zoom API テストエラー: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test/google-calendar')
def test_google_calendar():
    """Google Calendar API テスト"""
    try:
        if test_google_calendar_connection():
            return jsonify({"status": "success", "message": "Google Calendar API接続成功"})
        else:
            return jsonify({"status": "error", "message": "Google Calendar API接続失敗"}), 500
    except Exception as e:
        logger.error(f"Google Calendar API テストエラー: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test/all')
def test_all():
    """全API接続テスト"""
    try:
        results = {
            "zoom_api": test_zoom_connection(),
            "google_calendar": test_google_calendar_connection(),
            "database": True
        }
        
        # データベーステスト
        try:
            from database.init_db import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
        except Exception as e:
            results["database"] = False
            logger.error(f"データベーステストエラー: {str(e)}")
        
        all_success = all(results.values())
        
        return jsonify({
            "status": "success" if all_success else "partial",
            "results": results,
            "message": "全API接続テスト完了" if all_success else "一部API接続に問題があります"
        })
        
    except Exception as e:
        logger.error(f"全API接続テストエラー: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/meetings/<user_id>')
def get_user_meetings(user_id):
    """ユーザーの会議一覧取得"""
    try:
        from database.models import Meeting
        
        meetings = Meeting.get_by_user_id(user_id)
        
        return jsonify({
            "status": "success",
            "meetings": meetings
        })
        
    except Exception as e:
        logger.error(f"会議一覧取得エラー: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """404エラーハンドリング"""
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドリング"""
    return jsonify({"error": "Internal Server Error"}), 500

def main():
    """メイン関数"""
    try:
        # 設定検証
        Config.validate_config()
        logger.info("設定検証完了")
        
        # データベース初期化
        init_database()
        logger.info("データベース初期化完了")
        
        # アプリケーション起動
        logger.info(f"アプリケーション起動: {Config.HOST}:{Config.PORT}")
        
        # Railway環境での起動
        port = int(os.getenv('PORT', 8000))
        logger.info(f"Railway環境で起動中... ポート: {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"アプリケーション起動エラー: {str(e)}")
        print(f"❌ アプリケーション起動エラー: {str(e)}")
        raise

if __name__ == '__main__':
    main()

