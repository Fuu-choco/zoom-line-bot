import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def validate_date(date_str: str) -> Optional[datetime]:
    """日付文字列の検証と変換"""
    try:
        # 複数の日付形式に対応
        date_formats = [
            '%Y/%m/%d',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%Y年%m月%d日'
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                # 過去日チェック（2024年以降は許可）
                if date_obj.year < 2024:
                    return None
                return date_obj
            except ValueError:
                continue
        
        return None
    except Exception as e:
        logger.error(f"日付検証エラー: {str(e)}")
        return None

def validate_time(time_str: str) -> Optional[datetime]:
    """時間文字列の検証と変換"""
    try:
        # 複数の時間形式に対応
        time_formats = [
            '%H:%M',
            '%H時%M分',
            '%I:%M %p',  # 12時間形式
            '%I時%M分 %p'
        ]
        
        for fmt in time_formats:
            try:
                time_obj = datetime.strptime(time_str, fmt)
                return time_obj
            except ValueError:
                continue
        
        return None
    except Exception as e:
        logger.error(f"時間検証エラー: {str(e)}")
        return None

def validate_duration(duration_str: str) -> Optional[int]:
    """会議時間の検証（分単位）"""
    try:
        # 数字のみの場合
        if duration_str.isdigit():
            duration = int(duration_str)
            if 1 <= duration <= 480:  # 1分〜8時間
                return duration
        
        # "分"が含まれる場合
        if '分' in duration_str:
            numbers = re.findall(r'\d+', duration_str)
            if numbers:
                duration = int(numbers[0])
                if 1 <= duration <= 480:
                    return duration
        
        return None
    except Exception as e:
        logger.error(f"時間検証エラー: {str(e)}")
        return None

def combine_datetime(date: datetime, time: datetime) -> datetime:
    """日付と時間を結合"""
    try:
        return datetime.combine(date.date(), time.time())
    except Exception as e:
        logger.error(f"日時結合エラー: {str(e)}")
        raise

def format_datetime(dt: datetime) -> str:
    """日時のフォーマット"""
    try:
        return dt.strftime('%Y年%m月%d日 %H:%M')
    except Exception as e:
        logger.error(f"日時フォーマットエラー: {str(e)}")
        return str(dt)

def format_duration(minutes: int) -> str:
    """時間のフォーマット"""
    try:
        if minutes < 60:
            return f"{minutes}分"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours}時間"
            else:
                return f"{hours}時間{remaining_minutes}分"
    except Exception as e:
        logger.error(f"時間フォーマットエラー: {str(e)}")
        return f"{minutes}分"

def generate_meeting_password() -> str:
    """会議パスワード生成"""
    import random
    import string
    
    try:
        # 6桁の数字パスワード
        return ''.join(random.choices(string.digits, k=6))
    except Exception as e:
        logger.error(f"パスワード生成エラー: {str(e)}")
        return "123456"

def format_meeting_info(meeting_data: dict) -> str:
    """会議情報のフォーマット"""
    try:
        info = f"""
📅 会議名: {meeting_data['meeting_name']}
🕐 日時: {format_datetime(meeting_data['start_time'])}
⏱️ 時間: {format_duration(meeting_data['duration'])}
🔗 会議URL: {meeting_data['meeting_url']}
🔑 パスワード: {meeting_data['meeting_password']}
🆔 会議ID: {meeting_data['meeting_id']}
        """.strip()
        
        return info
    except Exception as e:
        logger.error(f"会議情報フォーマットエラー: {str(e)}")
        return "会議情報の表示にエラーが発生しました"

def is_business_hours(dt: datetime) -> bool:
    """営業時間内かチェック（9:00-18:00）"""
    try:
        hour = dt.hour
        return 9 <= hour < 18
    except Exception as e:
        logger.error(f"営業時間チェックエラー: {str(e)}")
        return True

def get_next_business_day() -> datetime:
    """次の営業日を取得"""
    try:
        now = datetime.now()
        next_day = now + timedelta(days=1)
        
        # 土日を避ける
        while next_day.weekday() >= 5:  # 土曜日=5, 日曜日=6
            next_day += timedelta(days=1)
        
        return next_day
    except Exception as e:
        logger.error(f"次の営業日取得エラー: {str(e)}")
        return datetime.now() + timedelta(days=1)
