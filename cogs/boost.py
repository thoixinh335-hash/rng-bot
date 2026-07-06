import discord
from discord.ext import commands
from discord import app_commands


class BoostSlotView(discord.ui.View):
    """View hiển thị buttons cho mỗi role trong collection"""

    def __init__(self, cog, user_id: int, owned_roles: list[dict], current_slot_role_id: int | None):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.owned_roles = owned_roles
        self.current_slot_role_id = current_slot_role_id

        # Thêm button cho mỗi role trong collection
        for role in owned_roles:
            is_equipped = role["role_id"] == current_slot_role_id
            button = discord.ui.Button(
                label=f"{role['name']}",
                style=discord.ButtonStyle.success if is_equipped else discord.ButtonStyle.secondary,
                emoji=role.get("emoji", "🎲"),
                custom_id=f"equip_{role['role_id']}",
                disabled=is_equipped
            )
            button.callback = self._make_callback(role)
            self.add_item(button)

    def _make_callback(self, role: dict):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Chỉ người gọi mới chọn được!", ephemeral=True)
                return

            await self.cog._equip_role(interaction, role)
            # Disable tất cả button sau khi chọn
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
        return callback


class BoostCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="equipslot", description="Chọn 1 role từ collection để đặt vào slot boost vĩnh viễn.")
    async def equipslot(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user = interaction.user

        # Kiểm tra boost
        boost_role_id = self.bot.config_service.get("boost_role_id", 0)
        if not boost_role_id or not interaction.guild:
            await interaction.followup.send("❌ Hệ thống boost chưa được cấu hình.")
            return

        member = interaction.guild.get_member(user.id)
        if not member or not any(r.id == boost_role_id for r in member.roles):
            embed = discord.Embed(
                title="⚠️ CẦN BOOST SERVER",
                description="Lệnh này chỉ dành cho **Server Booster**.\n\nBoost server để có **+1 slot vĩnh viễn** trong inventory!",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)
            return

        # Lấy collection của user
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute(
                "SELECT role_id FROM collections WHERE user_id = ?",
                (user.id,)
            ) as cursor:
                rows = await cursor.fetchall()
                owned_ids = {r[0] for r in rows}

        # Lấy role hiện tại trong boost slot
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute(
                "SELECT boost_slot_role_id FROM players WHERE user_id = ?",
                (user.id,)
            ) as cursor:
                row = await cursor.fetchone()
                current_slot_role_id = row[0] if row and row[0] else None

        # Lấy danh sách role user đã sở hữu
        roles_list = self.bot.config_service.get_roles_list()
        owned_roles = [r for r in roles_list if r["role_id"] in owned_ids]

        if not owned_roles:
            embed = discord.Embed(
                title="📦 BỘ SƯU TẬP TRỐNG",
                description="Bạn chưa có role nào trong collection. Hãy `/roll` để sưu tập trước nhé!",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)
            return

        # Hiển thị embed
        current_text = ""
        if current_slot_role_id:
            current_role = next((r for r in roles_list if r["role_id"] == current_slot_role_id), None)
            if current_role:
                current_text = f"Hiện tại đang giữ: **{current_role['emoji']} {current_role['name']}**"

        embed = discord.Embed(
            title="⚡ CHỌN ROLE CHO SLOT BOOST",
            description=f"{current_text}\n\nClick nút bên dưới để chọn role đặt vào slot boost vĩnh viễn.\n\n"
                        f"📦 Collection của bạn: **{len(owned_roles)}/30** role\n"
                        f"⏰ Bỏ boost → role bị khóa tạm thời (không mất)",
            color=discord.Color.purple()
        )

        view = BoostSlotView(self, user.id, owned_roles, current_slot_role_id)
        await interaction.followup.send(embed=embed, view=view)

    async def _equip_role(self, interaction: discord.Interaction, role: dict):
        """Lưu role vào boost slot"""
        user = interaction.user
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute(
                "UPDATE players SET boost_slot_role_id = ?, updated_at = ? WHERE user_id = ?",
                (role["role_id"], interaction.message.created_at.isoformat(), user.id)
            )
            await conn.commit()

        embed = discord.Embed(
            title="✅ ĐÃ ĐẶT VÀO SLOT BOOST",
            description=f"Role **{role['emoji']} {role['name']}** đã được đặt vào slot boost vĩnh viễn!\n\n"
                        f"💡 Slot này sẽ được tự động áp dụng khi bạn `/roll`.\n"
                        f"⏰ Bỏ boost → role bị khóa tạm thời (vẫn giữ trong collection).",
            color=int(role["embed_color"], 16)
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BoostCog(bot))