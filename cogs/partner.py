import discord
from discord.ext import commands
import logging
import asyncio

logger = logging.getLogger("rng_bot")

# ==========================================
# CẤU HÌNH ROLE VÀ KÊNH
# ==========================================
# Chỉ 2 Role này mới có quyền bấm nút duyệt và đóng kênh
ADMIN_ROLE_IDS = [
    1503824832075268386,
    1503824851046236161
]

# ID Kênh sẽ tự động đăng bài giới thiệu của khách sau khi được duyệt
PARTNER_CHANNEL_ID = 1504447095216803841 

# ID Role Đối Tác sẽ tự động cấp sau khi được duyệt thành công
PARTNER_ROLE_ID = 1504447660130828399

# ==========================================
# 0. NÚT BẤM ĐÓNG KÊNH (BỀN VỮNG VĨNH VIỄN)
# ==========================================
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def check_admin(self, interaction: discord.Interaction) -> bool:
        user_roles = [role.id for role in interaction.user.roles]
        if any(role_id in user_roles for role_id in ADMIN_ROLE_IDS) or interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message("❌ Bạn không có quyền đóng kênh này!", ephemeral=True)
        return False

    @discord.ui.button(label="🗑️ Đóng Kênh", style=discord.ButtonStyle.danger, custom_id="ticket_close_final")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_admin(interaction): return
        
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await interaction.channel.send("🗑️ Hệ thống đang dọn dẹp... Kênh sẽ tự động xóa sau 5 giây nữa.")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except Exception as e:
            logger.error(f"Không thể xóa kênh ticket: {e}")

# ==========================================
# 1. NÚT BẤM XÉT DUYỆT (TỰ ĐỘNG CẤP ROLE ĐỐI TÁC)
# ==========================================
class TicketAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    async def check_admin(self, interaction: discord.Interaction) -> bool:
        user_roles = [role.id for role in interaction.user.roles]
        if any(role_id in user_roles for role_id in ADMIN_ROLE_IDS) or interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message("❌ Bạn không có quyền sử dụng nút này! Chỉ bộ phận xét duyệt mới được phép.", ephemeral=True)
        return False

    @discord.ui.button(label="✅ Đồng Ý", style=discord.ButtonStyle.success, custom_id="ticket_approve")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_admin(interaction): return
        
        message = interaction.message
        if not message.embeds:
            await interaction.response.send_message("❌ Hệ thống không tìm thấy nội dung đơn đăng ký gốc trong tin nhắn này!", ephemeral=True)
            return

        embed = message.embeds[0]
        applicant = message.mentions[0] if message.mentions else interaction.user
        intro_text = embed.fields[0].value if embed.fields else "Nội dung bài viết trống."

        # ==========================================
        # CHỨC NĂNG MỚI: TỰ ĐỘNG TÌM KIẾM VÀ CẤP ROLE ĐỐI TÁC
        # ==========================================
        member = interaction.guild.get_member(applicant.id)
        if not member:
            try:
                member = await interaction.guild.fetch_member(applicant.id)
            except:
                member = None

        role_notification = ""
        if member:
            partner_role = interaction.guild.get_role(PARTNER_ROLE_ID)
            if partner_role:
                try:
                    await member.add_roles(partner_role)
                    # Tạo dòng chữ thông báo nạp role thành công
                    role_notification = f" và tự động cấp danh hiệu <@&{PARTNER_ROLE_ID}> cho bạn"
                    logger.info(f"👑 Đã cấp role đối tác thành công cho thành viên: {member.display_name}")
                except discord.Forbidden:
                    role_notification = "\n⚠️ *Lưu ý: Bạn này chưa được cấp role do vai trò của Bot đang xếp DƯỚI role Đối Tác trong Cài đặt server!*"
                    logger.error(f"Thất bại khi cấp role: Bot thiếu quyền vị trí vai trò.")
                except Exception as e:
                    role_notification = f"\n⚠️ *Lưu ý: Hệ thống gặp lỗi khi cấp role: {e}*"
            else:
                role_notification = f"\n⚠️ *Lưu ý: Không tìm thấy Role có ID {PARTNER_ROLE_ID} trong danh sách máy chủ.*"

        royal_city_text = (
            "**ROYAL CITY**\n"
            "Sever :\n"
            "Hoà Đồng.\n"
            "Thân thiện.\n"
            "Nơi gắn kết , trò chuyện.\n"
            "No toxic.\n"
            "Chúng tớ sống về đêm.\n"
            " Cam kết hog bơ mem iu\n\n"
            "Yêu cầu :\n"
            "Chúng tớ không giới hạn độ tuổi - vì ai cũng xứng được iu mò.\n"
            "Chỉ cần bạn thân thiện , hoà đồng Royal City luôn chào đón.\n\n"
            "Lưu ý : Không được gửi chat 18+ , xúc phạm , lăng mạ một cá nhân hay tập thể , raid ,..\n"
            "NẾU BẠN CẦN TÌM MỘT SEVER CHỮA LÀNH, TRÒ CHUYỆN ROYAL CITY LUÔN ĐỢI BẠN\n\n"
            "Link Sever : https://discord.gg/aExr4RTjf\n\n"
            f"Đại Diện : {interaction.user.mention} @everyone\n"
            "( cảm ơn vì đã đọc đến đây, sorry4ping)"
        )

        # 1. Đăng bài của KHÁCH ra kênh Partner công khai
        partner_channel = interaction.guild.get_channel(PARTNER_CHANNEL_ID)
        if partner_channel:
            final_post = f"**🤝 ĐỐI TÁC MỚI:** {applicant.mention}\n\n**BÀI GIỚI THIỆU CỦA ĐỐI TÁC:**\n{intro_text}"
            await partner_channel.send(content=final_post, allowed_mentions=discord.AllowedMentions(everyone=True))
        else:
            await interaction.channel.send(f"⚠️ Lỗi cấu hình hệ thống: Không tìm thấy kênh <#{PARTNER_CHANNEL_ID}> để đăng bài.")

        # 2. Báo thành công vào Ticket chat riêng (Có kèm thông báo cấp role)
        await interaction.response.send_message(
            f"🎉 Tuyệt vời! Yêu cầu Partner của {applicant.mention} đã được **CHẤP THUẬN**{role_notification}.\n\n"
            f"✅ **Dưới đây là bài giới thiệu của Royal City, bạn hãy copy và đăng lên server của bạn nhé:**\n\n{royal_city_text}"
        )
        
        # Khóa nút duyệt
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # 3. Gửi nút đóng kênh dọn dẹp
        await interaction.channel.send(
            "🔒 **HOÀN TẤT THỦ TỤC**\nQuản trị viên vui lòng bấm nút bên dưới để đóng kênh sau khi trao đổi xong.", 
            view=CloseTicketView()
        )

    @discord.ui.button(label="❌ Từ Chối", style=discord.ButtonStyle.danger, custom_id="ticket_reject")
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_admin(interaction): return
        
        message = interaction.message
        applicant = message.mentions[0] if message.mentions else interaction.user
        
        await interaction.response.send_message(f"🛑 Rất tiếc {applicant.mention}, yêu cầu Partner của bạn đã bị **TỪ CHỐI** bởi {interaction.user.mention}.")
        
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await interaction.channel.send(
            "🔒 **HOÀN TẤT THỦ TỤC**\nQuản trị viên vui lòng bấm nút bên dưới để đóng kênh.", 
            view=CloseTicketView()
        )

# ==========================================
# 2. BẢNG FORM ĐIỀN THÔNG TIN (MODAL)
# ==========================================
class PartnerForm(discord.ui.Modal, title='Đăng Ký Chương Trình Partner'):
    server_intro = discord.ui.TextInput(
        label='Gửi bài giới thiệu kèm link server',
        style=discord.TextStyle.paragraph,
        placeholder='VD: Xin chào, server của mình là...\nLink: https://discord.gg/...',
        required=True,
        max_length=2000
    )

    member_count = discord.ui.TextInput(
        label='Số lượng thành viên hiện tại',
        style=discord.TextStyle.short,
        placeholder='VD: 200',
        required=True,
        max_length=20
    )

    agreement = discord.ui.TextInput(
        label='Đồng ý luật & hài lòng với server?',
        style=discord.TextStyle.paragraph, 
        placeholder='VD: Tôi đồng ý với luật partner và rất hài lòng với server...',
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        for role_id in ADMIN_ROLE_IDS:
            admin_role = guild.get_role(role_id)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = discord.utils.get(guild.categories, name="Partner Tickets")
        if not category:
            category = await guild.create_category("Partner Tickets")

        ticket_channel = await guild.create_text_channel(
            name=f"partner-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title="📋 ĐƠN ĐĂNG KÝ PARTNER MỚI",
            description=f"**Người yêu cầu:** {interaction.user.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="🔗 Bài giới thiệu & Link", value=self.server_intro.value[:1024], inline=False)
        embed.add_field(name="👥 Số thành viên", value=self.member_count.value, inline=False)
        embed.add_field(name="✅ Trả lời xác nhận", value=self.agreement.value[:1024], inline=False)
        
        ping_role = f"<@&{ADMIN_ROLE_IDS[0]}>" 
        
        await ticket_channel.send(
            content=f"Xin chào {interaction.user.mention}, bộ phận xét duyệt {ping_role} sẽ sớm có mặt để trao đổi với bạn!", 
            embed=embed, 
            view=TicketAdminView()
        )
        
        jump_view = discord.ui.View()
        jump_view.add_item(discord.ui.Button(
            label="Nhảy đến kênh Ticket của bạn", 
            style=discord.ButtonStyle.link, 
            url=f"https://discord.com/channels/{guild.id}/{ticket_channel.id}"
        ))

        await interaction.response.send_message(
            f"✅ **Tạo form thành công!** Vui lòng bấm vào nút bên dưới để chuyển sang kênh trao đổi.", 
            ephemeral=True,
            view=jump_view
        )

# ==========================================
# 3. NÚT BẤM BÊN NGOÀI (MỞ FORM)
# ==========================================
class PartnerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Mở Form Đăng Ký", style=discord.ButtonStyle.success, custom_id="btn_partner_apply")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PartnerForm())

# ==========================================
# 4. CHỨC NĂNG CHÍNH (COG)
# ==========================================
class PartnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(PartnerView())
        self.bot.add_view(TicketAdminView())
        self.bot.add_view(CloseTicketView())

    @commands.hybrid_command(name="partner", description="Xem hướng dẫn và đăng ký chương trình Partner")
    async def partner_command(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🤝 CHƯƠNG TRÌNH ĐỐI TÁC (PARTNER)",
            description="Hãy trở thành đối tác của hệ thống để nhận những đặc quyền độc quyền!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="📜 Điều kiện xét duyệt", 
            value="👉 Máy chủ có ít nhất **200 thành viên**.\n👉 Hoạt động tích cực, không vi phạm TOS Discord.\n👉 Có kênh dành riêng để sử dụng bot.", 
            inline=False
        )
        embed.add_field(
            name="🎁 Đặc quyền nhận được", 
            value="✨ Huy hiệu `<Partner>` vĩnh viễn trên Profile.\n✨ Giảm 50% thời gian hồi chiêu (Cooldown) mọi lệnh.\n✨ Ưu tiên hỗ trợ kỹ thuật trực tiếp.", 
            inline=False
        )
        embed.add_field(
            name="📝 Hướng dẫn", 
            value="Nhấn vào nút **Mở Form Đăng Ký** bên dưới, điền bài giới thiệu và một kênh Ticket riêng tư sẽ được tạo ra.", 
            inline=False
        )
        
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        await ctx.send(embed=embed, view=PartnerView())

# ==========================================
# 5. SETUP KẾT NỐI VÀO BOT
# ==========================================
async def setup(bot):
    await bot.add_cog(PartnerCog(bot))