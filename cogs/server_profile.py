import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import logging
import io
import aiohttp
import urllib.parse

logger = logging.getLogger("rng_bot")
ADMIN_ID = 1119820359500304396  # ID tối cao của cậu

# Link ảnh nền mặc định khi người dùng chưa cài (Giao diện thành phố đêm sang trọng)
DEFAULT_BANNER = "https://images.unsplash.com/photo-1519501025264-65ba15a82390?q=80&w=1000&auto=format&fit=crop"


# ==========================================
# GIAO DIỆN NÚT BẤM CẦU HÔN HOÀNG GIA
# ==========================================
class MarriageProposalView(discord.ui.View):
    def __init__(self, cog, proposer: discord.Member, target: discord.Member):
        super().__init__(timeout=60)
        self.cog = cog
        self.proposer = proposer
        self.target = target

    @discord.ui.button(label="💍 Đồng Ý", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("❌ Đây không phải lời cầu hôn dành cho cậu!", ephemeral=True)
        
        now = datetime.utcnow().isoformat()
        async with await self.cog.bot.db_manager.connect() as conn:
            await conn.execute("UPDATE royal_profiles SET spouse_id = ?, marriage_date = ? WHERE user_id = ?", (self.target.id, now, self.proposer.id))
            await conn.execute("UPDATE royal_profiles SET spouse_id = ?, marriage_date = ? WHERE user_id = ?", (self.proposer.id, now, self.target.id))
            await conn.commit()
            
        self.stop()
        await interaction.response.edit_message(content=f"💖 Chúc mừng {self.proposer.mention} và {self.target.mention} đã chính thức kết hôn! Tri kỷ trọn đời! 💍", view=None)

    @discord.ui.button(label="💔 Từ Chối", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("❌ Thư từ chối này không thuộc về cậu!", ephemeral=True)
        self.stop()
        await interaction.response.edit_message(content=f"💔 {self.target.mention} đã từ chối lời cầu hôn.", view=None)


# ==========================================
# GIAO DIỆN NÚT BẤM BÌNH CHỌN / KHẢO SÁT
# ==========================================
class PollView(discord.ui.View):
    def __init__(self, question: str, opt1: str, opt2: str):
        super().__init__(timeout=300)
        self.question = question
        self.opt1 = opt1
        self.opt2 = opt2
        self.votes1 = set()
        self.votes2 = set()
        self.message = None

    def make_embed(self):
        total = len(self.votes1) + len(self.votes2)
        p1 = (len(self.votes1) / total * 100) if total > 0 else 0
        p2 = (len(self.votes2) / total * 100) if total > 0 else 0
        
        bar1 = "🟩" * int(p1/10) + "⬛" * (10 - int(p1/10))
        bar2 = "🟦" * int(p2/10) + "⬛" * (10 - int(p2/10))
        
        embed = discord.Embed(title=f"📊 CUỘC KHẢO SÁT CƯ DÂN", color=discord.Color.blue())
        embed.description = (
            f"### 📋 Câu hỏi: {self.question}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 **{self.opt1}:** {len(self.votes1)} phiếu ({p1:.1f}%)\n"
            f"> {bar1}\n\n"
            f"🔸 **{self.opt2}:** {len(self.votes2)} phiếu ({p2:.1f}%)\n"
            f"> {bar2}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 *Tổng số người đã tham gia bình chọn: {total}*"
        )
        embed.set_footer(text="Hệ thống biểu quyết tự động Royal City 🌃")
        return embed

    @discord.ui.button(label="Lựa chọn 1", style=discord.ButtonStyle.success, custom_id="vote_1")
    async def vote_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.votes2: self.votes2.remove(uid)
        self.votes1.add(uid)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="Lựa chọn 2", style=discord.ButtonStyle.primary, custom_id="vote_2")
    async def vote_two(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.votes1: self.votes1.remove(uid)
        self.votes2.add(uid)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            embed = self.make_embed()
            embed.title = "📊 KHẢO SÁT (ĐÃ KẾT THÚC THỜI GIAN)"
            await self.message.edit(embed=embed, view=self)
        except Exception: pass


class ServerProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.ensure_table())

    def cog_unload(self):
        self.check_unbans.cancel()
        self.check_reminders.cancel()

    async def ensure_table(self):
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS royal_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    bio TEXT DEFAULT 'Chưa có tiểu sử cư dân.',
                    gender TEXT DEFAULT 'Bí mật 🤫',
                    birthday TEXT DEFAULT 'Chưa cập nhật 📅',
                    location TEXT DEFAULT 'Trái Đất 🌍',
                    bg_url TEXT DEFAULT NULL,
                    updated_at TEXT
                )
            """)
            await conn.execute("CREATE TABLE IF NOT EXISTS royal_bans (user_id INTEGER PRIMARY KEY, unban_time TEXT)")
            await conn.execute("CREATE TABLE IF NOT EXISTS royal_afk (user_id INTEGER PRIMARY KEY, reason TEXT, time TEXT)")
            await conn.execute("CREATE TABLE IF NOT EXISTS royal_reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, channel_id INTEGER, remind_time TEXT, content TEXT)")
            
            try: await conn.execute("ALTER TABLE royal_profiles ADD COLUMN spouse_id INTEGER DEFAULT NULL")
            except: pass
            try: await conn.execute("ALTER TABLE royal_profiles ADD COLUMN marriage_date TEXT DEFAULT NULL")
            except: pass
            await conn.commit()
        
        if not self.check_unbans.is_running(): self.check_unbans.start()
        if not self.check_reminders.is_running(): self.check_reminders.start()

    @tasks.loop(minutes=1)
    async def check_unbans(self):
        now = datetime.utcnow().isoformat()
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT user_id FROM royal_bans WHERE unban_time <= ?", (now,)) as cursor:
                expired_bans = await cursor.fetchall()
            for row in expired_bans:
                uid = row[0]
                await conn.execute("DELETE FROM royal_bans WHERE user_id = ?", (uid,))
                await conn.commit()
                for guild in self.bot.guilds:
                    try: await guild.unban(discord.Object(id=uid), reason="Hết thời hạn trục xuất tự động.")
                    except Exception: pass

    @tasks.loop(seconds=5)
    async def check_reminders(self):
        now = datetime.utcnow().isoformat()
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT id, user_id, channel_id, content FROM royal_reminders WHERE remind_time <= ?", (now,)) as cursor:
                rows = await cursor.fetchall()
            for row in rows:
                r_id, u_id, c_id, content = row
                await conn.execute("DELETE FROM royal_reminders WHERE id = ?", (r_id,))
                await conn.commit()
                channel = self.bot.get_channel(c_id)
                if channel:
                    try:
                        embed = discord.Embed(title="🔔 CHUÔNG BÁO NHẮC NHỞ", description=f"Chào {f'<@{u_id}>'}, thời gian hẹn giờ của cậu đã đến!\n\n> 📋 **Nội dung nhắc việc:** {content}", color=discord.Color.gold())
                        await channel.send(content=f"<@{u_id}>", embed=embed)
                    except Exception: pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        content = message.content.strip()

        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT reason FROM royal_afk WHERE user_id = ?", (message.author.id,)) as cursor:
                is_afk = await cursor.fetchone()
            if is_afk:
                await conn.execute("DELETE FROM royal_afk WHERE user_id = ?", (message.author.id,))
                await conn.commit()
                welcome_embed = discord.Embed(description=f"🎉 Chào mừng {message.author.mention} đã quay trở lại chat! Trạng thái treo máy (AFK) của cậu đã được gỡ bỏ tự động.", color=discord.Color.green())
                await message.channel.send(embed=welcome_embed)

        if message.mentions:
            async with await self.bot.db_manager.connect() as conn:
                for target in message.mentions:
                    if target.bot or target.id == message.author.id: continue
                    async with conn.execute("SELECT reason, time FROM royal_afk WHERE user_id = ?", (target.id,)) as cursor:
                        afk_data = await cursor.fetchone()
                    if afk_data:
                        reason, start_time = afk_data
                        warn_embed = discord.Embed(
                            title="💤 CƯ DÂN ĐANG TREO MÁY",
                            description=f"Thành viên {target.mention} hiện đang bận và không có mặt tại bàn phím.\n\n"
                                        f"⏱️ **Bắt đầu từ:** `{start_time}`\n"
                                        f"📝 **Lý do bận:** {reason}",
                            color=discord.Color.orange()
                        )
                        await message.channel.send(embed=warn_embed)

        if content.startswith("!so"):
            search = content[4:].strip() if content.startswith("!so ") else (None if content == "!so" else content[3:].strip())
            await self.execute_hoso_view(message, search)

    async def execute_hoso_view(self, message: discord.Message, search: str = None):
        guild = message.guild
        target_user = None
        profile_id = None
        
        if not search: 
            target_user = message.author
        else:
            clean_search = search.replace("#", "")
            if clean_search.isdigit(): 
                profile_id = int(clean_search)
            else:
                if search.startswith("<@") and search.endswith(">"):
                    uid_str = "".join(c for c in search if c.isdigit())
                    if uid_str: 
                        target_user = guild.get_member(int(uid_str))
                if not target_user: 
                    target_user = discord.utils.get(guild.members, name=search) or discord.utils.get(guild.members, display_name=search)
                if not target_user: 
                    return await message.channel.send("❌ Không tìm thấy cư dân tại Royal City!")

        try:
            async with await self.bot.db_manager.connect() as conn:
                if target_user:
                    query = "SELECT id, bio, gender, birthday, location, bg_url, user_id, spouse_id FROM royal_profiles WHERE user_id = ?"
                    param = (target_user.id,)
                else:
                    query = "SELECT id, bio, gender, birthday, location, bg_url, user_id, spouse_id FROM royal_profiles WHERE id = ?"
                    param = (profile_id,)
                async with conn.execute(query, param) as cursor: 
                    row = await cursor.fetchone()

            if not row:
                if target_user:
                    if target_user == message.author: 
                        await message.channel.send("❌ Cậu chưa được cấp số hồ sơ! Liên hệ Admin để phê duyệt.")
                    else: 
                        await message.channel.send("❌ Thành viên này chưa được đăng ký sổ cư dân!")
                else: 
                    display_id = f"#{profile_id:03d}" if profile_id is not None else search
                    await message.channel.send(f"❌ Mã số hồ sơ `{display_id}` chưa tồn tại!")
                return

            p_id, bio, gender, birthday, location, bg_url, stored_user_id, spouse_id = row
            
            try:
                display_user = guild.get_member(stored_user_id) or await self.bot.fetch_user(stored_user_id)
            except Exception:
                display_user = None

            embed = discord.Embed(color=discord.Color.from_rgb(43, 45, 49))
            embed.set_author(name="R O Y A L   C I T Y   I D E N T I T Y   C A R D", icon_url=guild.icon.url if guild.icon else None)
            
            user_mention = display_user.mention if display_user else f"<@{stored_user_id}>"
            spouse_text = f"<@{spouse_id}>" if spouse_id else "`Độc thân 💔`"
            
            embed.description = (
                f"## ⚜️ SỐ HỒ SƠ: `#{p_id:03d}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"> 👤 **Chủ hộ:** {user_mention}\n"
                f"> 💍 **Tri kỷ:** {spouse_text}\n"
                f"> ⚧️ **Giới tính:** `{gender}`\n"
                f"> 🎂 **Sinh nhật:** `{birthday}`\n"
                f"> 📍 **Sinh sống:** `{location}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💬 **TIỂU SỬ CƯ DÂN:**\n*{bio}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            if display_user:
                embed.set_thumbnail(url=display_user.display_avatar.url)

            # Validate banner URL, fallback to default nếu URL lỗi
            final_banner = DEFAULT_BANNER
            if bg_url and bg_url.startswith(("http://", "https://")):
                final_banner = bg_url
            try:
                embed.set_image(url=final_banner)
            except Exception:
                embed.set_image(url=DEFAULT_BANNER)
            embed.set_footer(text="Cập nhật diện mạo thẻ bằng lệnh: /sua_hoso 🌃")
            await message.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Lỗi nghiêm trọng khi kết xuất hồ sơ: {e}")
            await message.channel.send("❌ Hệ thống gặp sự cố vật lý khi đang tải thông tin thẻ cư dân này!")


    # ==========================================
    # CÁC LỆNH TIỆN ÍCH CƯ DÂN
    # ==========================================
    @app_commands.command(name="afk", description="Thiết lập trạng thái treo máy bận rộn khi rời bàn phím")
    @app_commands.describe(ly_do="Điền lý do cậu treo máy (Ví dụ: Học bài, đi ngủ, đi tắm...)")
    async def set_afk(self, interaction: discord.Interaction, ly_do: str = "Treo máy không lý do."):
        await interaction.response.defer(ephemeral=True)
        time_now_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("INSERT OR REPLACE INTO royal_afk (user_id, reason, time) VALUES (?, ?, ?)", (interaction.user.id, ly_do, time_now_str))
            await conn.commit()
            
        public_embed = discord.Embed(description=f"💤 Cư dân {interaction.user.mention} đã bật chế độ treo máy bận rộn.\n> **Lý do:** {ly_do}", color=discord.Color.orange())
        await interaction.channel.send(embed=public_embed)
        await interaction.followup.send("✅ Đã kích hoạt trạng thái AFK của cậu thành công.", ephemeral=True)

    @app_commands.command(name="nhac_nho", description="Thiết lập bộ chuông báo hẹn giờ nhắc việc tự động")
    @app_commands.describe(thoi_gian="Nhập định dạng thời gian (Ví dụ: 30s, 15m, 2h, 1d)", noi_dung="Nội dung cần nhắc nhở")
    async def set_reminder(self, interaction: discord.Interaction, thoi_gian: str, noi_dung: str):
        await interaction.response.defer(ephemeral=True)
        
        def parse_duration(t_str):
            try:
                amt = int(t_str[:-1])
                unit = t_str[-1].lower()
                if unit == 's': return amt
                if unit == 'm': return amt * 60
                if unit == 'h': return amt * 3600
                if unit == 'd': return amt * 86400
            except Exception: pass
            return None

        seconds = parse_duration(thoi_gian.strip())
        if seconds is None or seconds <= 0:
            return await interaction.followup.send("❌ Định dạng thời gian sai rồi! Cậu vui lòng nhập kiểu: `30s` (giây), `10m` (phút), `2h` (giờ), `1d` (ngày).", ephemeral=True)

        remind_at = (datetime.utcnow() + timedelta(seconds=seconds)).isoformat()
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("INSERT INTO royal_reminders (user_id, channel_id, remind_time, content) VALUES (?, ?, ?, ?)", (interaction.user.id, interaction.channel.id, remind_at, noi_dung))
            await conn.commit()
            
        await interaction.followup.send(f"🔔 **Thiết lập chuông thành công!** Tớ sẽ ping nhắc nhở cậu sau **{thoi_gian}** nữa với nội dung: *\"{noi_dung}\"*.", ephemeral=True)

    @app_commands.command(name="poll", description="Khởi tạo một cuộc khảo sát lấy ý kiến cư dân bằng nút bấm chuyên nghiệp")
    @app_commands.describe(cau_hoi="Nội dung vấn đề cần khảo sát", lua_chon_1="Tiêu đề phương án thứ nhất", lua_chon_2="Tiêu đề phương án thứ hai")
    async def create_poll(self, interaction: discord.Interaction, cau_hoi: str, lua_chon_1: str, lua_chon_2: str):
        view = PollView(cau_hoi, lua_chon_1, lua_chon_2)
        await interaction.response.send_message(embed=view.make_embed(), view=view)
        view.message = await interaction.original_response()

    @app_commands.command(name="qrcode", description="Biến đường link hoặc văn bản thành mã QR Code định dạng ảnh quét siêu tốc")
    @app_commands.describe(link_hoac_van_ban="Dán đường link URL hoặc đoạn văn bản cần tạo mã QR")
    async def generate_qrcode(self, interaction: discord.Interaction, link_hoac_van_ban: str):
        await interaction.response.defer()
        encoded_data = urllib.parse.quote(link_hoac_van_ban.strip())
        api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_data}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=10) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ Hệ thống máy chủ tạo mã QR ngoại vi đang bận, cậu thử lại sau nhé!")
                    img_bytes = await resp.read()
            
            with io.BytesIO(img_bytes) as img_bin:
                img_bin.seek(0)
                qr_file = discord.File(fp=img_bin, filename="royal_qrcode.png")
                
                embed = discord.Embed(title="📲 MÁY TẠO MÃ QR CODE THÀNH CÔNG", description=f"Mã QR định danh của cậu đã sẵn sàng!\n\n> 📥 **Nội dung gốc:**\n`{link_hoac_van_ban}`", color=discord.Color.blue())
                embed.set_image(url="attachment://royal_qrcode.png")
                embed.set_footer(text="Quét mã bằng camera điện thoại để truy cập nhanh 🌃")
                
                await interaction.followup.send(embed=embed, file=qr_file)
        except Exception as e:
            logger.error(f"Lỗi tạo mã QR: {e}")
            await interaction.followup.send("❌ Gặp sự cố kết nối trong lúc kết xuất ảnh QR Code!")

    # ==========================================
    # CÁC LỆNH ĐIỀU HÀNH BAN QUẢN TRỊ (ADMIN)
    # ==========================================
    @app_commands.command(name="ban", description="Trục xuất thành viên phá hoại kèm tùy chỉnh thời gian và xóa tin nhắn (Chỉ dành cho Admin)")
    @app_commands.choices(xoa_tin_nhan=[
        app_commands.Choice(name="Không xóa tin nhắn nào", value=0), 
        app_commands.Choice(name="Xóa 5 tin nhắn gần nhất", value=5), 
        app_commands.Choice(name="Xóa 10 tin nhắn gần nhất", value=10), 
        app_commands.Choice(name="Xóa 15 tin nhắn gần nhất", value=15), 
        app_commands.Choice(name="Xóa 30 tin nhắn gần nhất", value=30), 
        app_commands.Choice(name="Xóa 50 tin nhắn gần nhất", value=50)
    ])
    @app_commands.describe(user="Chọn thành viên cần ban", thoi_gian_phut="Số phút cần ban (Điền 0 để ban Vĩnh Viễn)", xoa_tin_nhan="Chọn số tin nhắn chat cần dọn", ly_do="Lý do xử phạt")
    async def ban_user(self, interaction: discord.Interaction, user: discord.Member, thoi_gian_phut: int, xoa_tin_nhan: app_commands.Choice[int], ly_do: str = "Không có lý do rõ ràng."):
        if interaction.user.id != ADMIN_ID: return await interaction.response.send_message("❌ Cậu không có quyền tối cao!", ephemeral=True)
        if user.id == interaction.user.id: return await interaction.response.send_message("❌ Không thể tự ban chính mình!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        num_to_delete = xoa_tin_nhan.value
        if num_to_delete > 0:
            try:
                deleted_count = 0
                async for msg in interaction.channel.history(limit=300):
                    if msg.author.id == user.id:
                        await msg.delete()
                        deleted_count += 1
                        if deleted_count >= num_to_delete: break
            except Exception: pass

        ban_reason = f"Trục xuất bởi Admin tối cao. Lý do: {ly_do}"
        try: await guild.ban(user, reason=ban_reason, delete_message_seconds=0)
        except discord.Forbidden: return await interaction.followup.send("❌ Bot không đủ quyền ban người này!", ephemeral=True)

        if thoi_gian_phut > 0:
            unban_date = (datetime.utcnow() + timedelta(minutes=thoi_gian_phut)).isoformat()
            async with await self.bot.db_manager.connect() as conn:
                await conn.execute("INSERT OR REPLACE INTO royal_bans (user_id, unban_time) VALUES (?, ?)", (user.id, unban_date))
                await conn.commit()
            thoi_gian_text = f"{thoi_gian_phut} Phút"
        else: thoi_gian_text = "Vĩnh Viễn 🚫"

        announce_embed = discord.Embed(title="⚡ LỆNH TRỤC XUẤT TỐI CAO", description=f"🚫 Cư dân {user.mention} đã bị loại khỏi vương quốc **Royal City**.\n\n⏳ **Thời hạn:** `{thoi_gian_text}`\n💬 **Lý do:** {ly_do}", color=discord.Color.red())
        announce_embed.set_footer(text="Thi hành bởi Ban Quản Trị Tối Cao 🌃")
        await interaction.channel.send(embed=announce_embed)
        await interaction.followup.send(f"✅ Đã ban thành công thành viên {user.name}.", ephemeral=True)

    @app_commands.command(name="unban", description="Gỡ lệnh cấm trục xuất cho cư dân cũ (Chỉ dành cho Admin tối cao)")
    @app_commands.describe(user_id="Nhập chính xác dãy số ID Discord của người cần gỡ ban")
    async def unban_user(self, interaction: discord.Interaction, user_id: str):
        if interaction.user.id != ADMIN_ID: return await interaction.response.send_message("❌ Bạn không có quyền hành này!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        try: uid = int(user_id.strip())
        except ValueError: return await interaction.followup.send("❌ Đầu vào chuỗi ID không hợp lệ!", ephemeral=True)

        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("DELETE FROM royal_bans WHERE user_id = ?", (uid,))
            await conn.commit()

        try:
            try:
                user_obj = await self.bot.fetch_user(uid)
                user_mention = user_obj.mention
                user_name = f"{user_obj.name}"
            except Exception:
                user_mention = f"<@{uid}>"
                user_name = f"ID: {uid}"
            await guild.unban(discord.Object(id=uid), reason="Ân xá bởi Admin.")
        except discord.NotFound: return await interaction.followup.send("❌ Người này không có trong danh sách đen!", ephemeral=True)

        unban_embed = discord.Embed(title="✨ LỆNH ÂN XÁ TỐI CAO", description=f"🎉 Cư dân {user_mention} đã chính thức được xóa án cấm ban tại vương quốc **Royal City**.", color=discord.Color.green())
        await interaction.channel.send(embed=unban_embed)
        await interaction.followup.send(f"✅ Gỡ ban thành công cho {user_name}.", ephemeral=True)

    # ==========================================
    # LỆNH MỚI: HOÁN ĐỔI SỐ HỒ SƠ 
    # ==========================================
    @app_commands.command(name="doi_so_hoso", description="Hoán đổi số thứ tự hồ sơ giữa hai cư dân (Chỉ dành cho Admin tối cao)")
    @app_commands.describe(nguoi_a="Chọn cư dân thứ nhất", nguoi_b="Chọn cư dân thứ hai")
    async def swap_profile_id(self, interaction: discord.Interaction, nguoi_a: discord.Member, nguoi_b: discord.Member):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Cậu không có quyền tối cao để thực hiện thao tác này!", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        async with await self.bot.db_manager.connect() as conn:
            # Truy xuất ID hồ sơ hiện tại của 2 người
            async with conn.execute("SELECT id FROM royal_profiles WHERE user_id = ?", (nguoi_a.id,)) as cursor_a:
                row_a = await cursor_a.fetchone()
            async with conn.execute("SELECT id FROM royal_profiles WHERE user_id = ?", (nguoi_b.id,)) as cursor_b:
                row_b = await cursor_b.fetchone()
                
            if not row_a:
                return await interaction.followup.send(f"❌ {nguoi_a.mention} chưa có hồ sơ định danh trong hệ thống!")
            if not row_b:
                return await interaction.followup.send(f"❌ {nguoi_b.mention} chưa có hồ sơ định danh trong hệ thống!")
                
            id_a = row_a[0]
            id_b = row_b[0]
            
            if id_a == id_b:
                return await interaction.followup.send("❌ Hai người này là một mà, làm sao tráo đổi được?")
                
            # Đảo mã an toàn qua biến tạm (-1) để không vi phạm quy tắc PRIMARY KEY UNIQUE của CSDL
            await conn.execute("UPDATE royal_profiles SET id = -1 WHERE user_id = ?", (nguoi_a.id,))
            await conn.execute("UPDATE royal_profiles SET id = ? WHERE user_id = ?", (id_a, nguoi_b.id,))
            await conn.execute("UPDATE royal_profiles SET id = ? WHERE user_id = ?", (id_b, nguoi_a.id,))
            await conn.commit()
            
        embed = discord.Embed(
            title="🔄 HOÁN ĐỔI SỐ HỒ SƠ THÀNH CÔNG",
            description=f"Hai cư dân đã được hoán đổi danh tính:\n\n"
                        f"👤 {nguoi_a.mention}: `#{id_a:03d}` ➡️ **`#{id_b:03d}`**\n"
                        f"👤 {nguoi_b.mention}: `#{id_b:03d}` ➡️ **`#{id_a:03d}`**",
            color=discord.Color.purple()
        )
        await interaction.followup.send(embed=embed)

    # ==========================================
    # LỆNH MỚI: XÓA TRẮNG DỮ LIỆU HỒ SƠ 
    # ==========================================
    @app_commands.command(name="reset_hoso", description="Xóa trắng hoàn toàn hồ sơ của một người để làm lại từ đầu (Chỉ dành cho Admin tối cao)")
    @app_commands.describe(user="Chọn cư dân cần xóa dữ liệu thẻ")
    async def reset_profile(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Cậu không có quyền tối cao để thực hiện thao tác này!", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        
        async with await self.bot.db_manager.connect() as conn:
            # Check xem có dữ liệu không và lấy tình trạng hôn nhân (nếu có)
            async with conn.execute("SELECT id, spouse_id FROM royal_profiles WHERE user_id = ?", (user.id,)) as cursor:
                row = await cursor.fetchone()
                
            if not row:
                return await interaction.followup.send(f"❌ {user.mention} hiện tại không có hồ sơ nào trong hệ thống, không cần reset!")
                
            spouse_id = row[1]
            
            # Quét sạch hồ sơ của người bị chỉ định
            await conn.execute("DELETE FROM royal_profiles WHERE user_id = ?", (user.id,))
            
            # Tự động cắt đứt mối quan hệ để chống lỗi hệ thống cho người còn lại
            if spouse_id:
                await conn.execute("UPDATE royal_profiles SET spouse_id = NULL, marriage_date = NULL WHERE user_id = ?", (spouse_id,))
                
            await conn.commit()
            
        await interaction.followup.send(f"✅ Đã xóa toàn bộ dữ liệu hồ sơ của {user.mention}.\n> 💡 *Mẹo: Bây giờ cậu có thể dùng lệnh `/cap_hoso` để cấp cho người này một số định danh hoàn toàn mới nhé!*")


    # ==========================================
    # LỆNH CẤP/SỬA/TƯƠNG TÁC HỒ SƠ 
    # ==========================================
    @app_commands.command(name="marry", description="Cầu hôn một cư dân khác tại Royal City để kết đôi tri kỷ")
    async def marry(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        if user == interaction.user or user.bot: return await interaction.followup.send("❌ Đối tượng kết đôi không hợp lệ!", ephemeral=True)
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT spouse_id FROM royal_profiles WHERE user_id = ?", (interaction.user.id,)) as c1: p1 = await c1.fetchone()
            async with conn.execute("SELECT spouse_id FROM royal_profiles WHERE user_id = ?", (user.id,)) as c2: p2 = await c2.fetchone()
        if not p1: return await interaction.followup.send("❌ Cậu phải đăng ký sổ cư dân trước!", ephemeral=True)
        if not p2: return await interaction.followup.send("❌ Đối phương chưa có hồ sơ cư dân!", ephemeral=True)
        if p1[0] or p2[0]: return await interaction.followup.send("❌ Một trong hai đã kết hôn!", ephemeral=True)

        await interaction.followup.send(content=f"{user.mention} ơi! 🌹 **LỜI CẦU HÔN HOÀNG GIA** 🌹\n💖 {interaction.user.mention} đang cầu hôn cậu. Cậu có đồng ý kết đôi không?", view=MarriageProposalView(self, interaction.user, user))

    @app_commands.command(name="ly_hon", description="Xóa bỏ trạng thái kết đôi với tri kỷ hiện tại")
    async def divorce(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT spouse_id FROM royal_profiles WHERE user_id = ?", (interaction.user.id,)) as cursor: row = await cursor.fetchone()
            if not row or not row[0]: return await interaction.followup.send("❌ Bạn đang độc thân!", ephemeral=True)
            spouse_id = row[0]
            await conn.execute("UPDATE royal_profiles SET spouse_id = NULL, marriage_date = NULL WHERE user_id = ?", (interaction.user.id,))
            await conn.execute("UPDATE royal_profiles SET spouse_id = NULL, marriage_date = NULL WHERE user_id = ?", (spouse_id,))
            await conn.commit()
        await interaction.channel.send(f"💔 Cư dân {interaction.user.mention} và <@{spouse_id}> đã ly hôn.")
        await interaction.followup.send("✅ Đã xử lý thủ tục ly hôn thành công.", ephemeral=True)

    @app_commands.command(name="cap_hoso", description="Cấp số hiệu hồ sơ cư dân cho một thành viên (Chỉ Admin)")
    async def cap_hoso(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id != ADMIN_ID: return await interaction.followup.send("❌ Bạn không có quyền hạn!", ephemeral=True)
        if user.bot: return await interaction.followup.send("❌ Không cấp thẻ cho Bot!", ephemeral=True)
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT id FROM royal_profiles WHERE user_id = ?", (user.id,)) as cursor: exist = await cursor.fetchone()
            if exist: return await interaction.followup.send("⚠️ Họ đã có hồ sơ rồi! Cậu cần dùng lệnh `/reset_hoso` trước nếu muốn cấp lại.", ephemeral=True)
            now = datetime.utcnow().isoformat()
            cursor = await conn.execute("INSERT INTO royal_profiles (user_id, updated_at) VALUES (?, ?)", (user.id, now))
            await conn.commit()
            new_id = cursor.lastrowid
        embed = discord.Embed(title="🎉 CHÚC MỪNG CƯ DÂN MỚI!", description=f"Thành viên {user.mention} đã được cấp mã số định danh: **`#{new_id:03d}`**", color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Cấp thành công.", ephemeral=True)

    @app_commands.command(name="sua_hoso", description="Chỉnh sửa thông tin thẻ cư dân của bạn")
    async def hoso_edit(self, interaction: discord.Interaction, tieu_su: str = None, gioi_tinh: str = None, ngay_sinh: str = None, den_tu: str = None, tai_anh_tu_may: discord.Attachment = None, link_anh_ngoai: str = None):
        await interaction.response.defer(ephemeral=True)
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT bio, gender, birthday, location, bg_url FROM royal_profiles WHERE user_id = ?", (interaction.user.id,)) as cursor: row = await cursor.fetchone()
        if not row: return await interaction.followup.send("❌ Cậu chưa có tên trong sổ cư dân!", ephemeral=True)
        current_bio, current_gender, current_birthday, current_location, current_bg_url = row
        chosen_bg_url = current_bg_url
        if tai_anh_tu_may is not None:
            if tai_anh_tu_may.content_type and "image" in tai_anh_tu_may.content_type: chosen_bg_url = tai_anh_tu_may.url
            else: return await interaction.followup.send("❌ Định dạng file không hợp lệ!", ephemeral=True)
        elif link_anh_ngoai is not None: chosen_bg_url = link_anh_ngoai
        new_bio = tieu_su if tieu_su is not None else current_bio
        new_gender = gioi_tinh if gioi_tinh is not None else current_gender
        new_birthday = ngay_sinh if ngay_sinh is not None else current_birthday
        new_location = den_tu if den_tu is not None else current_location
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("UPDATE royal_profiles SET bio = ?, gender = ?, birthday = ?, location = ?, bg_url = ?, updated_at = ? WHERE user_id = ?", (new_bio, new_gender, new_birthday, new_location, chosen_bg_url, datetime.utcnow().isoformat(), interaction.user.id))
            await conn.commit()
        await interaction.followup.send("🎉 **Cập nhật hồ sơ thành công!**", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ServerProfileCog(bot))