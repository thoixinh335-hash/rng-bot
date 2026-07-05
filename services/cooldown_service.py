from datetime import datetime, timedelta
from services.config_service import ConfigService

class CooldownService:
    def __init__(self):
        self.config_service = ConfigService()

    def check_cooldown(self, last_roll_str: str | None) -> tuple[bool, float]:
        if not last_roll_str:
            return True, 0.0
        
        last_roll = datetime.fromisoformat(last_roll_str)
        # Đọc cấu hình giờ hồi chiêu từ file JSON (mặc định là 12h)
        cooldown_hours = self.config_service.get("cooldown_hours", 12)
        available_at = last_roll + timedelta(hours=cooldown_hours)
        now = datetime.utcnow()
        
        if now >= available_at:
            return True, 0.0
        else:
            remaining_seconds = (available_at - now).total_seconds()
            return False, remaining_seconds