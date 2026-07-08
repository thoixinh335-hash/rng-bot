import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger("rng_bot")
ADMIN_ID = 1119820359500304396  # ID tối cao của cậu

# ====================================================
# KHAI BÁO ID CÁC ROLE ĐÃ ĐỒNG BỘ CHUẨN XÁC 100%
# ====================================================
ROLE_MAP = {
    # 🎮 NHÓM GAME PHỔ BIẾN
    "game_other": 1503825065970499698,
    "game_csgo": 1503825062921240667,
    "game_ff": 1503825059460939877,
    "game_tft": 1503825055832870963,
    "game_minecraft": 1503825052108587142,
    "game_lienquan": 1503825048039981208,
    "game_roblox": 1503825045045252136,
    "game_valorant": 1503825041262116966,

    # 💖 NHÓM TRẠNG THÁI MỐI QUAN HỆ
    "status_lop": 1504440352713605222,
    "status_docthan": 1504544174588956746,
    "status_quanhe": 1504544966460965017,
    "status_phuctap": 1504545191418400811,

    # ⚧️ NHÓM GIỚI TÍNH / PRONOUNS
    "gender_he": 1503825023079678133,
    "gender_she": 1503825019443089418
}


# Hàm xử lý bật/tắt Role chung chống trùng lặp code
async def toggle_user_role(interaction: discord.Interaction, role_key: str):
    role_id = ROLE_MAP.get(role_key)
    if not role_id:
        return await interaction.response.send_message("❌ Role này chưa được thiết lập ID chính xác trong mã nguồn!", ephemeral=True)

    guild = interaction.guild
    role = guild.get_role(role_id)
    if not role:
        return await interaction.response.send_message("❌ Không tìm thấy Role này trên máy chủ Discord!", ephemeral=True)

    member = guild.get_member(interaction.user.id)

    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"➖ Đã gỡ bỏ vai trò: **{role.name}**", ephemeral=True)
    else:
        await member.add_roles(role)
        await interaction.response.send_message(f"➕ Đã cấp vai trò: **{role.name}**", ephemeral=True)


# Hàm gán/gỡ nhiều role cùng lúc (cho menu chọn nhiều)
async def toggle_multi_roles(interaction: discord.Interaction, role_keys: list[str]):
    guild = interaction.guild
    member = guild.get_member(interaction.user.id)

    added = []
    removed = []

    for key in role_keys:
        role_id = ROLE_MAP.get(key)
        if not role_id:
            continue
        role = guild.get_role(role_id)
        if not role:
            continue

        if role in member.roles:
            await member.remove_roles(role)
            removed.append(role.name)
        else:
            await member.add_roles(role)
            added.append(role.name)

    msg_parts = []
    if added:
        msg_parts.append(f"➕ Đã cấp: **{', '.join(added)}**")
    if removed:
        msg_parts.append(f"➖ Đã gỡ: **{', '.join(removed)}**")

    if msg_parts:
        await interaction.response.send_message("\n".join(msg_parts), ephemeral=True)
    else:
        await interaction.response.send_message("Không có thay đổi.", ephemeral=True)


# ==========================================
# CẤU TRÚC 3 MENU THẢ XUỐNG DÀNH CHO CƯ DÂN
# ==========================================
class GameRoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Không chơi game", emoji="🚫", value="game_other"),
            discord.SelectOption(label="Valorant", emoji="🏹", value="game_valorant"),
            discord.SelectOption(label="Roblox", emoji="🍮", value="game_roblox"),
            discord.SelectOption(label="Liên Quân Mobile", emoji="⚔️", value="game_lienquan"),
            discord.SelectOption(label="Minecraft", emoji="📦", value="game_minecraft"),
            discord.SelectOption(label="Đấu Trường Chân Lý (TFT)", emoji="🐧", value="game_tft"),
            discord.SelectOption(label="Free Fire", emoji="🐯", value="game_ff"),
            discord.SelectOption(label="CS:GO / CS2", emoji="💣", value="game_csgo"),
            discord.SelectOption(label="Game khác...", emoji="🎮", value="game_other"),
        ]
        super().__init__(
            placeholder="🎮 Chọn các tựa game cậu chơi (chọn nhiều được)...",
            options=options,
            max_values=len(options),
            min_values=0,
            custom_id="royal_self_game_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await toggle_multi_roles(interaction, self.values)


class GenderRoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="He / Him", emoji="🙋‍♂️", value="gender_he"),
            discord.SelectOption(label="She / Her", emoji="🙋‍♀️", value="gender_she"),
        ]
        super().__init__(
            placeholder="⚧️ Chọn giới tính / danh xưng của cậu...",
            options=options,
            max_values=1,
            custom_id="royal_self_gender_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await toggle_user_role(interaction, self.values[0])


class StatusRoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Độc thân", emoji="💔", value="status_docthan"),
            discord.SelectOption(label="Trong một mối quan hệ", emoji="💖", value="status_quanhe"),
            discord.SelectOption(label="Mối quan hệ phức tạp", emoji="❤️‍🩹", value="status_phuctap"),
            discord.SelectOption(label="Lốp dự phòng", emoji="🛞", value="status_lop"),
        ]
        super().__init__(placeholder="💘 Cập nhật tình trạng mối quan hệ...", options=options, custom_id="royal_self_status_select")

    async def callback(self, interaction: discord.Interaction):
        await toggle_user_role(interaction, self.values[0])


# Gói tổng hợp 3 Dropdown vào chung 1 bảng panel
class SelfRolesPersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Giúp các Menu thả xuống hoạt động mãi mãi kể cả khi restart bot
        self.add_item(GameRoleSelect())
        self.add_item(GenderRoleSelect())
        self.add_item(StatusRoleSelect())


class SelfRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(SelfRolesPersistentView())

    @app_commands.command(name="setup_roles", description="Khởi tạo bảng nhận danh hiệu/role tự động cho server (Chỉ Admin tối cao)")
    async def setup_roles(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Cậu không có quyền dùng lệnh này!", ephemeral=True)
            
        embed = discord.Embed(
            title="⚜️ TRUNG TÂM CẤP PHÁT DANH HIỆU ROYAL CITY ⚜️",
            color=discord.Color.from_rgb(255, 192, 203) # Màu hồng lãng mạn giống bảng xác minh
        )
        embed.description = (
            f"Chào mừng cư dân đã thông quan thành công! 🎉\n"
            f"Để mọi người dễ dàng tìm cạ cày game và ghép đôi trò chuyện, "
            f"cậu hãy tự chọn các vai trò định danh cho mình nhé!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎮 **Menu 1:** Chọn các tựa game cậu đang cày cuốc.\n"
            f"⚧️ **Menu 2:** Chọn danh xưng/giới tính của cậu.\n"
            f"💘 **Menu 3:** Cập nhật tình trạng mối quan hệ thực tế.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *Lưu ý: Chọn lần đầu để nhận vai trò, chọn lại lần nữa để hủy bỏ vai trò đó.*"
        )
        embed.set_image(url="https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1000")
        embed.set_footer(text="Hệ thống tự động hóa cư dân Royal City 🌃")
        
        await interaction.response.send_message("✅ Đã khởi tạo bảng phân tách vai trò thành công!", ephemeral=True)
        await interaction.channel.send(embed=embed, view=SelfRolesPersistentView())

async def setup(bot):
    await bot.add_cog(SelfRolesCog(bot))