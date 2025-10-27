from flask import request, jsonify
import requests
import hmac
import hashlib
import json
from config import Config
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

# LINE Bot API 設定
LINE_API_URL = 'https://api.line.me/v2/bot/message/reply'
LINE_PUSH_API_URL = 'https://api.line.me/v2/bot/message/push'

# ユーザーの会話状態を管理
user_states = {}

class ConversationState:
    """会話状態の定義"""
    WAITING_FOR_MEETING_NAME = "waiting_for_meeting_name"
    WAITING_FOR_DATE = "waiting_for_date"
    WAITING_FOR_TIME = "waiting_for_time"
    WAITING_FOR_DURATION = "waiting_for_duration"
    CONFIRMING = "confirming"

def verify_signature(body: str, signature: str) -> bool:
    """LINE Bot 署名検証"""
    try:
        # LINE Botの署名はBase64エンコードされている
        # HMAC-SHA256で署名を生成
        hash_value = hmac.new(
            Config.LINE_CHANNEL_SECRET.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Base64エンコード
        import base64
        expected_signature = base64.b64encode(hash_value).decode('utf-8')
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"署名検証エラー: {str(e)}")
        return False

def handle_webhook(request):
    """LINE Bot Webhook処理"""
    try:
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        
        logger.info(f"Webhook受信: {body}")
        
        # 署名検証
        if not verify_signature(body, signature):
            logger.error("Invalid signature")
            return jsonify({"error": "Invalid signature"}), 400
        
        # イベント処理
        events = json.loads(body).get('events', [])
        for event in events:
            if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                handle_message_event(event)
        
        return jsonify({"status": "OK"})
        
    except Exception as e:
        logger.error(f"Webhook処理エラー: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

def handle_message_event(event):
    """メッセージイベント処理"""
    import time
    start_time = time.time()
    
    try:
        user_id = event.get('source', {}).get('userId', '')
        message_text = event.get('message', {}).get('text', '')
        reply_token = event.get('replyToken', '')
        
        logger.info(f"メッセージ受信: {message_text} from {user_id}")
        
        # ユーザー状態を取得
        user_state = user_states.get(user_id, {})
        current_state = user_state.get('state', '')
        
        if message_text == "会議作成":
            # 会議作成開始
            start_meeting_creation(user_id, reply_token)
        elif current_state == ConversationState.WAITING_FOR_MEETING_NAME:
            # 会議名入力
            handle_meeting_name(user_id, message_text, reply_token)
        elif current_state == ConversationState.WAITING_FOR_DATE:
            # 日付入力
            handle_date_input(user_id, message_text, reply_token)
        elif current_state == ConversationState.WAITING_FOR_TIME:
            # 時間入力
            handle_time_input(user_id, message_text, reply_token)
        elif current_state == ConversationState.WAITING_FOR_DURATION:
            # 会議時間入力
            handle_duration_input(user_id, message_text, reply_token)
        elif current_state == ConversationState.CONFIRMING:
            # 確認処理
            handle_confirmation(user_id, message_text, reply_token)
        else:
            # 不明なメッセージ
            send_message(reply_token, "「会議作成」と入力してください")
        
        # 処理時間をログ出力
        processing_time = time.time() - start_time
        logger.info(f"メッセージ処理時間: {processing_time:.2f}秒")
            
    except Exception as e:
        logger.error(f"メッセージ処理エラー: {str(e)}")
        send_message(event.get('replyToken', ''), "エラーが発生しました。もう一度お試しください。")

def start_meeting_creation(user_id: str, reply_token: str):
    """会議作成開始"""
    try:
        # ユーザー状態をリセット
        user_states[user_id] = {
            'state': ConversationState.WAITING_FOR_MEETING_NAME,
            'meeting_data': {}
        }
        
        send_message(reply_token, "会議名を教えてください")
        
    except Exception as e:
        logger.error(f"会議作成開始エラー: {str(e)}")
        send_message(reply_token, "エラーが発生しました。もう一度お試しください。")

def handle_meeting_name(user_id: str, meeting_name: str, reply_token: str):
    """会議名処理"""
    try:
        if not meeting_name.strip():
            send_message(reply_token, "会議名を入力してください")
            return
        
        # ユーザー状態を更新
        user_states[user_id]['meeting_data']['meeting_name'] = meeting_name.strip()
        user_states[user_id]['state'] = ConversationState.WAITING_FOR_DATE
        
        send_message(reply_token, "日付を教えてください（例：2024/01/15）")
        
    except Exception as e:
        logger.error(f"会議名処理エラー: {str(e)}")
        send_message(reply_token, "エラーが発生しました。もう一度お試しください。")

def handle_date_input(user_id: str, date_str: str, reply_token: str):
    """日付入力処理"""
    try:
        from utils.helpers import validate_date
        
        date_obj = validate_date(date_str)
        if not date_obj:
            send_message(reply_token, "正しい日付を入力してください（例：2024/01/15）")
            return
        
        # ユーザー状態を更新
        user_states[user_id]['meeting_data']['date'] = date_obj
        user_states[user_id]['state'] = ConversationState.WAITING_FOR_TIME
        
        send_message(reply_token, "開始時間を教えてください（例：14:00）")
        
    except Exception as e:
        logger.error(f"日付入力処理エラー: {str(e)}")
        send_message(reply_token, "エラーが発生しました。もう一度お試しください。")

def handle_time_input(user_id: str, time_str: str, reply_token: str):
    """時間入力処理"""
    try:
        from utils.helpers import validate_time
        
        time_obj = validate_time(time_str)
        if not time_obj:
            send_message(reply_token, "正しい時間を入力してください（例：14:00）")
            return
        
        # ユーザー状態を更新
        user_states[user_id]['meeting_data']['time'] = time_obj
        user_states[user_id]['state'] = ConversationState.WAITING_FOR_DURATION
        
        send_message(reply_token, "会議時間を教えてください（例：60分）")
        
    except Exception as e:
        logger.error(f"時間入力処理エラー: {str(e)}")
        send_message(reply_token, "エラーが発生しました。もう一度お試しください。")

def handle_duration_input(user_id: str, duration_str: str, reply_token: str):
    """会議時間入力処理"""
    try:
        from utils.helpers import validate_duration
        
        duration = validate_duration(duration_str)
        if not duration:
            send_message(reply_token, "正しい時間を入力してください（例：60分）")
            return
        
        # ユーザー状態を更新
        user_states[user_id]['meeting_data']['duration'] = duration
        user_states[user_id]['state'] = ConversationState.CONFIRMING
        
        # 確認メッセージ送信
        send_confirmation_message(user_id, reply_token)
        
    except Exception as e:
        logger.error(f"会議時間入力処理エラー: {str(e)}")
        send_message(reply_token, "エラーが発生しました。もう一度お試しください。")

def send_confirmation_message(user_id: str, reply_token: str):
    """確認メッセージ送信"""
    try:
        meeting_data = user_states[user_id]['meeting_data']
        
        from utils.helpers import combine_datetime, format_datetime, format_duration
        
        # 日時を結合
        start_datetime = combine_datetime(meeting_data['date'], meeting_data['time'])
        
        message = f"""
以下の内容で会議を作成しますか？

📅 会議名: {meeting_data['meeting_name']}
🕐 日時: {format_datetime(start_datetime)}
⏱️ 時間: {format_duration(meeting_data['duration'])}

「はい」または「いいえ」でお答えください。
        """.strip()
        
        send_message(reply_token, message)
        
    except Exception as e:
        logger.error(f"確認メッセージ送信エラー: {str(e)}")
        send_message(reply_token, "エラーが発生しました。もう一度お試しください。")

def handle_confirmation(user_id: str, response: str, reply_token: str):
    """確認処理"""
    try:
        if response == "はい":
            # 会議作成処理
            create_meeting(user_id, reply_token)
        elif response == "いいえ":
            # 会議作成キャンセル
            user_states[user_id] = {}
            send_message(reply_token, "会議作成をキャンセルしました。")
        else:
            send_message(reply_token, "「はい」または「いいえ」でお答えください。")
            
    except Exception as e:
        logger.error(f"確認処理エラー: {str(e)}")
        send_message(reply_token, "エラーが発生しました。もう一度お試しください。")

def create_meeting(user_id: str, reply_token: str):
    """会議作成処理（非同期）"""
    try:
        # 即座に処理中メッセージを送信
        send_message(reply_token, "会議を作成中です... しばらくお待ちください。")
        
        # ユーザー状態を一時保存
        meeting_data = user_states[user_id]['meeting_data'].copy()
        
        # 非同期で会議作成を実行
        import threading
        thread = threading.Thread(target=_create_meeting_async, args=(user_id, meeting_data))
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        logger.error(f"会議作成開始エラー: {str(e)}")
        send_message(reply_token, "会議作成中にエラーが発生しました。もう一度お試しください。")

def _create_meeting_async(user_id: str, meeting_data: dict):
    """非同期会議作成処理"""
    try:
        
        # 日時を結合
        from utils.helpers import combine_datetime
        start_datetime = combine_datetime(meeting_data['date'], meeting_data['time'])
        
        # Zoom API で会議作成
        from services.zoom_api import create_zoom_meeting
        
        zoom_meeting_data = {
            'meeting_name': meeting_data['meeting_name'],
            'start_time': start_datetime,
            'duration': meeting_data['duration']
        }
        
        zoom_result = create_zoom_meeting(zoom_meeting_data)
        
        # Google Calendar にイベント作成
        from services.google_calendar import create_calendar_event
        
        calendar_event_data = {
            'meeting_name': meeting_data['meeting_name'],
            'start_time': start_datetime,
            'duration': meeting_data['duration'],
            'meeting_url': zoom_result['meeting_url'],
            'meeting_id': zoom_result['meeting_id'],
            'meeting_password': zoom_result['meeting_password']
        }
        
        calendar_result = create_calendar_event(calendar_event_data)
        
        # データベースに保存
        from database.models import Meeting
        meeting = Meeting(
            line_user_id=user_id,
            meeting_name=meeting_data['meeting_name'],
            start_time=start_datetime,
            duration=meeting_data['duration']
        )
        meeting.meeting_id = zoom_result['meeting_id']
        meeting.meeting_password = zoom_result['meeting_password']
        meeting.meeting_url = zoom_result['meeting_url']
        meeting.google_event_id = calendar_result['event_id'] if calendar_result else None
        meeting.save()
        
        # 成功メッセージ送信（プッシュメッセージ）
        from utils.helpers import format_meeting_info
        meeting_info = {
            'meeting_name': meeting_data['meeting_name'],
            'start_time': start_datetime,
            'duration': meeting_data['duration'],
            'meeting_id': zoom_result['meeting_id'],
            'meeting_password': zoom_result['meeting_password'],
            'meeting_url': zoom_result['meeting_url']
        }
        
        success_message = f"✅ 会議を作成しました！\n\n{format_meeting_info(meeting_info)}"
        send_push_message(user_id, success_message)
        
        # ユーザー状態をリセット
        user_states[user_id] = {}
        
    except Exception as e:
        logger.error(f"非同期会議作成エラー: {str(e)}")
        send_push_message(user_id, "会議作成中にエラーが発生しました。もう一度お試しください。")

def send_message(reply_token: str, message: str):
    """メッセージ送信"""
    import time
    start_time = time.time()
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Config.LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        data = {
            'replyToken': reply_token,
            'messages': [{
                'type': 'text',
                'text': message
            }]
        }
        
        response = requests.post(LINE_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        send_time = time.time() - start_time
        logger.info(f"メッセージ送信成功: {message} (送信時間: {send_time:.2f}秒)")
        
    except Exception as e:
        logger.error(f"メッセージ送信エラー: {str(e)}")

def send_push_message(user_id: str, message: str):
    """プッシュメッセージ送信"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Config.LINE_CHANNEL_ACCESS_TOKEN}'
        }
        
        data = {
            'to': user_id,
            'messages': [{
                'type': 'text',
                'text': message
            }]
        }
        
        response = requests.post(LINE_PUSH_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        logger.info(f"プッシュメッセージ送信成功: {message}")
        
    except Exception as e:
        logger.error(f"プッシュメッセージ送信エラー: {str(e)}")