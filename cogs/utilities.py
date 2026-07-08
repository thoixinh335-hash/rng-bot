import discord
from discord.ext import commands
import random
from datetime import datetime

# Danh sách lời chúc/lời chữa lành ngọt ngào cho lệnh /healing
HEALING_QUOTES = [
    "Cậu đã làm rất tốt ngày hôm nay rồi. Giờ thì thả lỏng bờ vai, hít một hơi thật sâu và để mọi mệt mỏi trôi đi nhé. Royal City luôn ở bên cậu! 💕",
    "Nếu hôm nay thế giới có khắt khe với cậu quá, thì hãy về đây nhé. Ở Royal City luôn có những cái ôm ấm áp và cam kết 'hog bơ mem iu' chờ cậu. 🌸",
    "Đừng áp lực quá nhé, mỗi bông hoa đều có thời gian nở rộ của riêng mình. Cậu cứ đi theo tiến độ của cậu, cậu đang làm tốt lắm rồi! ✨",
    "Ngày hôm nay của cậu thế nào? Nếu chưa tốt thì cũng không sao cả, ngày mai là một cơ hội mới. Hãy nghỉ ngơi thật tốt để lấy sức nha. 🌙",
    "Cậu xứng đáng được yêu thương, xứng đáng được hạnh phúc. Đừng vì vài lời tiêu cực của người khác mà hoài nghi bản thân mình nhé! 🧸",
    "Một ngày mệt mỏi rồi đúng không? Đi uống một ngụm nước ấm, đắp chăn thật êm rồi lướt Royal City tán gẫu với bọn tớ một tí cho khuây khỏa nha. ☕"
]

# Danh sách lời thì thầm ban đêm cho lệnh /goidem
NIGHT_QUOTES = [
    "Chào cú đêm của Royal City! Tầm này thế giới ngủ hết rồi, chỉ còn những tâm hồn cô đơn tụ họp ở đây thôi. Cậu đang làm gì đấy? 🦉",
    "Giờ này mà cậu chưa ngủ là đang nhớ người yêu cũ hay đang chờ một tin nhắn vậy? Nếu không có ai nhắn tin thì ở đây buôn chuyện với tụi tớ nè. 👻",
    "Thức đêm có hại cho sức khỏe lắm á, nhưng mà thức đêm ở Royal City thì... vui quá không nỡ đi ngủ đúng không? Cơ mà muộn rồi, nhớ chú ý sức khỏe nha. 🌃",
    "Không gian đêm muộn luôn là lúc chúng ta sống thật với cảm xúc nhất. Nếu có tâm sự gì khó nói, cứ thoải mái chia sẻ với mọi người ở đây nha, tụi tớ lắng nghe. 💜",
    "Đêm đã về khuya, chúc cho những suy nghĩ ngổn ngang trong đầu cậu sớm được dẹp gọn. Chúc cậu có một giấc ngủ thật ngon và những giấc mơ thật đẹp! 🌠"
]

class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. LỆNH CHỮA LÀNH
    @commands.hybrid_command(name="healing", description="Nhận một lời chữa lành ấm áp từ Royal City")
    async def healing_command(self, ctx: commands.Context):
        quote = random.choice(HEALING_QUOTES)
        
        embed = discord.Embed(
            title="🌸 TIỆM CHỮA LÀNH ROYAL CITY",
            description=quote,
            color=discord.Color.from_rgb(255, 182, 193) # Màu hồng pastel dịu mắt
        )
        # Đã cập nhật link GIF Tenor bông hoa mặt trời ôm tim cực bền
        embed.set_thumbnail(url="https://media.tenor.com/7S8EOnI3VfEAAAAi/flower-cute.gif") 
        embed.set_footer(text=f"Gửi tặng đến tâm hồn của {ctx.author.display_name} ❤️")
        
        await ctx.send(embed=embed)

    # 2. LỆNH SỐNG VỀ ĐÊM
    @commands.hybrid_command(name="goidem", description="Lời thì thầm dành riêng cho cư dân sống về đêm (23h - 5h)")
    async def goidem_command(self, ctx: commands.Context):
        current_hour = datetime.now().hour
        
        # Chỉ hoạt động từ 23h đêm đến 5h sáng
        if current_hour >= 23 or current_hour < 5:
            quote = random.choice(NIGHT_QUOTES)
            embed = discord.Embed(
                title="🌙 GÓC CÚ ĐÊM • ROYAL CITY",
                description=quote,
                color=discord.Color.from_rgb(44, 62, 80) # Màu xanh đêm thẫm
            )
            embed.set_footer(text="Chúng tớ sống về đêm • Cam kết hog bơ mem iu 🦉")
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                "🛑 **Chưa đến giờ 'sống về đêm' đâu nè!** Lệnh này chỉ kích hoạt từ **23h00 đêm đến 05h00 sáng** thôi. "
                "Ban ngày cậu hãy chăm chỉ học tập/làm việc nhé, hẹn gặp lại cậu lúc nửa đêm! ☀️",
                ephemeral=True
            )

    # 3. LỆNH THÔNG TIN SERVER
    @commands.hybrid_command(name="serverinfo", description="Xem thông tin chi tiết đầy tự hào của Royal City")
    async def serverinfo_command(self, ctx: commands.Context):
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ Lệnh này chỉ có thể sử dụng bên trong Server.")
            return

        created_at = guild.created_at.strftime("%d/%m/%Y")
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        
        embed = discord.Embed(
            title=f"🏰 THÔNG TIN MÁY CHỦ: {guild.name}",
            description="Chào mừng bạn đến với Ngôi Nhà Chung của chúng mình! Nơi gắn kết, chữa lành và no toxic.",
            color=discord.Color.gold()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Chủ sở hữu (Owner)", value=guild.owner.mention if guild.owner else "Không xác định", inline=True)
        embed.add_field(name="📅 Ngày thành lập", value=created_at, inline=True)
        embed.add_field(name="👥 Tổng thành viên", value=f"**{guild.member_count}** thành viên", inline=True)
        
        embed.add_field(name="💬 Kênh văn bản", value=f"{text_channels} kênh", inline=True)
        embed.add_field(name="🔊 Kênh đàm thoại", value=f"{voice_channels} kênh", inline=True)
        embed.add_field(name="🛡️ Tổng số vai trò (Roles)", value=f"{len(guild.roles)} vai trò", inline=True)
        
        embed.add_field(name="💎 Cấp độ Boost", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="✨ Tổng số Boosts", value=f"{guild.premium_subscription_count} Boosts", inline=True)
        embed.add_field(name="🔒 Mức độ bảo mật", value=str(guild.verification_level).title(), inline=True)

        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name} • Royal City Bot", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilitiesCog(bot))