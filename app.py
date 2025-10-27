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

@app.route('/')
def index():
    """トップページ"""
    return jsonify({
        "message": "Zoom Meeting Bot API",
        "status": "running",
        "version": "1.0.0",
        "environment": "railway" if Config.IS_RAILWAY else "local",
        "line_secret_configured": bool(Config.LINE_CHANNEL_SECRET),
        "line_token_configured": bool(Config.LINE_CHANNEL_ACCESS_TOKEN)
    })

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    try:
        from datetime import datetime
        
        # データベース接続確認
        from database.init_db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        # サービス設定確認
        zoom_configured = bool(Config.ZOOM_API_KEY and Config.ZOOM_API_SECRET and Config.ZOOM_ACCOUNT_ID)
        google_configured = bool(Config.GOOGLE_CREDENTIALS_JSON)
        line_configured = bool(Config.LINE_CHANNEL_ACCESS_TOKEN and Config.LINE_CHANNEL_SECRET)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "services": {
                "zoom_api": "configured" if zoom_configured else "not_configured",
                "google_calendar": "configured" if google_configured else "not_configured",
                "line_bot": "configured" if line_configured else "not_configured"
            },
            "environment": "railway" if Config.IS_RAILWAY else "local"
        }
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
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

@app.route('/debug/env')
def debug_env():
    """環境変数デバッグ（開発用）"""
    try:
        import os
        from config import Config
        
        # 環境変数の直接確認
        env_vars = {}
        for key in ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET', 'ZOOM_API_KEY', 'ZOOM_API_SECRET', 'ZOOM_ACCOUNT_ID', 'GOOGLE_CREDENTIALS_JSON']:
            value = os.getenv(key)
            if value:
                # 機密情報は一部のみ表示
                if 'SECRET' in key or 'TOKEN' in key or 'KEY' in key:
                    env_vars[key] = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    env_vars[key] = value
            else:
                env_vars[key] = "未設定"
        
        # Configクラスの値確認
        config_vars = {}
        for key in ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET', 'ZOOM_API_KEY', 'ZOOM_API_SECRET', 'ZOOM_ACCOUNT_ID', 'GOOGLE_CREDENTIALS_JSON']:
            value = getattr(Config, key)
            if value:
                if 'SECRET' in key or 'TOKEN' in key or 'KEY' in key:
                    config_vars[key] = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    config_vars[key] = value
            else:
                config_vars[key] = "未設定"
        
        return jsonify({
            "environment": "railway" if Config.IS_RAILWAY else "local",
            "os_environ": env_vars,
            "config_class": config_vars,
            "railway_env": os.getenv('RAILWAY_ENVIRONMENT'),
            "port": os.getenv('PORT'),
            "railway_port": os.getenv('RAILWAY_PORT')
        })
        
    except Exception as e:
        logger.error(f"環境変数デバッグエラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
        logger.info("設定検証開始...")
        logger.info(f"LINE_CHANNEL_ACCESS_TOKEN: {'設定済み' if Config.LINE_CHANNEL_ACCESS_TOKEN else '未設定'}")
        logger.info(f"LINE_CHANNEL_SECRET: {'設定済み' if Config.LINE_CHANNEL_SECRET else '未設定'}")
        logger.info(f"ZOOM_API_KEY: {'設定済み' if Config.ZOOM_API_KEY else '未設定'}")
        logger.info(f"ZOOM_API_SECRET: {'設定済み' if Config.ZOOM_API_SECRET else '未設定'}")
        logger.info(f"ZOOM_ACCOUNT_ID: {'設定済み' if Config.ZOOM_ACCOUNT_ID else '未設定'}")
        Config.validate_config()
        logger.info("設定検証完了")
        
        # データベース初期化
        init_database()
        logger.info("データベース初期化完了")
        
        # アプリケーション起動
        logger.info(f"アプリケーション起動: {Config.HOST}:{Config.PORT}")
        
        # Railway環境での起動
        port = int(os.getenv('PORT', 8000))
        logger.info(f"アプリケーション起動中... ポート: {port}")
        
        # Railway環境の判定を改善
        is_railway = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT')
        logger.info(f"Railway環境判定: {is_railway}")
        logger.info(f"利用可能な環境変数: {list(os.environ.keys())}")
        
        # Railway環境では本番用WSGIサーバーを使用
        if is_railway:
            logger.info("Railway環境で本番用WSGIサーバーを使用")
            try:
                from waitress import serve
                logger.info("waitressのインポート成功")
                serve(app, host='0.0.0.0', port=port)
            except ImportError as e:
                logger.error(f"waitressのインポートエラー: {e}")
                logger.info("Flask開発サーバーにフォールバック")
                app.run(host='0.0.0.0', port=port, debug=False)
        else:
            logger.info("ローカル環境でFlask開発サーバーを使用")
            app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        import traceback
        logger.error(f"アプリケーション起動エラー: {str(e)}")
        logger.error(f"エラー詳細: {traceback.format_exc()}")
        print(f"❌ アプリケーション起動エラー: {str(e)}")
        print(f"エラー詳細: {traceback.format_exc()}")
        raise

if __name__ == '__main__':
    main()

