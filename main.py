import os
import sys
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands

from database.database import DatabaseManager
from services.config_service import ConfigService
from services.rng_engine import RNGEngine
from services.player_service import PlayerService
from services.cooldown_service import CooldownService
from services.role_manager import RoleManager
from services.announcement_service import AnnouncementService
from services.leaderboard_service import LeaderboardService
from services.season_service import SeasonService

# Cấu hình logging kép chuyên nghiệp
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("rng_bot")
logger.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')

# Stream Handler xuất màn hình terminal
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# File Handler lưu toàn bộ log chạy trực tiếp
latest_handler = logging.FileHandler("logs/latest.log", encoding="utf-8", mode="w")
latest_handler.setFormatter(formatter)
logger.addHandler(latest_handler)

# File Handler riêng biệt cho các lỗi hệ thống nghiêm trọng
error_handler = logging.FileHandler("logs/errors.log", encoding="utf-8", mode="a")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

# Tải biến môi trường bảo mật .env
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class RNGBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True  # Yêu cầu kích hoạt Privileged Intents tại Discord Developer Portal
        intents.message_content = True
        
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
        # Đọc dữ liệu cài đặt ban đầu vào Cache bộ nhớ
        self.config_service = ConfigService()
        self.config_service.load_all()

        # Khởi tạo mô hình kiến trúc Core Services & Repository
        self.db_manager = DatabaseManager()
        self.rng_engine = RNGEngine()
        self.player_service = PlayerService(self.db_manager)
        self.cooldown_service = CooldownService()
        self.role_manager = RoleManager()
        self.announcement_service = AnnouncementService(self)
        self.leaderboard_service = LeaderboardService(self.db_manager)
        self.season_service = SeasonService(self.db_manager)

    async def setup_hook(self):
        # 1. Khởi tạo schema và các kết nối SQLite an toàn
        await self.db_manager.initialize()
        
        # 2. Kiểm tra tính toàn vẹn và mốc thời gian của Mùa Giải (Season)
        await self.season_service.check_and_update_season()

        # 3. Nạp động tất cả các Cogs giao diện tương tác lệnh
        initial_extensions = [
            "cogs.ping",
            "cogs.roll",
            "cogs.profile",
            "cogs.collection",
            "cogs.history",
            "cogs.leaderboard",
            "cogs.admin",
            "cogs.missions",
            "cogs.boost"
        ]
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Đã kích hoạt phân hệ Cog thành công: {ext}")
            except Exception as e:
                logger.error(f"Thất bại khi nạp phân hệ Cog {ext}: {e}")

    async def on_ready(self):
        logger.info(f"--- ĐÃ ĐĂNG NHẬP THÀNH CÔNG VỚI TÊN: {self.user} ---")
        try:
            # Sync global (có thể mất 1h) + sync instant cho từng guild
            synced = await self.tree.sync()
            logger.info(f"Hệ thống điều hướng Application Tree đã đồng bộ {len(synced)} lệnh Slash thành công.")
            # Sync ngay cho từng guild đang có mặt
            for guild in self.guilds:
                await self.tree.sync(guild=guild)
                logger.info(f"Đã sync instant cho guild: {guild.name}")
        except Exception as e:
            logger.error(f"Lỗi xảy ra trong quá trình đồng bộ các ứng dụng lệnh Slash: {e}")

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        # Hệ thống bọc bắt lỗi tập trung (Global Exception Catching) cho toàn bộ lệnh Slash
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ Lỗi: Bạn không đủ quyền hạn thực thi lệnh này.", ephemeral=True)
        elif isinstance(error, discord.app_commands.errors.CommandInvokeError):
            logger.error(f"Lỗi thực thi nội bộ tại lệnh {interaction.command.name if interaction.command else 'Unknown'}: {error.original}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Hệ thống gặp sự cố trong quá trình truy vấn cơ sở dữ liệu.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Hệ thống gặp sự cố trong quá trình xử lý tác vụ.", ephemeral=True)
        else:
            logger.error(f"Lỗi không xác định: {error}")

bot = RNGBot()

if __name__ == "__main__":
    if not TOKEN:
        logger.critical("Không tìm thấy biến môi trường DISCORD_BOT_TOKEN trong file .env!")
        sys.exit(1)
    bot.run(TOKEN)