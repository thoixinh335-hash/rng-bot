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
        """Quay nhiều lần, bỏ qua role trùng. Trả về danh sách unique."""
        results = []
        seen_ids = set()
        max_attempts = count * 10  # Chống loop vô hạn nếu quá xui

        attempts = 0
        while len(results) < count and attempts < max_attempts:
            role = self.roll(lucky_multiplier)
            attempts += 1
            if role["role_id"] not in seen_ids:
                seen_ids.add(role["role_id"])
                results.append(role)

        return results