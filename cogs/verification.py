import discord
from discord.ext import commands
from datetime import datetime
import logging

logger = logging.getLogger("rng_bot")

ADMIN_ID = 1119820359500304396
VERIFIED_ROLE_ID = 1524357636286578718
DEFAULT_BANNER = "https://images.unsplash.com/photo-1519501025264-65ba15a82390?q=80&w=1000&auto=format&fit=crop"

GENDER_OPTIONS = [
    {"label": "Nam 💙", "value": "nam", "gender": "Nam"},
    {"label": "Nữ 🩷", "value": "nu", "gender": "Nữ"},
    {"label": "Khác 💜", "value": "khac", "gender": "Bí mật 🤫"},
]

# Game + Role ID tương ứng — không dùng emoji trong Select để tránh lỗi Invalid emoji
GAME_OPTIONS = [
    {"label": "Liên Quân Mobile", "value": "lienquan", "role_id": 1503825048039981208},
    {"label": "Valorant", "value": "valorant", "role_id": 1503825041262116966},
    {"label": "Roblox", "value": "roblox", "role_id": 1503825045045252136},
    {"label": "Minecraft", "value": "minecraft", "role_id": 1503825052108587142},
    {"label": "TFT", "value": "tft", "role_id": 1503825055832870963},
    {"label": "Free Fire", "value": "freefire", "role_id": 1503825059460939877},
    {"label": "CS:GO / CS2", "value": "csgo", "role_id": 1503825062921240667},
]



class VerificationStepView(discord.ui.View):
    """Xác minh 2 bước: giới tính -> game"""
    def __init__(self, bot, member: discord.Member, guild: discord.Guild):
        super().__init__(timeout=300)
        self.bot = bot
        self.member = member
        self.guild = guild
        self.chosen_gender = None
        self.step = 1  # 1=giới tính, 2=game
        self._build_step1()

    def _build_step1(self):
        self.clear_items()
        options = [discord.SelectOption(label=g["label"], value=g["value"]) for g in GENDER_OPTIONS]
        select_menu = discord.ui.Select(
            placeholder="👆 Bước 1/2: Chọn giới tính của bạn...",
            options=options,
            custom_id="verify_step1_gender"
        )
        select_menu.callback = self.gender_callback
        self.add_item(select_menu)

    def _build_step2(self):
        self.clear_items()
        options = [discord.SelectOption(label=g["label"], value=g["value"]) for g in GAME_OPTIONS]
        select_menu = discord.ui.Select(
            placeholder="🎮 Bước 2/2: Chọn game bạn chơi (có thể chọn nhiều)!",
            options=options,
            custom_id="verify_step2_game",
            min_values=1,
            max_values=len(options)
        )
        select_menu.callback = self.game_callback
        self.add_item(select_menu)

    async def gender_callback(self, interaction: discord.Interaction):
        chosen_value = interaction.data['values'][0]
        self.chosen_gender = next((g for g in GENDER_OPTIONS if g["value"] == chosen_value), None)
        if not self.chosen_gender:
            return await interaction.response.edit_message(content="❌ Lỗi!", embed=None, view=None)

        self.step = 2
        self._build_step2()
        embed = self._make_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def game_callback(self, interaction: discord.Interaction):
        chosen_values = interaction.data['values']  # list (multi-select)
        if not chosen_values:
            return await interaction.response.edit_message(content="❌ Chưa chọn game nào!", embed=None, view=None)

        await interaction.response.edit_message(content="⏳ Đang xử lý xác minh...", embed=None, view=None)

        # Cấp Verified Role
        verified_role = self.guild.get_role(VERIFIED_ROLE_ID)
        if not verified_role:
            return await interaction.edit_original_response(content=f"❌ Không tìm thấy Role ID `{VERIFIED_ROLE_ID}`!")

        try:
            await self.member.add_roles(verified_role, reason="Hoàn thành xác minh danh tính.")
        except discord.Forbidden:
            return await interaction.edit_original_response(content="❌ Bot thiếu quyền cấp Role!")

        # Cấp Role Game cho từng game đã chọn
        game_names = []
        for val in chosen_values:
            game = next((g for g in GAME_OPTIONS if g["value"] == val), None)
            if game and game.get("role_id"):
                game_role = self.guild.get_role(game["role_id"])
                if game_role:
                    try:
                        await self.member.add_roles(game_role, reason=f"Xác minh: {game['label']}")
                        game_names.append(game['label'])
                    except discord.Forbidden:
                        pass

        # Tạo hồ sơ với giới tính đã chọn
        profile_id = None
        try:
            async with await self.bot.db_manager.connect() as conn:
                async with conn.execute("SELECT id FROM royal_profiles WHERE user_id = ?", (self.member.id,)) as cursor:
                    exists = await cursor.fetchone()
                if not exists:
                    now = datetime.utcnow().isoformat()
                    cursor = await conn.execute(
                        "INSERT INTO royal_profiles (user_id, gender, updated_at) VALUES (?, ?, ?)",
                        (self.member.id, self.chosen_gender["gender"], now)
                    )
                    await conn.commit()
                    profile_id = cursor.lastrowid
                    logger.info(f"✅ Đã tự tạo hồ sơ #{profile_id} cho {self.member.name}")
        except Exception as e:
            logger.error(f"Lỗi tạo hồ sơ: {e}")

        game_text = ", ".join(game_names) if game_names else "Không có"
        desc = (
            f"🏰 **Chào mừng đến với Royal City!**\n\n"
            f"👤 **Cư dân:** {self.member.mention}\n"
            f"⚧️ **Giới tính:** `{self.chosen_gender['gender']}`\n"
            f"🎮 **Game:** `{game_text}`\n"
            f"🛡️ **Role:** {verified_role.mention}\n"
        )
        desc += (f"📋 **Hồ sơ:** `#{profile_id:03d}` đã được tạo tự động!" if profile_id else "⚠️ Có lỗi khi tạo hồ sơ, hãy báo Admin.")

        success_embed = discord.Embed(
            title="✨ Xác Minh Thành Công! ✨",
            description=desc,
            color=discord.Color.green()
        )
        success_embed.set_footer(text="Hệ thống xác minh tự động Royal City 🏙️")
        await interaction.edit_original_response(content=None, embed=success_embed, view=None)

    def _make_embed(self):
        if self.step == 1:
            desc = "🏰 **Chào mừng đến với Royal City!**\n\n👉 **Bước 1/2:** Chọn giới tính của bạn bên dưới."
        else:
            desc = (
                f"⚧️ **Giới tính:** `{self.chosen_gender['gender']}`\n\n"
                f"👉 **Bước 2/2:** Chọn những game bạn chơi (có thể chọn nhiều)! 🎮"
            )
        embed = discord.Embed(
            title="🧚‍♀️ Xác Minh Danh Tính 🧚‍♀️",
            description=desc,
            color=discord.Color.from_rgb(88, 101, 242)
        )
        embed.set_footer(text=f"Bước {self.step}/2")
        return embed


class VerificationLandingView(discord.ui.View):
    """Bảng nút bấm xác minh công khai"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Bắt đầu xác minh", style=discord.ButtonStyle.success, custom_id="royal_city_gatekeeper_btn")
    async def start_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        view = VerificationStepView(interaction.client, member, interaction.guild)

        await interaction.response.send_message(
            embed=view._make_embed(),
            view=view,
            ephemeral=True
        )

class VerificationCog(commands.Cog):
    """Cog quản lý xác minh thành viên — chỉ đăng ký persistent view, không có lệnh admin"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Đăng ký persistent view cho landing page (timeout=None để sống vĩnh viễn)
        self.bot.add_view(VerificationLandingView())


async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
