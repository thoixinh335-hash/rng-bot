import json
import logging
import os

logger = logging.getLogger("rng_bot")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
            config_path = os.path.join(BASE_DIR, "config", "config.json")
            roles_path = os.path.join(BASE_DIR, "data", "roles.json")
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            with open(roles_path, "r", encoding="utf-8") as f:
                self.roles = json.load(f)
                self.roles.sort(key=lambda x: x["rank"])
                self.roles_dict = {r["role_id"]: r for r in self.roles}
            logger.info("Đã tải thành công tệp cấu hình và danh sách Roles vào bộ nhớ Cache.")
        except Exception as e:
            logger.critical(f"Lỗi nghiêm trọng khi tải tệp cấu hình cấu trúc JSON: {e}")
            raise e

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        self.config[key] = value

    def save(self):
        try:
            config_path = os.path.join(BASE_DIR, "config", "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("Đã lưu cấu hình vào config.json")
        except Exception as e:
            logger.error(f"Lỗi lưu cấu hình: {e}")

    def get_role_by_id(self, role_id: int) -> dict | None:
        return self.roles_dict.get(role_id)

    def get_roles_list(self) -> list:
        return self.roles