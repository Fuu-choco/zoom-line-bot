import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GoogleCalendarAPI:
    """Google Calendar API クライアント"""
    
    def __init__(self):
        self.credentials_json = Config.GOOGLE_CREDENTIALS_JSON
        self.service = None
        self.calendar_id = 'primary'  # デフォルトはプライマリカレンダー
    
    def get_service(self):
        """Google Calendar サービス取得"""
        try:
            if self.service is None:
                credentials_info = json.loads(self.credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                self.service = build('calendar', 'v3', credentials=credentials)
            
            return self.service
        except Exception as e:
            logger.error(f"Google Calendar サービス取得エラー: {str(e)}")
            raise
    
    def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """カレンダーイベント作成"""
        try:
            service = self.get_service()
            
            # イベントデータ構築
            event = {
                'summary': event_data['meeting_name'],
                'description': self._build_event_description(event_data),
                'start': {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'end': {
                    'dateTime': (event_data['start_time'] + timedelta(minutes=event_data['duration'])).isoformat(),
                    'timeZone': 'Asia/Tokyo',
                },
                'location': event_data.get('meeting_url', ''),
                'attendees': event_data.get('attendees', []),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1日前
                        {'method': 'popup', 'minutes': 10},       # 10分前
                    ],
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"zoom-{event_data.get('meeting_id', '')}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
            }
            
            logger.info(f"Google Calendar イベント作成開始: {event_data['meeting_name']}")
            
            # イベント作成
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                conferenceDataVersion=1,
                sendUpdates='none'  # 参加者に通知しない
            ).execute()
            
            logger.info(f"Google Calendar イベント作成成功: {created_event.get('id')}")
            
            return {
                'event_id': created_event.get('id'),
                'event_url': created_event.get('htmlLink'),
                'meeting_url': created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', ''),
                'summary': created_event.get('summary'),
                'start_time': created_event.get('start', {}).get('dateTime'),
                'end_time': created_event.get('end', {}).get('dateTime')
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API エラー: {str(e)}")
            raise Exception(f"Google Calendar API エラー: {str(e)}")
        except Exception as e:
            logger.error(f"Google Calendar イベント作成エラー: {str(e)}")
            raise
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """イベント取得"""
        try:
            service = self.get_service()
            
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return event
            
        except HttpError as e:
            logger.error(f"Google Calendar イベント取得エラー: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Google Calendar イベント取得エラー: {str(e)}")
            return None
    
    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """イベント更新"""
        try:
            service = self.get_service()
            
            # 既存のイベントを取得
            existing_event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # 更新データをマージ
            existing_event['summary'] = event_data['meeting_name']
            existing_event['description'] = self._build_event_description(event_data)
            existing_event['start']['dateTime'] = event_data['start_time'].isoformat()
            existing_event['end']['dateTime'] = (event_data['start_time'] + timedelta(minutes=event_data['duration'])).isoformat()
            existing_event['location'] = event_data.get('meeting_url', '')
            
            # イベント更新
            service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=existing_event
            ).execute()
            
            logger.info(f"Google Calendar イベント更新成功: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Calendar イベント更新エラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Google Calendar イベント更新エラー: {str(e)}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """イベント削除"""
        try:
            service = self.get_service()
            
            service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Google Calendar イベント削除成功: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Calendar イベント削除エラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Google Calendar イベント削除エラー: {str(e)}")
            return False
    
    def _build_event_description(self, event_data: Dict[str, Any]) -> str:
        """イベント説明文構築"""
        try:
            description = f"""
Zoom会議

会議URL: {event_data.get('meeting_url', '')}
会議ID: {event_data.get('meeting_id', '')}
パスワード: {event_data.get('meeting_password', '')}

この会議はLINE Bot経由で作成されました。
            """.strip()
            
            return description
        except Exception as e:
            logger.error(f"イベント説明文構築エラー: {str(e)}")
            return "Zoom会議"
    
    def test_connection(self) -> bool:
        """接続テスト"""
        try:
            service = self.get_service()
            
            # カレンダー一覧取得でテスト
            calendar_list = service.calendarList().list().execute()
            
            logger.info("Google Calendar API 接続テスト成功")
            return True
            
        except Exception as e:
            logger.error(f"Google Calendar API 接続テストエラー: {str(e)}")
            return False
    
    def get_calendar_list(self) -> list:
        """カレンダー一覧取得"""
        try:
            service = self.get_service()
            
            calendar_list = service.calendarList().list().execute()
            
            calendars = []
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar.get('id'),
                    'summary': calendar.get('summary'),
                    'description': calendar.get('description'),
                    'primary': calendar.get('primary', False)
                })
            
            return calendars
            
        except Exception as e:
            logger.error(f"カレンダー一覧取得エラー: {str(e)}")
            return []

# グローバルインスタンス
google_calendar_api = GoogleCalendarAPI()

def create_calendar_event(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """カレンダーイベント作成（外部呼び出し用）"""
    try:
        return google_calendar_api.create_event(event_data)
    except Exception as e:
        logger.error(f"Google Calendar イベント作成エラー: {str(e)}")
        return None

def get_calendar_event(event_id: str) -> Optional[Dict[str, Any]]:
    """カレンダーイベント取得（外部呼び出し用）"""
    try:
        return google_calendar_api.get_event(event_id)
    except Exception as e:
        logger.error(f"Google Calendar イベント取得エラー: {str(e)}")
        return None

def update_calendar_event(event_id: str, event_data: Dict[str, Any]) -> bool:
    """カレンダーイベント更新（外部呼び出し用）"""
    try:
        return google_calendar_api.update_event(event_id, event_data)
    except Exception as e:
        logger.error(f"Google Calendar イベント更新エラー: {str(e)}")
        return False

def delete_calendar_event(event_id: str) -> bool:
    """カレンダーイベント削除（外部呼び出し用）"""
    try:
        return google_calendar_api.delete_event(event_id)
    except Exception as e:
        logger.error(f"Google Calendar イベント削除エラー: {str(e)}")
        return False

def test_google_calendar_connection() -> bool:
    """Google Calendar接続テスト（外部呼び出し用）"""
    try:
        return google_calendar_api.test_connection()
    except Exception as e:
        logger.error(f"Google Calendar接続テストエラー: {str(e)}")
        return False

