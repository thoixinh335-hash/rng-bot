import aiosqlite
from database.database import DatabaseManager

class LeaderboardService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def get_top_rarity(self, limit: int = 10) -> list[dict]:
        async with await self.db.connect() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT user_id, username, highest_role_name, highest_rank 
                FROM players ORDER BY highest_rank DESC, total_rolls ASC LIMIT ?
            """, (limit,)) as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def get_top_collection(self, limit: int = 10) -> list[dict]:
        async with await self.db.connect() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT p.user_id, p.username, COUNT(c.role_id) as collection_count 
                FROM players p
                LEFT JOIN collections c ON p.user_id = c.user_id
                GROUP BY p.user_id
                ORDER BY collection_count DESC, p.total_rolls ASC LIMIT ?
            """, (limit,)) as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def get_top_lucky(self, limit: int = 10) -> list[dict]:
        async with await self.db.connect() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT user_id, username, lucky FROM players ORDER BY lucky DESC LIMIT ?
            """, (limit,)) as cursor:
                return [dict(r) for r in await cursor.fetchall()]

    async def get_top_rolls(self, limit: int = 10) -> list[dict]:
        async with await self.db.connect() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT user_id, username, total_rolls FROM players ORDER BY total_rolls DESC LIMIT ?
            """, (limit,)) as cursor:
                return [dict(r) for r in await cursor.fetchall()]