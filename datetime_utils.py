#!/usr/bin/env python3
"""
🎯 SNIPER DATETIME UTILITIES - Timezone Management
Utility functions untuk menangani timezone UTC+7 (WIB)
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz
from config import Config

class DateTimeUtils:
    """
    🎯 Utility class untuk menangani timezone dan datetime operations
    Menggunakan timezone UTC+7 (Asia/Jakarta) sesuai dengan lokasi user
    """
    
    # Setup timezone UTC+7
    UTC_PLUS_7 = timezone(timedelta(hours=7))
    JAKARTA_TZ = pytz.timezone('Asia/Jakarta')
    
    @classmethod
    def now_utc7(cls) -> datetime:
        """
        Mendapatkan datetime saat ini dalam timezone UTC+7
        
        Returns:
            datetime: Current datetime in UTC+7 timezone
        """
        return datetime.now(cls.UTC_PLUS_7)
    
    @classmethod
    def now_jakarta(cls) -> datetime:
        """
        Mendapatkan datetime saat ini dalam timezone Jakarta (WIB)
        
        Returns:
            datetime: Current datetime in Jakarta timezone
        """
        return datetime.now(cls.JAKARTA_TZ)
    
    @classmethod
    def utc_to_utc7(cls, utc_datetime: datetime) -> datetime:
        """
        Konversi datetime dari UTC ke UTC+7
        
        Args:
            utc_datetime: Datetime object in UTC
            
        Returns:
            datetime: Converted datetime in UTC+7
        """
        if utc_datetime.tzinfo is None:
            # Assume UTC if no timezone info
            utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
        
        return utc_datetime.astimezone(cls.UTC_PLUS_7)
    
    @classmethod
    def timestamp_to_utc7(cls, timestamp: float) -> datetime:
        """
        Konversi Unix timestamp ke datetime UTC+7
        
        Args:
            timestamp: Unix timestamp (seconds since epoch)
            
        Returns:
            datetime: Datetime object in UTC+7
        """
        utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return cls.utc_to_utc7(utc_dt)
    
    @classmethod
    def format_utc7(cls, dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S WIB") -> str:
        """
        Format datetime dalam timezone UTC+7 dengan format yang readable
        
        Args:
            dt: Datetime object (default: current time)
            format_str: Format string (default: YYYY-MM-DD HH:MM:SS WIB)
            
        Returns:
            str: Formatted datetime string
        """
        if dt is None:
            dt = cls.now_utc7()
        elif dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=timezone.utc).astimezone(cls.UTC_PLUS_7)
        elif dt.tzinfo != cls.UTC_PLUS_7:
            # Convert to UTC+7 if different timezone
            dt = dt.astimezone(cls.UTC_PLUS_7)
        
        return dt.strftime(format_str)
    
    @classmethod
    def get_trading_session_info(cls) -> dict:
        """
        Mendapatkan informasi sesi trading berdasarkan waktu UTC+7
        
        Returns:
            dict: Trading session information
        """
        now = cls.now_utc7()
        hour = now.hour
        
        # Define trading sessions (WIB time)
        sessions = {
            'asian': (7, 16),      # 07:00 - 16:00 WIB
            'european': (14, 23),   # 14:00 - 23:00 WIB  
            'american': (21, 6)     # 21:00 - 06:00 WIB (next day)
        }
        
        active_sessions = []
        
        for session, (start, end) in sessions.items():
            if session == 'american':
                # Handle overnight session
                if hour >= start or hour < end:
                    active_sessions.append(session)
            else:
                if start <= hour < end:
                    active_sessions.append(session)
        
        return {
            'current_time': cls.format_utc7(now),
            'hour': hour,
            'active_sessions': active_sessions,
            'is_market_hours': len(active_sessions) > 0
        }
    
    @classmethod
    def log_timestamp(cls) -> str:
        """
        Generate timestamp untuk logging dalam format yang konsisten
        
        Returns:
            str: Formatted timestamp untuk logging
        """
        return cls.format_utc7(format_str="%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def iso_timestamp_utc7(cls) -> str:
        """
        Generate ISO format timestamp dalam UTC+7
        
        Returns:
            str: ISO formatted timestamp
        """
        return cls.now_utc7().isoformat()

# Convenience functions untuk backward compatibility
def now_utc7() -> datetime:
    """Shortcut untuk mendapatkan current time UTC+7"""
    return DateTimeUtils.now_utc7()

def format_utc7(dt: Optional[datetime] = None) -> str:
    """Shortcut untuk format datetime UTC+7"""
    return DateTimeUtils.format_utc7(dt)

def log_timestamp() -> str:
    """Shortcut untuk logging timestamp"""
    return DateTimeUtils.log_timestamp()