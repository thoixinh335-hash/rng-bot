from datetime import datetime
import aiosqlite
from database.database import DatabaseManager

class PlayerService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def get_player(self, user_id: int) -> dict | None:
        async with await self.db.connect() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT * FROM players WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def create_player(self, user_id: int, username: str, default_role: dict) -> dict:
        async with await self.db.connect() as conn:
            now = datetime.utcnow().isoformat()
            await conn.execute("""
                INSERT INTO players (user_id, username, current_role_id, current_role_name, 
                                    highest_role_id, highest_role_name, highest_rank, lucky, total_rolls, last_roll, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, NULL, ?, ?)
            """, (user_id, username, default_role["role_id"], default_role["name"], 
                  default_role["role_id"], default_role["name"], default_role["rank"], now, now))
            await conn.commit()
        return await self.get_player(user_id)

    async def process_roll_transaction(self, user_id: int, username: str, rolled_role: dict, is_highest: bool, next_lucky: int) -> None:
        async with await self.db.connect() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("BEGIN TRANSACTION;")
                try:
                    now = datetime.utcnow().isoformat()
                    if is_highest:
                        await cursor.execute("""
                            UPDATE players SET 
                                username = ?, current_role_id = ?, current_role_name = ?,
                                highest_role_id = ?, highest_role_name = ?, highest_rank = ?,
                                lucky = ?, total_rolls = total_rolls + 1, last_roll = ?, updated_at = ?
                            WHERE user_id = ?
                        """, (username, rolled_role["role_id"], rolled_role["name"],
                              rolled_role["role_id"], rolled_role["name"], rolled_role["rank"],
                              next_lucky, now, now, user_id))
                    else:
                        await cursor.execute("""
                            UPDATE players SET 
                                username = ?, current_role_id = ?, current_role_name = ?,
                                lucky = ?, total_rolls = total_rolls + 1, last_roll = ?, updated_at = ?
                            WHERE user_id = ?
                        """, (username, rolled_role["role_id"], rolled_role["name"],
                              next_lucky, now, now, user_id))

                    # Thêm vào bộ sưu tập (Bỏ qua nếu đã tồn tại nhờ cấu trúc UNIQUE)
                    await cursor.execute("""
                        INSERT OR IGNORE INTO collections (user_id, role_id, obtained_at)
                        VALUES (?, ?, ?)
                    """, (user_id, rolled_role["role_id"], now))

                    # Lưu vào lịch sử hệ thống
                    await cursor.execute("""
                        INSERT INTO history (user_id, role_id, rolled_at)
                        VALUES (?, ?, ?)
                    """, (user_id, rolled_role["role_id"], now))

                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    raise e