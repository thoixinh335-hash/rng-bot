import discord
from services.config_service import ConfigService

class AnnouncementService:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.config_service = ConfigService()

    async def broadcast_roll(self, user: discord.User, role: dict) -> None:
        channel_id = self.config_service.get("announcement_channel")
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
        if not channel:
            return

        rank = role["rank"]
        galactic_rank = self.config_service.get("galactic_rank", 19)
        seraph_rank = self.config_service.get("seraph_rank", 25)
        secret_rank = self.config_service.get("secret_rank", 30)

        color = int(role["embed_color"], 16)
        
        if rank >= secret_rank:
            # Thông báo Tuyệt Mật đặc biệt (Secret)
            embed = discord.Embed(
                title="👑 TOÀN SERVER CHÚ Ý - DANH HIỆU TỐI MẬT XUẤT HIỆN 👑",
                description=f"**{user.mention}** vừa phá vỡ thực tại và nhận được danh hiệu tối mật: {role['emoji']} **{role['name']}**!\n\nTỷ lệ không tưởng: **1/{role['chance']:,}**",
                color=discord.Color.from_rgb(255, 20, 147)
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_image(url="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbWdtcm90YXp5b3B6ZnduN3Fma290bXN6cmN0ZzZ3NmR2NWhsc2F0NyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7qE1YN7aBOFPRw8E/giphy.gif")
            await channel.send(content="@everyone 🌌 SỰ KIỆN HUYỀN THOẠI!", embed=embed)
            
        elif rank >= seraph_rank:
            embed = discord.Embed(
                title="👼 THẦN THOẠI GIÁNG LÂM 👼",
                description=f"Một thực thể cấp cao xuất hiện! **{user.mention}** đã đạt được: {role['emoji']} **{role['name']}**\nCơ hội xuất hiện: **1/{role['chance']:,}**",
                color=color
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(content="@everyone", embed=embed)
            
        elif rank >= galactic_rank:
            embed = discord.Embed(
                title="🌀 SỨC MẠNH VŨ TRỤ 🌀",
                description=f"Chúc mừng **{user.mention}** đã roll thành công danh hiệu vĩ đại: {role['emoji']} **{role['name']}**\nTỷ lệ: **1/{role['chance']:,}**",
                color=color
            )
            await channel.send(embed=embed)