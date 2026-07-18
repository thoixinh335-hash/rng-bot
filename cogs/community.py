import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger("rng_bot")
CONFESSION_CHANNEL_ID = 1503825245671395368
CONFESSION_CHANNEL_ID_OLD = 1523960669324574750

# ==========================================
# MODAL REPLY CHO CONFESSION (kênh chung)
# ==========================================
class ConfessionReplyModal(discord.ui.Modal, title="💬 Gửi Reply cho Confession"):
    reply_text = discord.ui.TextInput(
        label="Nội dung reply",
        style=discord.TextStyle.paragraph,
        placeholder="Viết lời nhắn gửi đến người đã gửi confession...",
        required=True,
        max_length=1500
    )

    def __init__(self, confession_id: int, target_user_id: int, original_content: str):
        super().__init__()
        self.confession_id = confession_id
        self.target_user_id = target_user_id
        self.original_content = original_content

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        target_member = guild.get_member(self.target_user_id)
        if not target_member:
            try:
                target_member = await guild.fetch_member(self.target_user_id)
            except:
                target_member = None

        embed_reply = discord.Embed(
            title="💬 CÓ NGƯỜI REPLY CONFESSION CỦA BẠN!",
            description=f"**Confession gốc:**\n> {self.original_content[:500]}",
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed_reply.add_field(
            name="📨 Tin nhắn reply",
            value=self.reply_text.value,
            inline=False
        )
        embed_reply.set_footer(text="Góc ẩn danh • Royal City 🌃")

        if target_member:
            try:
                await target_member.send(embed=embed_reply)
                await interaction.response.send_message(
                    "✅ Reply của bạn đã được gửi đến người đó (qua DM riêng tư)!",
                    ephemeral=True
                )
                return
            except discord.Forbidden:
                pass

        await interaction.response.send_message(
            f"💬 Reply dành cho confession #{self.confession_id} (không DM được):\n{self.reply_text.value}",
            ephemeral=True
        )

class ConfessionReplyView(discord.ui.View):
    def __init__(self, confession_id: int, target_user_id: int, original_content: str):
        super().__init__(timeout=None)
        self.confession_id = confession_id
        self.target_user_id = target_user_id
        self.original_content = original_content

    @discord.ui.button(label="💬 Reply", style=discord.ButtonStyle.primary, emoji="✉️")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ConfessionReplyModal(self.confession_id, self.target_user_id, self.original_content)
        await interaction.response.send_modal(modal)


# ==========================================
# MODAL REPLY CHO /NHANGUI (DM riêng)
# ==========================================
class NhangReplyModal(discord.ui.Modal, title="💬 Trả lời tin nhắn"):
    reply_text = discord.ui.TextInput(
        label="Nội dung trả lời",
        style=discord.TextStyle.paragraph,
        placeholder="Viết gì đó gửi lại cho người ta đi...",
        required=True,
        max_length=1500
    )

    def __init__(self, sender_id: int, an_danh: bool, original_message: str):
        super().__init__()
        self.sender_id = sender_id
        self.an_danh = an_danh
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        sender = guild.get_member(self.sender_id)
        if not sender:
            try:
                sender = await guild.fetch_member(self.sender_id)
            except:
                sender = None

        embed = discord.Embed(
            title="💬 CÓ NGƯỜI ĐÃ TRẢ LỜI TIN NHẮN CỦA BẠN!",
            description=f"**Tin nhắn gốc của bạn:**\n> {self.original_message[:500]}",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.add_field(name="📨 Trả lời", value=self.reply_text.value, inline=False)

        if self.an_danh:
            embed.add_field(name="👤 Người trả lời:", value="*Một cư dân bí mật 🤫*", inline=False)
        else:
            embed.add_field(name="👤 Người trả lời:", value=interaction.user.mention, inline=False)

        embed.set_footer(text="Reply tự động • Royal City 🌃")

        if sender:
            try:
                await sender.send(embed=embed)
                await interaction.response.send_message(
                    "✅ Tin nhắn của bạn đã được gửi đến người đó!",
                    ephemeral=True
                )
                return
            except discord.Forbidden:
                pass

        await interaction.response.send_message(
            "⚠️ Không thể gửi DM cho người đó (họ tắt DM hoặc không ở trong server).",
            ephemeral=True
        )

class NhangReplyView(discord.ui.View):
    def __init__(self, sender_id: int, an_danh: bool, original_message: str):
        super().__init__(timeout=None)
        self.sender_id = sender_id
        self.an_danh = an_danh
        self.original_message = original_message

    @discord.ui.button(label="💬 Trả lời", style=discord.ButtonStyle.primary, emoji="✉️")
    async def reply_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = NhangReplyModal(self.sender_id, self.an_danh, self.original_message)
        await interaction.response.send_modal(modal)


# ==========================================
# FORM ĐIỀN CONFESSION (MODAL)
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
        confession_id = None
        try:
            async with await self.cog.bot.db_manager.connect() as conn:
                cursor = await conn.execute(
                    "INSERT INTO confessions (user_id, content, created_at) VALUES (?, ?, ?)",
                    (interaction.user.id, self.content.value, datetime.utcnow().isoformat())
                )
                await conn.commit()
                confession_id = cursor.lastrowid
        except Exception as e:
            logger.error(f"Lỗi lưu database confession: {e}")

        channel = interaction.guild.get_channel(CONFESSION_CHANNEL_ID)
        embed = discord.Embed(
            title="💖 ROYAL CONFESSION",
            description=self.content.value,
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed.set_footer(text="Góc ẩn danh • Royal City 🌃")

        if channel:
            view = ConfessionReplyView(
                confession_id=confession_id,
                target_user_id=interaction.user.id,
                original_content=self.content.value
            ) if confession_id else None
            await channel.send(embed=embed, view=view)
            # Gửi thêm vào kênh cũ
            channel_old = interaction.guild.get_channel(CONFESSION_CHANNEL_ID_OLD)
            if channel_old and channel_old != channel:
                await channel_old.send(embed=embed)
            await interaction.response.send_message("✅ Gửi thành công! Tâm sự của cậu đã được ẩn danh trên kênh.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Lỗi: Không tìm thấy kênh gửi Confession.", ephemeral=True)


class ConfessionView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="✍️ Viết Lời Tâm Sự (Ẩn Danh)", style=discord.ButtonStyle.danger, custom_id="btn_send_confess")
    async def confess_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfessionModal(self.cog))


# ==========================================
# PHÂN HỆ CHÍNH (COG)
# ==========================================
class CommunityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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
            # Migration: thêm cột user_id nếu chưa có (khi restore từ backup cũ)
            try:
                await conn.execute("ALTER TABLE confessions ADD COLUMN user_id INTEGER")
            except:
                pass
            await conn.commit()

    @app_commands.command(name="confess", description="Mở bảng gửi tâm sự ẩn danh")
    async def confess_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📬 GÓC LỜI THÚ NHẬN",
            description="Bấm vào nút bên dưới để gửi confession ẩn danh lên kênh chung nhé.",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, view=ConfessionView(self), ephemeral=True)

    @app_commands.command(name="nhangui", description="Gửi lời nhắn ngọt ngào bí mật tới ai đó")
    @app_commands.describe(user="Người nhận", message="Nội dung thư", an_danh="True để ẩn danh, False để hiện tên")
    async def nhangui_command(self, interaction: discord.Interaction, user: discord.Member, message: str, an_danh: bool = True):
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

        view = NhangReplyView(
            sender_id=interaction.user.id,
            an_danh=an_danh,
            original_message=message
        )

        try:
            await user.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Đã gửi phát chuyển nhanh tới {user.mention} thành công!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(content=f"💌 {user.mention} ơi! Vì cậu đang khóa DM nên tớ xin phép gửi thư tay tại đây nhé:", embed=embed)

async def setup(bot):
    await bot.add_cog(CommunityCog(bot))
