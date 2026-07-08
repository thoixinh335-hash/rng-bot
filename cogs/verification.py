import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import logging

logger = logging.getLogger("rng_bot")

ADMIN_ID = 1119820359500304396
VERIFIED_ROLE_ID = 1524357636286578718
DEFAULT_BANNER = "https://images.unsplash.com/photo-1519501025264-65ba15a82390?q=80&w=1000&auto=format&fit=crop"

QUIZ_QUESTIONS = [
    {
        "question": "Hành vi nào dưới đây bị cấm tuyệt đối tại các kênh chat của Royal City?",
        "options": [
            "A. Gửi ảnh meme hài hước",
            "B. Tag Admin để báo cáo lỗi hệ thống",
            "C. Spam từ ngữ độc hại, quảng cáo hoặc xúc phạm người khác",
            "D. Chúc mọi người trong server buổi tối tốt lành"
        ],
        "correct_index": 2
    },
    {
        "question": "Hãy tính nhẩm nhanh để chứng minh cậu không phải là Bot tự động: 5 + 3 bằng bao nhiêu?",
        "options": [
            "A. Bằng 2",
            "B. Bằng 7",
            "C. Bằng 8",
            "D. Bằng 15"
        ],
        "correct_index": 2
    },
    {
        "question": "Nếu bạn vô server để partner thì hãy sài lệnh /partner và chọn bot của server, bot sẽ tự động làm hết. Nếu không phải vào để partner thì hãy bỏ qua đoạn này nha",
        "options": [
            "A. Ok",
            "B. Không",
            "C. Không Đồng Ý"
        ],
        "correct_index": 0
    }
]

class VerificationQuizView(discord.ui.View):
    def __init__(self, member: discord.Member, guild: discord.Guild):
        super().__init__(timeout=600)
        self.member = member
        self.guild = guild
        self.current_question_idx = 0
        self.score = 0
        self.update_dropdown_menu()

    def update_dropdown_menu(self):
        self.clear_items()
        if self.current_question_idx >= len(QUIZ_QUESTIONS):
            return
        q_data = QUIZ_QUESTIONS[self.current_question_idx]
        select_options = []
        for i, opt in enumerate(q_data["options"]):
            select_options.append(discord.SelectOption(label=opt[:100], value=str(i)))
        select_menu = discord.ui.Select(
            placeholder="Chọn đáp án phù hợp bên dưới...",
            options=select_options,
            custom_id="verification_dropdown_select"
        )
        select_menu.callback = self.dropdown_callback
        self.add_item(select_menu)

    async def dropdown_callback(self, interaction: discord.Interaction):
        chosen_val = int(interaction.data['values'][0])
        correct_idx = QUIZ_QUESTIONS[self.current_question_idx]["correct_index"]
        if chosen_val == correct_idx:
            self.score += 1
        self.current_question_idx += 1
        self.update_dropdown_menu()
        embed = self.make_question_embed()
        if embed:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(content="🔄 Đang xử lý...", embed=None, view=None)
            await self.apply_verification_result(interaction)

    def make_question_embed(self):
        if self.current_question_idx >= len(QUIZ_QUESTIONS):
            return None
        q_data = QUIZ_QUESTIONS[self.current_question_idx]
        embed = discord.Embed(
            title="❓ Câu hỏi xác minh",
            description=f"### {q_data['question']}",
            color=discord.Color.from_rgb(88, 101, 242)
        )
        embed.set_footer(text=f"Tiến trình: {self.current_question_idx + 1}/{len(QUIZ_QUESTIONS)}")
        return embed

    async def apply_verification_result(self, interaction: discord.Interaction):
        total_q = len(QUIZ_QUESTIONS)
        if self.score == total_q:
            role = self.guild.get_role(VERIFIED_ROLE_ID)
            if role:
                try:
                    await self.member.add_roles(role, reason="Hoàn thành xuất sắc bài test đầu vào.")

                    # Tự động tạo hồ sơ cư dân
                    try:
                        async with await self.bot.db_manager.connect() as conn:
                            async with conn.execute("SELECT id FROM royal_profiles WHERE user_id = ?", (self.member.id,)) as cursor:
                                exists = await cursor.fetchone()
                            if not exists:
                                now = datetime.utcnow().isoformat()
                                cursor = await conn.execute(
                                    "INSERT INTO royal_profiles (user_id, updated_at) VALUES (?, ?)",
                                    (self.member.id, now)
                                )
                                await conn.commit()
                                new_id = cursor.lastrowid
                                logger.info(f"✅ Đã tự tạo hồ sơ #{new_id} cho {self.member.name}")
                    except Exception as e:
                        logger.error(f"Lỗi tạo hồ sơ: {e}")

                    success_embed = discord.Embed(
                        title="✨ Xác Minh Thành Công! ✨",
                        description=f"Đã hoàn thành xác minh **{self.score}/{total_q}** câu hỏi!\n"
                                    f"Vai trò **{role.name}** đã được kích hoạt.\n"
                                    f"Hồ sơ cư dân đã được tạo tự động!",
                        color=discord.Color.green()
                    )
                    await interaction.message.edit(content=None, embed=success_embed, view=None)
                except discord.Forbidden:
                    await interaction.message.edit(content="❌ Bot thiếu quyền cấp Role!", embed=None, view=None)
            else:
                await interaction.message.edit(content=f"❌ Không tìm thấy Role ID `{VERIFIED_ROLE_ID}`!", embed=None, view=None)
        else:
            fail_view = discord.ui.View(timeout=60)
            retry_btn = discord.ui.Button(label="🔄 Thử Làm Lại Bài Kiểm Tra", style=discord.ButtonStyle.danger)

            async def retry_callback(inter: discord.Interaction):
                new_quiz = VerificationQuizView(self.member, self.guild)
                await inter.response.send_message(embed=new_quiz.make_question_embed(), view=new_quiz)

            retry_btn.callback = retry_callback
            fail_view.add_item(retry_btn)

            fail_embed = discord.Embed(
                title="💔 Xác Minh Thất Bại",
                description=f"Rất tiếc! Cậu chỉ trả lời đúng **{self.score}/{total_q}** câu hỏi.\n\n"
                            f"⚠️ Yêu cầu đạt **tuyệt đối 100%** để thông quan.\n"
                            f"💡 Hãy nhấn nút bên dưới để làm lại bài test nhé!",
                color=discord.Color.red()
            )
            await interaction.message.edit(content=None, embed=fail_embed, view=fail_view)


class VerificationLandingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Bắt đầu xác minh", style=discord.ButtonStyle.success, custom_id="royal_city_gatekeeper_btn")
    async def start_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        quiz_view = VerificationQuizView(member, interaction.guild)
        first_embed = quiz_view.make_question_embed()

        welcome_dm_text = (
            f"🏰 **Chào mừng bạn đã đặt chân tới vương quốc ROYAL CITY!**\n\n"
            f"Để ngăn chặn tình trạng tài khoản Bot spam phá hoại, "
            f"hệ thống yêu cầu bạn hoàn thành một bài trắc nghiệm gồm **{len(QUIZ_QUESTIONS)} câu hỏi**.\n"
            f"Trả lời đúng toàn bộ câu hỏi, hệ thống sẽ cấp quyền cư dân và mở khóa toàn bộ kênh chat cho bạn!"
        )

        try:
            await member.send(content=welcome_dm_text)
            await member.send(embed=first_embed, view=quiz_view)
            await interaction.response.send_message("📬 Đã gửi trình xác minh về DMs!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                content="⚠️ Cậu đang tắt DM! Tớ sẽ cho cậu làm bài kiểm tra ngay tại đây.",
                embed=first_embed,
                view=quiz_view,
                ephemeral=True
            )

class VerificationSetupModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Cấu hình bảng Xác Minh Hoàng Gia")

        self.embed_title = discord.ui.TextInput(
            label="1. Tiêu đề bảng công khai (Title)",
            default="🧚‍♀️ Xác Minh Thành Viên 🧚‍♀️",
            placeholder="Nhập tiêu đề lớn của bảng...",
            max_length=256,
            required=True
        )
        self.embed_desc = discord.ui.TextInput(
            label="2. Hướng dẫn cư dân (Description)",
            style=discord.TextStyle.paragraph,
            default="✨ Chào mừng bạn đến với Royal City!\n\n📌 Nhấn nút bên dưới để bắt đầu xác minh tài khoản.\nBot sẽ gửi các câu hỏi lựa chọn vào tin nhắn riêng (DMs) của bạn.",
            placeholder="Nhập nội dung chữ hiển thị trên bảng...",
            max_length=1500,
            required=True
        )
        self.embed_footer = discord.ui.TextInput(
            label="3. Dòng chữ nhỏ dưới đáy (Footer)",
            default="Hệ thống bảo vệ biên giới tự động Royal City 🏙️",
            placeholder="Nhập nội dung chân trang...",
            max_length=256,
            required=False
        )
        self.embed_color = discord.ui.TextInput(
            label="4. Mã màu thanh Embed (Hex Code)",
            default="FFB6C1",
            placeholder="Ví dụ: FFB6C1 (Hồng), 5865F2 (Xanh), 2ECC71 (Lục)...",
            max_length=7,
            required=False
        )

        self.add_item(self.embed_title)
        self.add_item(self.embed_desc)
        self.add_item(self.embed_footer)
        self.add_item(self.embed_color)

    async def on_submit(self, interaction: discord.Interaction):
        color_hex = self.embed_color.value.strip().replace("#", "")
        try:
            color = discord.Color(int(color_hex, 16))
        except ValueError:
            color = discord.Color.from_rgb(255, 192, 203)
        embed = discord.Embed(
            title=self.embed_title.value,
            description=self.embed_desc.value,
            color=color
        )
        if self.embed_footer.value:
            embed.set_footer(text=self.embed_footer.value)
        landing_view = VerificationLandingView()
        await interaction.response.send_message("✅ Đã khởi tạo bảng xác minh thành công!", ephemeral=True)
        await interaction.channel.send(embed=embed, view=landing_view)


class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(VerificationLandingView())

    @app_commands.command(name="setup_verification", description="Khởi tạo bảng nút bấm xác minh tùy chỉnh nội dung bằng Form Popup (Chỉ dành cho Admin tối cao)")
    async def setup_verification(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Cậu không phải là Người cấp quyền tối cao để dùng lệnh này!", ephemeral=True)
        await interaction.response.send_modal(VerificationSetupModal())

async def setup(bot):
    await bot.add_cog(VerificationCog(bot))