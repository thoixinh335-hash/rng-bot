import random
from services.config_service import ConfigService

class RNGEngine:
    def __init__(self):
        self.config_service = ConfigService()

    def roll(self, lucky_multiplier: int) -> dict:
        roles = self.config_service.get_roles_list()
        # Duyệt từ danh hiệu hiếm nhất (Rank 30) về thấp nhất (Rank 1)
        for role in reversed(roles):
            base_chance = role["chance"]
            # Áp dụng công thức tính Luck: giảm bớt mẫu số cơ hội thực tế
            effective_chance = max(2, base_chance // (1 + lucky_multiplier))
            if random.randint(1, effective_chance) == 1:
                return role
        return roles[0] # Fallback an toàn về Common

    def roll_multi(self, lucky_multiplier: int, count: int = 3) -> list[dict]:
        """Quay nhiều lần, mỗi lần trả về 1 role. Có thể trùng nhau."""
        results = []
        for _ in range(count):
            results.append(self.roll(lucky_multiplier))
        return results