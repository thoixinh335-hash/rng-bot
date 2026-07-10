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

# Base directory = thư mục chứa main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cấu hình logging kép chuyên nghiệp
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
logger = logging.getLogger("rng_bot")
logger.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')

# Stream Handler xuất màn hình terminal
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# File Handler lưu toàn bộ log chạy trực tiếp
latest_handler = logging.FileHandler(os.path.join(BASE_DIR, "logs", "latest.log"), encoding="utf-8", mode="w")
latest_handler.setFormatter(formatter)
logger.addHandler(latest_handler)

# File Handler riêng biệt cho các lỗi hệ thống nghiêm trọng
error_handler = logging.FileHandler(os.path.join(BASE_DIR, "logs", "errors.log"), encoding="utf-8", mode="a")
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
        
        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=intents, help_command=None)
        
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

        # 3. Nạp động tất cả các Cogs (guard chống load trùng)
        initial_extensions = [
            "cogs.ping",
            "cogs.roll",
            "cogs.profile",
            "cogs.collection",
            "cogs.history",
            "cogs.leaderboard",
            "cogs.admin",
            "cogs.missions",
            "cogs.boost",
            "cogs.avatar",
            "cogs.partner",
            "cogs.utilities",
            "cogs.community",
            "cogs.spyfall",
            "cogs.server_profile",
            "cogs.verification",
            "cogs.self_roles"
        ]
        loaded = set()
        for ext in initial_extensions:
            if ext in loaded:
                logger.warning(f"Bỏ qua cog bị duplicate: {ext}")
                continue
            try:
                await self.load_extension(ext)
                loaded.add(ext)
                logger.info(f"Đã kích hoạt phân hệ Cog thành công: {ext}")
            except Exception as e:
                logger.error(f"Thất bại khi nạp phân hệ Cog {ext}: {e}")

        # 4. Không sync ở đây - self.guilds rỗng trước on_ready
        #    Việc sync được chuyển xuống on_ready

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ Lỗi: Bạn không đủ quyền hạn thực thi lệnh này.", ephemeral=True)
        elif isinstance(error, discord.app_commands.errors.CommandInvokeError):
            if isinstance(error.original, discord.errors.NotFound) and "10062" in str(error.original):
                logger.warning(f"⚠️ Interaction hết hạn (Gateway Resume) - lệnh {interaction.command.name}")
                return
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Hệ thống gặp sự cố.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Hệ thống gặp sự cố.", ephemeral=True)
        else:
            logger.error(f"Lỗi không xác định: {error}")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Lỗi prefix command '{ctx.command}': {error}")

    async def on_ready(self):
        logger.info(f"--- ĐÃ ĐĂNG NHẬP THÀNH CÔNG VỚI TÊN: {self.user} ---")
        await self.wait_until_ready()

        # Dồng bộ Slash Commands - CHỈ GUILD
        try:
            guild = discord.utils.get(self.guilds)
            if guild:
                guild_obj = discord.Object(id=guild.id)
                self.tree.copy_global_to(guild=guild_obj)
                synced = await self.tree.sync(guild=guild_obj)
                logger.info(f"⚡ Đã sync {len(synced)} slash commands cho guild {guild.name}")
            else:
                logger.warning("Bot chưa ở server nào, bỏ qua sync slash commands.")
        except Exception as e:
            logger.error(f"Lỗi sync slash commands: {e}")

        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Royal City | /help"
            )
        )
        logger.info("Hệ thống lệnh Slash đã sẵn sàng!")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # Bỏ qua lỗi CommandNotFound - đó là text listener như !so, không cần xử lý
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Lỗi prefix command '{ctx.command}': {error}")

bot = RNGBot()

# ==========================================
# SINGLE-INSTANCE LOCK: Chống chạy trùng bot
# ==========================================
LOCK_FILE = os.path.join(BASE_DIR, "bot.lock")

def check_single_instance():
    """Kiểm tra và khóa chống chạy trùng"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = f.read().strip()
            # Thử kiểm tra process
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, False, int(old_pid))
                if handle and handle.value:
                    kernel32.CloseHandle(handle)
                    # Có thể đọc lock → xem PID này còn không
                    import psutil
                    if psutil.pid_exists(int(old_pid)):
                        logger.critical(f"❌ Bot ĐÃ chạy (PID: {old_pid}). KHÔNG thể chạy thêm!")
                        return False
                # Lock cũ chết rồi, xóa
                os.remove(LOCK_FILE)
            except:
                pass
        except:
            pass
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True

if __name__ == "__main__":
    if not TOKEN:
        logger.critical("Không tìm thấy biến môi trường DISCORD_BOT_TOKEN trong file .env!")
        sys.exit(1)
    if not check_single_instance():
        sys.exit(1)
    try:
        bot.run(TOKEN)
    finally:
        try:
            os.remove(LOCK_FILE)
        except:
            pass