import discord
from discord.ext import commands
from discord import app_commands
from services.config_service import ConfigService

class CollectionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_service = ConfigService()

    @app_commands.command(name="collection", description="Hiển thị bộ sưu tập đầy đủ 30 danh hiệu trong game.")
    async def collection(self, interaction: discord.Interaction):
        user = interaction.user
        roles = self.config_service.get_roles_list()
        
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT role_id FROM collections WHERE user_id = ?", (user.id,)) as cursor:
                rows = await cursor.fetchall()
                owned_ids = {r[0] for r in rows}

        embed = discord.Embed(
            title=f"📦 BỘ SƯU TẬP DANH HIỆU - {user.name}",
            description="Tìm kiếm và mở khóa toàn bộ 30 danh hiệu ẩn giấu thế giới.",
            color=discord.Color.dark_magenta()
        )

        # Chia nhỏ danh sách hiển thị để tránh vượt giới hạn ký tự của Discord Embed
        field_text = ""
        for index, r in enumerate(roles, 1):
            if r["role_id"] in owned_ids:
                field_text += f"`{index:02d}` {r['emoji']} **{r['name']}** (1/{r['chance']:,})\n"
            else:
                field_text += f"`{index:02d}` ❓ ???\n"
            
            if index % 15 == 0 or index == len(roles):
                start = index - 14 if index % 15 == 0 else ((index - 1) // 15) * 15 + 1
                embed.add_field(name=f"Danh sách từ {start} đến {index}", value=field_text, inline=False)
                field_text = ""

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(CollectionCog(bot))