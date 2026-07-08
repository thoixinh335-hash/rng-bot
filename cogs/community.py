import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger("rng_bot")
CONFESSION_CHANNEL_ID = 1523960669324574750 

# ==========================================
# 1. BẢNG FORM ĐIỀN CONFESSION (MODAL)
# ==========================================
class ConfessionModal(discord.ui.Modal, title="Gửi Confession Ẩn Danh"):
    content = discord.ui.TextInput(
        label="Nhập nội dung tâm sự",
        style=discord.TextStyle.paragraph,
        placeholder="Viết những điều thầm kín vào đây...",
        required=True,
        max_length=2000
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        # Lưu vào Database (Bao gồm cả ID người gửi)
        try:
            async with await self.cog.bot.db_manager.connect() as conn:
                await conn.execute(
                    "INSERT INTO confessions (user_id, content, created_at) VALUES (?, ?, ?)",
                    (interaction.user.id, self.content.value, datetime.utcnow().isoformat())
                )
                await conn.commit()
        except Exception as e:
            logger.error(f"Lỗi lưu database confession: {e}")

        # Gửi lên kênh công khai
        channel = interaction.guild.get_channel(CONFESSION_CHANNEL_ID)
        embed = discord.Embed(
            title="💖 ROYAL CONFESSION",
            description=self.content.value,
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed.set_footer(text="Góc ẩn danh • Royal City 🌃")

        if channel:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Gửi thành công! Tâm sự của cậu đã được ẩn danh trên kênh.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Lỗi: Không tìm thấy kênh gửi Confession. Hãy báo cho Admin nhé!", ephemeral=True)

class ConfessionView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="✍️ Viết Lời Tâm Sự (Ẩn Danh)", style=discord.ButtonStyle.danger, custom_id="btn_send_confess")
    async def confess_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfessionModal(self.cog))

# ==========================================
# 2. PHÂN HỆ CHÍNH (COG)
# ==========================================
class CommunityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Chạy tác vụ kiểm tra/tạo bảng database khi bot khởi động
        self.bot.loop.create_task(self.ensure_table())

    async def ensure_table(self):
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS confessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    content TEXT,
                    created_at TEXT
                )
            """)
            await conn.commit()

    # --- LỆNH 1: /confess ---
    @app_commands.command(name="confess", description="Mở bảng gửi tâm sự ẩn danh")
    async def confess_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📬 GÓC LỜI THÚ NHẬN",
            description="Bấm vào nút bên dưới để gửi confession ẩn danh lên kênh chung nhé.",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, view=ConfessionView(self))

    # --- LỆNH 2: /nhangui ---
    @app_commands.command(name="nhangui", description="Gửi lời nhắn ngọt ngào bí mật tới ai đó")
    @app_commands.describe(user="Người nhận", message="Nội dung thư", an_danh="True để ẩn danh, False để hiện tên")
    async def nhangui_command(self, interaction: discord.Interaction, user: discord.Member, message: str, an_danh: bool = False):
        if user == interaction.user:
            return await interaction.response.send_message("⚠️ Cậu không thể tự nhắn cho chính mình đâu!", ephemeral=True)

        embed = discord.Embed(
            title="💌 BẠN CÓ MỘT LỜI NHẮN YÊU THƯƠNG!",
            description=f"```{message}```",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.set_thumbnail(url="https://media.tenor.com/T_G72gX5_0QAAAAi/love-letter-heart.gif")
        
        if an_danh:
            embed.add_field(name="👤 Người gửi:", value="*Một cư dân bí mật tại Royal City 🤫*", inline=False)
        else:
            embed.add_field(name="👤 Người gửi:", value=interaction.user.mention, inline=False)
            
        embed.set_footer(text="Gửi đi từ Royal City • Vì ai cũng xứng đáng được yêu mò 💕")

        try:
            await user.send(embed=embed)
            await interaction.response.send_message(f"✅ Đã gửi phát chuyển nhanh tới {user.mention} thành công!", ephemeral=True)
        except discord.Forbidden:
            # Nếu người đó chặn tin nhắn riêng từ người lạ/bot
            await interaction.response.send_message(content=f"💌 {user.mention} ơi! Vì cậu đang khóa DM nên tớ xin phép gửi thư tay tại đây nhé:", embed=embed)

    # --- LỆNH 3: /view_conf (BẢO MẬT HIỂN THỊ CẢ ID/MENTION) ---
    @app_commands.command(name="view_conf", description="Xem lịch sử confession (Chỉ dành cho Admin)")
    async def view_conf(self, interaction: discord.Interaction, limit: int = 5):
        # Chỉ duy nhất ID này mới có thể gọi lệnh
        ALLOWED_ID = 1119820359500304396
        if interaction.user.id != ALLOWED_ID:
            return await interaction.response.send_message("❌ Cậu không có quyền sử dụng lệnh này!", ephemeral=True)

        async with await self.bot.db_manager.connect() as conn:
            # Truy xuất thêm user_id từ database
            async with conn.execute("SELECT id, content, created_at, user_id FROM confessions ORDER BY id DESC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                
                if not rows:
                    return await interaction.response.send_message("📭 Chưa có confession nào được lưu trong database.", ephemeral=True)
                
                embed = discord.Embed(title=f"📜 {limit} Lời tâm sự gần nhất", color=discord.Color.blue())
                for r in rows:
                    conf_id, content, created_at, user_id = r
                    content_preview = content[:50] + "..." if len(content) > 50 else content
                    
                    # Hiển thị Tag tên người gửi
                    embed.add_field(
                        name=f"ID: {conf_id} • Người gửi: <@{user_id}>", 
                        value=f"📅 {created_at[:16]}\n💬 {content_preview}", 
                        inline=False
                    )
                
                # Ephemeral=True để chỉ mình cậu nhìn thấy bảng kết quả này
                await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommunityCog(bot))