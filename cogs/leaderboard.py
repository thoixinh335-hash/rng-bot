import discord
from discord.ext import commands
from discord import app_commands

class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _filter_active(self, data: list[dict]) -> list[dict]:
        """Lọc chỉ giữ lại user còn trong guild"""
        if not self.bot.guilds:
            return data
        guild = self.bot.guilds[0]  # Lấy guild đầu tiên (chỉ có 1 server)
        member_ids = {m.id for m in guild.members}
        return [row for row in data if row["user_id"] in member_ids]

    leaderboard_group = app_commands.Group(name="leaderboard", description="Bảng xếp hạng vinh danh người chơi hàng đầu.")

    @leaderboard_group.command(name="rarity", description="Xếp hạng dựa trên Danh hiệu hiếm nhất đạt được.")
    async def rarity_lb(self, interaction: discord.Interaction):
        data = await self.bot.leaderboard_service.get_top_rarity()
        data = self._filter_active(data)
        embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG: DANH HIỆU CAO NHẤT", color=discord.Color.gold())
        desc = ""
        for i, row in enumerate(data, 1):
            desc += f"`#{i}` **{row['username']}** - {row['highest_role_name']} (Rank {row['highest_rank']})\n"
        embed.description = desc or "Chưa có dữ liệu."
        await interaction.response.send_message(embed=embed)

    @leaderboard_group.command(name="collection", description="Xếp hạng dựa trên Số lượng danh hiệu đã sưu tập.")
    async def collection_lb(self, interaction: discord.Interaction):
        data = await self.bot.leaderboard_service.get_top_collection()
        data = self._filter_active(data)
        embed = discord.Embed(title="📦 BẢNG XẾP HẠNG: BỘ SƯU TẬP", color=discord.Color.purple())
        desc = ""
        for i, row in enumerate(data, 1):
            desc += f"`#{i}` **{row['username']}** - {row['collection_count']}/30 Danh hiệu\n"
        embed.description = desc or "Chưa có dữ liệu."
        await interaction.response.send_message(embed=embed)

    @leaderboard_group.command(name="lucky", description="Xếp hạng dựa trên Điểm số may mắn hiện tại.")
    async def lucky_lb(self, interaction: discord.Interaction):
        data = await self.bot.leaderboard_service.get_top_lucky()
        data = self._filter_active(data)
        embed = discord.Embed(title="🔮 BẢNG XẾP HẠNG: LUCK TÍCH LŨY", color=discord.Color.blurple())
        desc = ""
        for i, row in enumerate(data, 1):
            desc += f"`#{i}` **{row['username']}** - +{row['lucky']}% Luck\n"
        embed.description = desc or "Chưa có dữ liệu."
        await interaction.response.send_message(embed=embed)

    @leaderboard_group.command(name="rolls", description="Xếp hạng dựa trên Tổng số lần thực hiện Roll.")
    async def rolls_lb(self, interaction: discord.Interaction):
        data = await self.bot.leaderboard_service.get_top_rolls()
        data = self._filter_active(data)
        embed = discord.Embed(title="📊 BẢNG XẾP HẠNG: TỔNG SỐ LẦN ROLL", color=discord.Color.blue())
        desc = ""
        for i, row in enumerate(data, 1):
            desc += f"`#{i}` **{row['username']}** - {row['total_rolls']:,} lượt\n"
        embed.description = desc or "Chưa có dữ liệu."
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))