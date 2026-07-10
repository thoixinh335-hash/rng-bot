import discord
from discord.ext import commands
import random
from datetime import datetime
import aiohttp

# Map cung hoàng đạo tiếng Việt -> API name
ZODIAC_MAP = {
    "Bạch Dương ♈": "aries", "Kim Ngưu ♉": "taurus", "Song Tử ♊": "gemini",
    "Cự Giải ♋": "cancer", "Sư Tử ♌": "leo", "Xử Nữ ♍": "virgo",
    "Thiên Bình ♎": "libra", "Bọ Cạp ♏": "scorpio", "Nhân Mã ♐": "sagittarius",
    "Ma Kết ♑": "capricorn", "Bảo Bình ♒": "aquarius", "Song Ngư ♓": "pisces"
}

ZODIAC_DATES = {
    "Bạch Dương ♈": "21/03 - 19/04", "Kim Ngưu ♉": "20/04 - 20/05",
    "Song Tử ♊": "21/05 - 20/06", "Cự Giải ♋": "21/06 - 22/07",
    "Sư Tử ♌": "23/07 - 22/08", "Xử Nữ ♍": "23/08 - 22/09",
    "Thiên Bình ♎": "23/09 - 22/10", "Bọ Cạp ♏": "23/10 - 21/11",
    "Nhân Mã ♐": "22/11 - 21/12", "Ma Kết ♑": "22/12 - 19/01",
    "Bảo Bình ♒": "20/01 - 18/02", "Song Ngư ♓": "19/02 - 20/03"
}

COMPATIBILITY_VN = {
    "aries": "Bạch Dương ♈", "taurus": "Kim Ngưu ♉", "gemini": "Song Tử ♊",
    "cancer": "Cự Giải ♋", "leo": "Sư Tử ♌", "virgo": "Xử Nữ ♍",
    "libra": "Thiên Bình ♎", "scorpio": "Bọ Cạp ♏", "sagittarius": "Nhân Mã ♐",
    "capricorn": "Ma Kết ♑", "aquarius": "Bảo Bình ♒", "pisces": "Song Ngư ♓"
}

def calc_zodiac(birthday_str: str) -> str | None:
    """Tính cung hoàng đạo từ ngày sinh dd/mm/yyyy"""
    try:
        parts = birthday_str.replace("-", "/").replace(".", "/").split("/")
        day, month = int(parts[0]), int(parts[1])
        if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "Bạch Dương ♈"
        if (month == 4 and day >= 20) or (month == 5 and day <= 20): return "Kim Ngưu ♉"
        if (month == 5 and day >= 21) or (month == 6 and day <= 20): return "Song Tử ♊"
        if (month == 6 and day >= 21) or (month == 7 and day <= 22): return "Cự Giải ♋"
        if (month == 7 and day >= 23) or (month == 8 and day <= 22): return "Sư Tử ♌"
        if (month == 8 and day >= 23) or (month == 9 and day <= 22): return "Xử Nữ ♍"
        if (month == 9 and day >= 23) or (month == 10 and day <= 22): return "Thiên Bình ♎"
        if (month == 10 and day >= 23) or (month == 11 and day <= 21): return "Bọ Cạp ♏"
        if (month == 11 and day >= 22) or (month == 12 and day <= 21): return "Nhân Mã ♐"
        if (month == 12 and day >= 22) or (month == 1 and day <= 19): return "Ma Kết ♑"
        if (month == 1 and day >= 20) or (month == 2 and day <= 18): return "Bảo Bình ♒"
        if (month == 2 and day >= 19) or (month == 3 and day <= 20): return "Song Ngư ♓"
    except: pass
    return None

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

    # 4. LỆNH BÓI TOÁN - Dữ liệu thật từ API
    @commands.hybrid_command(name="boi_toan", description="Xem tử vi hôm nay theo cung hoàng đạo của bạn 🔮 (Dữ liệu thật)")
    async def boi_toan(self, ctx: commands.Context):
        await ctx.defer()

        # Lấy cung hoàng đạo từ hồ sơ
        zodiac_key = None
        try:
            async with await self.bot.db_manager.connect() as conn:
                async with conn.execute("SELECT birthday FROM royal_profiles WHERE user_id = ?", (ctx.author.id,)) as cursor:
                    row = await cursor.fetchone()
            if row and row[0] and row[0] != "Chưa cập nhật 📅":
                zodiac_key = calc_zodiac(row[0])
        except:
            pass

        if not zodiac_key or zodiac_key not in ZODIAC_MAP:
            return await ctx.send(
                "❌ Không thể xác định cung hoàng đạo của bạn!\n"
                "📝 Hãy cập nhật **ngày sinh** trong hồ sơ trước: `/sua_hoso ngay_sinh:dd/mm/yyyy`\n"
                "💡 Ví dụ: `/sua_hoso ngay_sinh:26/08/2000`"
            )

        api_sign = ZODIAC_MAP[zodiac_key]
        api_url = f"https://aztro.sameerkumar.website/?sign={api_sign}&day=today"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url) as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Máy chủ tử vi đang bận, thử lại sau nhé!")
                    data = await resp.json()
        except Exception:
            return await ctx.send("❌ Không thể kết nối đến máy chủ tử vi. Thử lại sau nhé!")

        compat_vn = COMPATIBILITY_VN.get(data.get("compatibility", "").lower(), data.get("compatibility", "???"))

        embed = discord.Embed(
            title=f"🔮 TỬ VI HÔM NAY CHO {ctx.author.display_name} 🔮",
            description=f"✨ **{zodiac_key}** ({ZODIAC_DATES.get(zodiac_key, '')}) | Ngày {data.get('current_date', 'hôm nay')}",
            color=discord.Color.purple()
        )

        embed.add_field(name="📝 **Tổng quan:**", value=data.get("description", "Không có dữ liệu."), inline=False)
        embed.add_field(name="😊 **Tâm trạng:**", value=data.get("mood", "???"), inline=True)
        embed.add_field(name="💞 **Hợp nhất với:**", value=compat_vn, inline=True)
        embed.add_field(name="🌈 **Màu sắc may mắn:**", value=data.get("color", "???"), inline=True)
        embed.add_field(name="🎲 **Con số may mắn:**", value=f"`{data.get('lucky_number', '???')}`", inline=True)
        embed.add_field(name="⏰ **Khung giờ may mắn:**", value=data.get("lucky_time", "???"), inline=True)

        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_footer(text="🔮 Dữ liệu tử vi thật từ Aztro API | Royal City Fortune")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UtilitiesCog(bot))