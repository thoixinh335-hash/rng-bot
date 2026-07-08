import discord
from discord.ext import commands, tasks
import datetime
import random
import logging

logger = logging.getLogger("rng_bot")

# CẤU HÌNH HỆ THỐNG
TARGET_CHANNEL_ID = 1503825245671395368  # ID kênh chat của bạn
IDLE_TIMEOUT_SECONDS = 300               # Thời gian kẹt chat (5 phút = 300 giây)

# KHO CÂU THOẠI KÍCH CHAT (Bạn có thể tự do thêm bớt câu thoại văn vở tại đây)
REVIVAL_MESSAGES = [
    "Ủa mọi người ơi, tự dưng im ắng thế? Đang bận trốn đi ngủ hết rồi à? 🦉",
    "Kênh chat hôm nay trôi chậm quá, ai đó thả một chiếc meme cứu rỗi bầu không khí này đi! 🥺",
    "Phòng chat bỗng dưng lặng gió... Có ai đang online đó không, chấm một cái cho tớ biết với nào! ✨",
    "Tầm này mà im lặng thế này là đáng nghi lắm nha, hay là mọi người đang rủ nhau đi chơi bí mật bỏ rơi tớ rồi? 🔎",
    "Hú hồn, tớ cứ tưởng mất mạng! Sao tự dưng im re vậy các cư dân Royal City ơi? Đọc được tin nhắn này thì rep tớ nha! 🏰",
    "Góc tìm người lạc: Ai đó vào phá tan cái sự im lặng đáng sợ này giùm tớ với! 💥"
]

class ChatReviverCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Khởi tạo mốc thời gian tin nhắn cuối cùng bằng giờ hiện tại lúc bật bot
        self.last_message_time = datetime.datetime.now(datetime.timezone.utc)
        # Bắt đầu kích hoạt vòng lặp chạy ngầm
        self.check_chat_idle.start()

    def cog_unload(self):
        # Tắt vòng lặp khi bot unload phân hệ để tránh tốn tài nguyên
        self.check_chat_idle.cancel()

    # ==========================================
    # LẮNG NGHE LƯỢT CHAT MỚI ĐỂ RESET THỜI GIAN
    # ==========================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Nếu có ai đó chat tại đúng kênh chỉ định và người đó KHÔNG PHẢI BOT
        if message.channel.id == TARGET_CHANNEL_ID and not message.author.bot:
            # Cập nhật lại mốc thời gian tin nhắn cuối cùng sang thời gian hiện tại
            self.last_message_time = datetime.datetime.now(datetime.timezone.utc)

    # ==========================================
    # VÒNG LẶP KIỂM TRA NGẦM (CỨ 15 GIÂY QUÉT 1 LẦN)
    # ==========================================
    @tasks.loop(seconds=15)
    async def check_chat_idle(self):
        # Đợi cho tới khi bot đăng nhập thành công hoàn toàn mới chạy lệnh
        if not self.bot.is_ready():
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        # Tính toán số giây im lặng tính từ tin nhắn cuối cùng
        time_passed = (now - self.last_message_time).total_seconds()

        # Nếu thời gian im lặng vượt ngưỡng cấu hình (5 phút)
        if time_passed >= IDLE_TIMEOUT_SECONDS:
            channel = self.bot.get_channel(TARGET_CHANNEL_ID)
            if channel:
                try:
                    # Bốc ngẫu nhiên một câu văn vở trong kho thoại
                    random_msg = random.choice(REVIVAL_MESSAGES)
                    await channel.send(random_msg)
                    logger.info("🎤 Kênh chính bị bơ quá 5 phút. Bot đã chủ động gửi tin nhắn kích chat.")
                except Exception as e:
                    logger.error(f"Lỗi không thể gửi tin nhắn kích chat: {e}")
            
            # QUAN TRỌNG: Ghi đè lại mốc thời gian hiện tại ngay sau khi bot nhắn câu kích chat,
            # điều này giúp bot không bị spam liên tục sau mỗi 15 giây tiếp theo.
            self.last_message_time = datetime.datetime.now(datetime.timezone.utc)

async def setup(bot):
    await bot.add_cog(ChatReviverCog(bot))