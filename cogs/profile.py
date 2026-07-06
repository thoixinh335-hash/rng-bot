import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from services.config_service import ConfigService

class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_service = ConfigService()

    async def _build_profile_embed(self, user: discord.User) -> discord.Embed | None:
        """Tạo embed profile cho user, trả về None nếu chưa có dữ liệu"""
        player = await self.bot.player_service.get_player(user.id)

        if not player:
            return None

        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT COUNT(*) FROM collections WHERE user_id = ?", (user.id,)) as cursor:
                count_row = await cursor.fetchone()
                collection_count = count_row[0]

        # Lấy rolls_used trong window hiện tại
        from datetime import datetime, timedelta
        rolls_used = player.get("rolls_used", 0) or 0
        roll_limit = self.config_service.get("roll_limit", 3)
        window_start_str = player.get("rolls_window_start")

        rolls_text = f"🎲 Đã dùng: **{rolls_used}/{roll_limit}** (3 tiếng)"

        current_role = self.config_service.get_role_by_id(player["current_role_id"])
        highest_role = self.config_service.get_role_by_id(player["highest_role_id"])
        color = int(highest_role["embed_color"], 16) if highest_role else discord.Color.blue().value

        # Thiết lập cấu trúc giao diện Neon Card cao cấp
        embed = discord.Embed(
            title=f"🎮 THẺ THÔNG TIN RNG • {user.name.upper()}",
            description=f"**Mùa Giải:** `Season {await self.bot.season_service.get_current_season_number()}`\n{rolls_text}",
            color=color
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(name="🎭 Đang Trang Bị", value=f"{current_role['emoji'] if current_role else '⚪'} `{player['current_role_name']}`", inline=True)
        embed.add_field(name="🏆 Đỉnh Cao (Best)", value=f"{highest_role['emoji'] if highest_role else '⚪'} `{player['highest_role_name']}`", inline=True)
        embed.add_field(name="🔮 Điểm May Mắn", value=f"`+{player['lucky']}% Luck`", inline=True)

        # Hệ thống tính toán thanh tiến trình Collection (3 danh hiệu tương đương 1 khối xanh)
        blocks = max(0, min(10, int(collection_count // 3)))
        progress_bar = "🟩" * blocks + "⬛" * (10 - blocks)
        embed.add_field(name="📦 Bộ Sưu Tập Danh Hiệu", value=f"{progress_bar}\n📊 Đã mở khóa: **{collection_count} / 30**", inline=False)

        embed.set_footer(text=f"Tổng số lượt quay: {player['total_rolls']:,} rolls")
        return embed

    @app_commands.command(name="profile", description="Xem thẻ thông tin RNG. Có thể xem của người khác bằng @user.")
    @app_commands.describe(user="Người chơi muốn xem (mặc định là bạn)")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        embed = await self._build_profile_embed(target)

        if not embed:
            if target.id == interaction.user.id:
                embed = discord.Embed(
                    description="❌ Bạn chưa có dữ liệu hành trình. Hãy gõ `/roll` để khởi tạo nhân vật!",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    description=f"❌ **{target.name}** chưa có dữ liệu trong hệ thống.",
                    color=discord.Color.orange()
                )
            await interaction.response.send_message(embed=embed)
            return

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))