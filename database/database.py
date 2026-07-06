import os
import aiosqlite

class _ConnectionContext:
    """Lớp bọc ngữ cảnh để quản lý kết nối an toàn, tránh kích hoạt trùng lặp luồng thread"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = None

    async def __aenter__(self):
        # Chỉ kích hoạt luồng tại đây khi bắt đầu vào block 'async with'
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("PRAGMA foreign_keys = ON;")
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            await self.db.close()

class DatabaseManager:
    def __init__(self, db_path: str = "database/rng.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            
            # Bảng Người chơi (Players)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    current_role_id INTEGER NOT NULL,
                    current_role_name TEXT NOT NULL,
                    highest_role_id INTEGER NOT NULL,
                    highest_role_name TEXT NOT NULL,
                    highest_rank INTEGER NOT NULL,
                    lucky INTEGER DEFAULT 0,
                    total_rolls INTEGER DEFAULT 0,
                    last_roll TEXT,
                    rolls_used INTEGER DEFAULT 0,
                    rolls_window_start TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Migration: thêm cột nếu bảng players đã tồn tại
            try:
                await db.execute("ALTER TABLE players ADD COLUMN rolls_used INTEGER DEFAULT 0;")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE players ADD COLUMN rolls_window_start TEXT;")
            except Exception:
                pass

            # Bảng Bộ sưu tập (Collections)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, role_id),
                    FOREIGN KEY(user_id) REFERENCES players(user_id) ON DELETE CASCADE
                );
            """)

            # Bảng Lịch sử quay (History)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    rolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES players(user_id) ON DELETE CASCADE
                );
            """)

            # Bảng Quản lý Mùa giải (Seasons)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS seasons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season_number INTEGER NOT NULL UNIQUE,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE'
                );
            """)

            # Bảng Kho đồ tạm thời sau khi Roll (Roll Inventory)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS roll_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    slot INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES players(user_id) ON DELETE CASCADE
                );
            """)

            # Bảng Nhiệm vụ hàng ngày (Daily Missions) - không FK
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_missions (
                    user_id INTEGER PRIMARY KEY,
                    chat_count INTEGER DEFAULT 0,
                    roll_count INTEGER DEFAULT 0,
                    voice_seconds INTEGER DEFAULT 0,
                    date TEXT NOT NULL,
                    free_rolls INTEGER DEFAULT 0
                );
            """)
            # Xóa FK cũ nếu có (cho upgrade từ version trước)
            await db.execute("PRAGMA foreign_keys = OFF;")
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_missions_old'"
            )
            exists = await cursor.fetchone()
            if not exists:
                # Lần đầu chạy bản này: rename + recreate không FK
                await db.execute("ALTER TABLE daily_missions RENAME TO daily_missions_old;")
                await db.execute("""
                    CREATE TABLE daily_missions (
                        user_id INTEGER PRIMARY KEY,
                        chat_count INTEGER DEFAULT 0,
                        roll_count INTEGER DEFAULT 0,
                        voice_seconds INTEGER DEFAULT 0,
                        date TEXT NOT NULL,
                        free_rolls INTEGER DEFAULT 0
                    );
                """)
                await db.execute(
                    "INSERT INTO daily_missions (user_id, chat_count, roll_count, voice_seconds, date, free_rolls) "
                    "SELECT user_id, chat_count, roll_count, voice_seconds, date, free_rolls FROM daily_missions_old;"
                )
                await db.execute("DROP TABLE daily_missions_old;")
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.commit()

    async def connect(self) -> _ConnectionContext:
        # Trả về đối tượng context chưa kích hoạt luồng để tương thích với cấu trúc 'async with await'
        return _ConnectionContext(self.db_path)