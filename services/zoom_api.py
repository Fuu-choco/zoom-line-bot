import requests
import time
from datetime import datetime
from config import Config
import logging
from typing import Dict, Any, Optional
import base64

logger = logging.getLogger(__name__)

class ZoomAPI:
    """Zoom API クライアント (Server to Server OAuth)"""
    
    def __init__(self):
        self.client_id = Config.ZOOM_API_KEY  # Client ID
        self.client_secret = Config.ZOOM_API_SECRET  # Client Secret
        self.account_id = Config.ZOOM_ACCOUNT_ID  # Account ID
        self.base_url = "https://api.zoom.us/v2"
        self.access_token = None
        self.token_expires_at = 0
    
    def get_access_token(self) -> str:
        """OAuth アクセストークン取得"""
        try:
            # トークンが有効な場合は再利用
            if self.access_token and time.time() < self.token_expires_at:
                return self.access_token
            
            # 新しいトークンを取得
            url = "https://zoom.us/oauth/token"
            
            # Basic認証用のヘッダー
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "account_credentials",
                "account_id": self.account_id
            }
            
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expires_at = time.time() + token_data["expires_in"] - 60  # 1分前に更新
            
            return self.access_token
            
        except Exception as e:
            logger.error(f"OAuth トークン取得エラー: {str(e)}")
            raise
    
    def get_headers(self) -> Dict[str, str]:
        """API リクエストヘッダー取得"""
        try:
            token = self.get_access_token()
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        except Exception as e:
            logger.error(f"ヘッダー取得エラー: {str(e)}")
            raise
    
    def create_meeting(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """会議作成"""
        try:
            headers = self.get_headers()
            url = f"{self.base_url}/users/me/meetings"
            
            # 会議設定
            meeting_settings = {
                "topic": meeting_data['meeting_name'],
                "type": 2,  # スケジュールされた会議
                "start_time": meeting_data['start_time'].strftime('%Y-%m-%dT%H:%M:%S'),
                "duration": meeting_data['duration'],
                "timezone": "Asia/Tokyo",
                "password": meeting_data.get('password', self.generate_password()),
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "join_before_host": False,
                    "mute_upon_entry": True,
                    "waiting_room": True,
                    "approval_type": 0,  # 自動承認
                    "audio": "both",
                    "auto_recording": "none"
                }
            }
            
            logger.info(f"Zoom会議作成開始: {meeting_data['meeting_name']}")
            
            response = requests.post(url, headers=headers, json=meeting_settings)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Zoom会議作成成功: {result.get('id')}")
            
            return {
                'meeting_id': result.get('id'),
                'meeting_password': result.get('password'),
                'meeting_url': result.get('join_url'),
                'start_url': result.get('start_url'),
                'topic': result.get('topic'),
                'start_time': result.get('start_time'),
                'duration': result.get('duration')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom API リクエストエラー: {str(e)}")
            raise Exception(f"Zoom API エラー: {str(e)}")
        except Exception as e:
            logger.error(f"Zoom会議作成エラー: {str(e)}")
            raise
    
    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """会議情報取得"""
        try:
            headers = self.get_headers()
            url = f"{self.base_url}/meetings/{meeting_id}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom会議取得エラー: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Zoom会議取得エラー: {str(e)}")
            return None
    
    def update_meeting(self, meeting_id: str, meeting_data: Dict[str, Any]) -> bool:
        """会議情報更新"""
        try:
            headers = self.get_headers()
            url = f"{self.base_url}/meetings/{meeting_id}"
            
            update_data = {
                "topic": meeting_data.get('meeting_name'),
                "start_time": meeting_data['start_time'].strftime('%Y-%m-%dT%H:%M:%S'),
                "duration": meeting_data['duration']
            }
            
            response = requests.patch(url, headers=headers, json=update_data)
            response.raise_for_status()
            
            logger.info(f"Zoom会議更新成功: {meeting_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom会議更新エラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Zoom会議更新エラー: {str(e)}")
            return False
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """会議削除"""
        try:
            headers = self.get_headers()
            url = f"{self.base_url}/meetings/{meeting_id}"
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Zoom会議削除成功: {meeting_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoom会議削除エラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Zoom会議削除エラー: {str(e)}")
            return False
    
    def generate_password(self) -> str:
        """会議パスワード生成"""
        import random
        import string
        
        try:
            # 6桁の数字パスワード
            return ''.join(random.choices(string.digits, k=6))
        except Exception as e:
            logger.error(f"パスワード生成エラー: {str(e)}")
            return "123456"
    
    def test_connection(self) -> bool:
        """接続テスト"""
        try:
            headers = self.get_headers()
            url = f"{self.base_url}/users/me"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            logger.info("Zoom API 接続テスト成功")
            return True
            
        except Exception as e:
            logger.error(f"Zoom API 接続テストエラー: {str(e)}")
            return False

# グローバルインスタンス
zoom_api = ZoomAPI()

def create_zoom_meeting(meeting_data: Dict[str, Any]) -> Dict[str, Any]:
    """Zoom会議作成（外部呼び出し用）"""
    try:
        return zoom_api.create_meeting(meeting_data)
    except Exception as e:
        logger.error(f"Zoom会議作成エラー: {str(e)}")
        raise

def get_zoom_meeting(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Zoom会議取得（外部呼び出し用）"""
    try:
        return zoom_api.get_meeting(meeting_id)
    except Exception as e:
        logger.error(f"Zoom会議取得エラー: {str(e)}")
        return None

def update_zoom_meeting(meeting_id: str, meeting_data: Dict[str, Any]) -> bool:
    """Zoom会議更新（外部呼び出し用）"""
    try:
        return zoom_api.update_meeting(meeting_id, meeting_data)
    except Exception as e:
        logger.error(f"Zoom会議更新エラー: {str(e)}")
        return False

def delete_zoom_meeting(meeting_id: str) -> bool:
    """Zoom会議削除（外部呼び出し用）"""
    try:
        return zoom_api.delete_meeting(meeting_id)
    except Exception as e:
        logger.error(f"Zoom会議削除エラー: {str(e)}")
        return False

def test_zoom_connection() -> bool:
    """Zoom接続テスト（外部呼び出し用）"""
    try:
        return zoom_api.test_connection()
    except Exception as e:
        logger.error(f"Zoom接続テストエラー: {str(e)}")
        return False

