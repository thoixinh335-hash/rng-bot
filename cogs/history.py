import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from services.config_service import ConfigService

class HistoryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_service = ConfigService()

    @app_commands.command(name="history", description="Liệt kê danh sách 20 lượt quay gần đây nhất của bạn.")
    async def history(self, interaction: discord.Interaction):
        user = interaction.user
        
        async with await self.bot.db_manager.connect() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT role_id, rolled_at FROM history 
                WHERE user_id = ? ORDER BY id DESC LIMIT 20
            """, (user.id,)) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message("Hệ thống chưa ghi nhận lịch sử vòng quay nào của bạn.")
            return

        embed = discord.Embed(title=f"📜 LỊCH SỬ QUAY GẦN ĐÂY - {user.name}", color=discord.Color.blue())
        
        lines = []
        for index, row in enumerate(rows, 1):
            role = self.config_service.get_role_by_id(row["role_id"])
            if role:
                lines.append(f"`#{index:02d}` {role['emoji']} **{role['name']}** - <t:{int(discord.utils.parse_time(row['rolled_at']).timestamp())}:R>")
        
        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HistoryCog(bot))