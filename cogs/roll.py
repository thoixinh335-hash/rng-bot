import discord
from discord.ext import commands
from discord import app_commands
from services.config_service import ConfigService

class RollCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_service = ConfigService()

    @app_commands.command(name="roll", description="Thực hiện lượt quay may mắn 12 giờ để săn danh hiệu tối cao.")
    async def roll(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        user = interaction.user
        player_service = self.bot.player_service
        cooldown_service = self.bot.cooldown_service
        rng_engine = self.bot.rng_engine
        role_manager = self.bot.role_manager
        announcement_service = self.bot.announcement_service
        season_service = self.bot.season_service

        # Tự động cập nhật trạng thái mùa giải trước khi thực hiện tác vụ
        await season_service.check_and_update_season()
        player = await player_service.get_player(user.id)
        
        if not player:
            roles_list = self.config_service.get_roles_list()
            player = await player_service.create_player(user.id, user.name, roles_list[0])

        is_available, remaining = cooldown_service.check_cooldown(player["last_roll"])
        if not is_available:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            seconds = int(remaining % 60)
            
            embed = discord.Embed(
                title="⏳ VÒNG QUAY ĐANG TRONG THỜI GIAN CHỜ",
                description=f"Thao tác quá nhanh! Bạn đã sử dụng lượt quay của phiên này rồi.\n\n`⏱️` Vui lòng quay lại sau: **{hours:02d} giờ {minutes:02d} phút {seconds:02d} giây**",
                color=discord.Color.from_rgb(255, 75, 75)
            )
            embed.set_footer(text="Mẹo: Hệ thống hồi chiêu tự động mỗi 12 giờ.")
            await interaction.followup.send(embed=embed)
            return

        rolled_role = rng_engine.roll(player["lucky"])
        
        galactic_rank = self.config_service.get("galactic_rank", 19)
        if rolled_role["rank"] < galactic_rank:
            next_lucky = player["lucky"] + 1
        else:
            next_lucky = 0

        is_highest = rolled_role["rank"] > player["highest_rank"]
        
        # Lưu kết quả an toàn bằng Transaction
        await player_service.process_roll_transaction(
            user_id=user.id, username=user.name, rolled_role=rolled_role,
            is_highest=is_highest, next_lucky=next_lucky
        )

        # Đồng bộ vai trò trên Discord Server
        await role_manager.update_discord_roles(interaction.guild.get_member(user.id), rolled_role["role_id"])
        await announcement_service.broadcast_roll(user, rolled_role)

        # Giao diện đóng khung Roblox Gaming Style cực đẹp
        color = int(rolled_role["embed_color"], 16)
        embed = discord.Embed(
            title="✨ VÒNG QUAY HOÀN TẤT ✨",
            description=f"{user.mention} vừa bẻ gãy dòng thời gian và nhận được:\n\n**▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬**\n{rolled_role['emoji']}  **{rolled_role['name'].upper()}**\n**▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬**",
            color=color
        )
        
        embed.add_field(name="🎲 CƠ HỘI GỐC", value=f"`1 in {rolled_role['chance']:,}`", inline=True)
        embed.add_field(name="🔮 LUCK ĐÃ DÙNG", value=f"`+{player['lucky']}%`", inline=True)
        embed.add_field(name="📈 LUCK LƯỢT SAU", value=f"`+{next_lucky}%`" if next_lucky > 0 else "`Reset (0%)`", inline=True)
        
        # Thanh tiến trình đồ họa giả lập thời gian hồi chiêu
        embed.add_field(name="⏱️ TRẠNG THÁI HỒI CHIÊU", value="🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 `12 Giờ`", inline=False)
        
        if is_highest:
            embed.add_field(name="🏆 KỶ LỤC MỚI", value=f"Đây là Danh hiệu có cấp bậc tốt nhất từ trước tới nay của bạn! (Rank {rolled_role['rank']})", inline=False)
            
        embed.set_footer(text=f"RNG BOT • Tổng số lần bạn đã roll: {player['total_rolls'] + 1:,}")
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(RollCog(bot))