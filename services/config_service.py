import json
import logging

logger = logging.getLogger("rng_bot")

class ConfigService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigService, cls).__new__(cls, *args, **kwargs)
            cls._instance.config = {}
            cls._instance.roles = []
            cls._instance.roles_dict = {}
        return cls._instance

    def load_all(self):
        try:
            with open("config/config.json", "r", encoding="utf-8") as f:
                self.config = json.load(f)
            with open("data/roles.json", "r", encoding="utf-8") as f:
                self.roles = json.load(f)
                self.roles.sort(key=lambda x: x["rank"])
                self.roles_dict = {r["role_id"]: r for r in self.roles}
            logger.info("Đã tải thành công tệp cấu hình và danh sách Roles vào bộ nhớ Cache.")
        except Exception as e:
            logger.critical(f"Lỗi nghiêm trọng khi tải tệp cấu hình cấu trúc JSON: {e}")
            raise e

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def get_role_by_id(self, role_id: int) -> dict | None:
        return self.roles_dict.get(role_id)

    def get_roles_list(self) -> list:
        return self.roles