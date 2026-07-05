from datetime import datetime, timedelta
import aiosqlite
import logging
from database.database import DatabaseManager
from services.config_service import ConfigService

logger = logging.getLogger("rng_bot")

class SeasonService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.config_service = ConfigService()

    async def check_and_update_season(self) -> None:
        async with await self.db.connect() as conn:
            conn.row_factory = aiosqlite.Row
            now = datetime.utcnow()
            
            async with conn.execute("SELECT * FROM seasons WHERE status = 'ACTIVE' LIMIT 1") as cursor:
                active_season = await cursor.fetchone()

            if not active_season:
                # Tạo mùa giải đầu tiên nếu chưa có
                duration = self.config_service.get("season_days", 90)
                end_date = now + timedelta(days=duration)
                await conn.execute("""
                    INSERT INTO seasons (season_number, start_date, end_date, status)
                    VALUES (1, ?, ?, 'ACTIVE')
                """, (now.isoformat(), end_date.isoformat()))
                await conn.commit()
                logger.info("Đã thiết lập tự động Season 1 mới cho máy chủ.")
                return

            end_date_active = datetime.fromisoformat(active_season["end_date"])
            if now >= end_date_active:
                # Tiến hành reset để sang mùa giải kế tiếp
                current_num = active_season["season_number"]
                logger.info(f"Mùa giải {current_num} đã kết thúc. Đang tự động tiến hành cấu trúc dọn dẹp hệ thống dữ liệu...")
                
                async with conn.cursor() as trans:
                    await trans.execute("BEGIN TRANSACTION;")
                    try:
                        await trans.execute("UPDATE seasons SET status = 'EXPIRED' WHERE id = ?", (active_season["id"],))
                        
                        # Tạo mới bản ghi mùa tiếp theo
                        duration = self.config_service.get("season_days", 90)
                        new_end = now + timedelta(days=duration)
                        await trans.execute("""
                            INSERT INTO seasons (season_number, start_date, end_date, status)
                            VALUES (?, ?, ?, 'ACTIVE')
                        """, (current_num + 1, now.isoformat(), new_end.isoformat()))
                        
                        # Reset thông số người chơi theo yêu cầu
                        await trans.execute("UPDATE players SET lucky = 0;")
                        await trans.execute("DELETE FROM history;")
                        
                        await conn.commit()
                        logger.info(f"Đã hoàn thành chuyển đổi từ Season {current_num} sang Season {current_num + 1}.")
                    except Exception as e:
                        await conn.rollback()
                        logger.error(f"Lỗi trong quá trình chuyển đổi mùa giải: {e}")

    async def get_current_season_number(self) -> int:
        async with await self.db.connect() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT season_number FROM seasons WHERE status = 'ACTIVE' LIMIT 1") as cursor:
                row = await cursor.fetchone()
                return row["season_number"] if row else 1

    async def force_reset_season(self) -> None:
        async with await self.db.connect() as conn:
            async with conn.cursor() as trans:
                await trans.execute("BEGIN TRANSACTION;")
                try:
                    await trans.execute("UPDATE seasons SET status = 'EXPIRED' WHERE status = 'ACTIVE';")
                    now = datetime.utcnow()
                    duration = self.config_service.get("season_days", 90)
                    new_end = now + timedelta(days=duration)
                    
                    await trans.execute("""
                        INSERT INTO seasons (season_number, start_date, end_date, status)
                        VALUES (1, ?, ?, 'ACTIVE')
                    """, (now.isoformat(), new_end.isoformat()))
                    
                    await trans.execute("UPDATE players SET lucky = 0;")
                    await trans.execute("DELETE FROM history;")
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    raise e