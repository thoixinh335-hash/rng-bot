import discord
from discord.ext import commands
from discord import app_commands
import os
import shutil
from datetime import datetime, timedelta
import aiosqlite
import logging
from services.config_service import ConfigService

logger = logging.getLogger("rng_bot")

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_service = ConfigService()

    def is_owner(self, interaction: discord.Interaction) -> bool:
        admin_ids = self.config_service.get("admin_ids", [])
        return interaction.user.id in admin_ids

    admin_group = app_commands.Group(name="admin", description="Hệ thống lệnh kiểm soát đặc quyền tối cao của Quản Trị Viên.")

    @admin_group.command(name="reload", description="Tải lại toàn bộ tệp cấu hình JSON ngay lập tức mà không cần khởi động lại Bot.")
    async def reload_config(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi: Bạn không có đặc quyền Admin tối cao.", ephemeral=True)
            return
        self.config_service.load_all()
        await interaction.response.send_message("✅ Đã tải lại thành công dữ liệu từ `config.json` và `roles.json` vào Cache bộ nhớ.", ephemeral=True)

    @admin_group.command(name="stats", description="Xem chi tiết báo cáo hiệu năng và thông số kỹ thuật của hệ thống cơ sở dữ liệu.")
    async def system_stats(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return
        
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute("SELECT COUNT(*) FROM players") as c1:
                total_players = (await c1.fetchone())[0]
            async with conn.execute("SELECT COUNT(*) FROM history") as c2:
                total_history = (await c2.fetchone())[0]

        embed = discord.Embed(title="📊 THÔNG SỐ HỆ THỐNG BOT", color=discord.Color.dark_red())
        embed.add_field(name="👥 Tổng số người chơi", value=f"{total_players} người dùng")
        embed.add_field(name="📜 Bản ghi lịch sử lưu trữ", value=f"{total_history} dòng log")
        embed.add_field(name="⚙️ Phiên bản phần mềm", value=self.config_service.get("version", "1.0.0"))
        await interaction.response.send_message(embed=embed)

    @admin_group.command(name="backup", description="Tạo một bản sao lưu (Hot-Backup) an toàn cho cơ sở dữ liệu RNG.")
    async def backup_db(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return
        
        os.makedirs("assets", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"assets/rng_backup_{timestamp}.db"
        shutil.copyfile("database/rng.db", backup_path)
        await interaction.response.send_message(f"📁 Đã tạo bản sao lưu an toàn tại: `{backup_path}`", ephemeral=True)

    @admin_group.command(name="restore", description="Khôi phục trạng thái cơ sở dữ liệu từ file backup chỉ định.")
    @app_commands.describe(filename="Tên tệp tin backup nằm trong thư mục assets (ví dụ: rng_backup_XYZ.db)")
    async def restore_db(self, interaction: discord.Interaction, filename: str):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return
        
        source_path = f"assets/{filename}"
        if not os.path.exists(source_path):
            await interaction.response.send_message("❌ Lỗi: Không thể tìm thấy tệp tin backup chỉ định.", ephemeral=True)
            return
        
        # Đóng kết nối tạm thời bằng cách sao chép đè tệp trực tiếp
        shutil.copyfile(source_path, "database/rng.db")
        await interaction.response.send_message("✅ Khôi phục thành công cấu trúc cơ sở dữ liệu. Vui lòng thực hiện `/admin reload`.", ephemeral=True)

    @admin_group.command(name="reset-player", description="Xóa bỏ hoàn toàn dữ liệu của một người chơi cụ thể.")
    @app_commands.describe(target_user="Người chơi cần xóa dữ liệu")
    async def reset_player(self, interaction: discord.Interaction, target_user: discord.User):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return
        
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("DELETE FROM players WHERE user_id = ?", (target_user.id,))
            await conn.execute("DELETE FROM daily_missions WHERE user_id = ?", (target_user.id,))
            await conn.commit()
            
        await interaction.response.send_message(f"🧹 Đã xóa bỏ toàn bộ dữ liệu lịch sử và hồ sơ của người dùng {target_user.mention} khỏi hệ thống.", ephemeral=True)

    @admin_group.command(name="reset-season", description="Ép buộc kết thúc và reset mùa giải hiện tại ngay lập tức.")
    async def force_reset_season_cmd(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return
        
        await self.bot.season_service.force_reset_season()
        await interaction.response.send_message("🚨 CẢNH BÁO: Đã thực hiện dọn dẹp và reset toàn bộ dữ liệu để bước sang Season mới!", ephemeral=True)

    @admin_group.command(name="config", description="Hiển thị nóng các thông số đang chạy trong config.json.")
    async def view_config(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return

        conf = self.config_service.config
        embed = discord.Embed(title="⚙️ CONFIGURATION ENGINE LIVE VIEW", color=discord.Color.orange())
        for k, v in conf.items():
            embed.add_field(name=k, value=f"`{v}`", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="cleanup", description="Dọn dẹp toàn bộ dữ liệu người dùng đã rời server nhưng chưa được xử lý.")
    async def cleanup_left_members(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return

        await interaction.response.defer()
        guild = interaction.guild
        member_ids = {m.id for m in guild.members}

        async with await self.bot.db_manager.connect() as conn:
            # Lấy tất cả user_id từ players
            async with conn.execute("SELECT user_id FROM players") as cursor:
                all_players = await cursor.fetchall()

            removed_count = 0
            freed_marriages = 0
            for (uid,) in all_players:
                if uid not in member_ids:
                    # Xử lý spouse trước
                    async with conn.execute(
                        "SELECT spouse_id FROM royal_profiles WHERE user_id = ?", (uid,)
                    ) as cursor:
                        row = await cursor.fetchone()
                    if row and row[0]:
                        await conn.execute(
                            "UPDATE royal_profiles SET spouse_id = NULL, marriage_date = NULL, "
                            "love_points = 0 WHERE user_id = ?",
                            (row[0],),
                        )
                        freed_marriages += 1

                    # Xóa social data (giữ nguyên players/collections/history cho RNG)
                    await conn.execute("DELETE FROM royal_profiles WHERE user_id = ?", (uid,))
                    await conn.execute("DELETE FROM royal_afk WHERE user_id = ?", (uid,))
                    await conn.execute("DELETE FROM royal_reminders WHERE user_id = ?", (uid,))
                    await conn.execute("DELETE FROM royal_bans WHERE user_id = ?", (uid,))
                    await conn.execute("DELETE FROM roll_inventory WHERE user_id = ?", (uid,))
                    await conn.execute("DELETE FROM daily_missions WHERE user_id = ?", (uid,))

                    removed_count += 1

            await conn.commit()

        embed = discord.Embed(
            title="🧹 DỌN DẸP DỮ LIỆU GHOST",
            description=(
                f"✅ **Hoàn tất!**\n\n"
                f"🗑️ Đã xử lý: **{removed_count}** người dùng đã rời server\n"
                f"💔 Đã giải phóng: **{freed_marriages}** cuộc hôn nhân\n\n"
                f"*Dữ liệu RNG (players, collections, history) vẫn được giữ nguyên.*"
            ),
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)

    @admin_group.command(name="checkperms", description="Kiểm tra quyền của bot (Manage Roles, hierarchy).")
    async def check_perms(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Lệnh chỉ dùng trong server.", ephemeral=True)
            return

        me = guild.me
        perms = me.guild_permissions

        embed = discord.Embed(title="🔐 KIỂM TRA QUYỀN BOT", color=discord.Color.blue())

        # Quyền cơ bản
        embed.add_field(name="📋 Quyền cơ bản", value="\n".join([
            f"{'✅' if perms.manage_roles else '❌'} Manage Roles",
            f"{'✅' if perms.manage_guild else '❌'} Manage Guild",
            f"{'✅' if perms.kick_members else '❌'} Kick Members",
            f"{'✅' if perms.ban_members else '❌'} Ban Members",
        ]), inline=False)

        # Vị trí role bot
        bot_top_role = me.top_role
        embed.add_field(name="🤖 Bot top role", value=f"`{bot_top_role.name}` (position: {bot_top_role.position})", inline=False)

        # Check các role RNG
        roles_list = self.config_service.get_roles_list()
        rng_roles = []
        cannot_assign = []
        for r in roles_list:
            role = guild.get_role(r["role_id"])
            if role:
                rng_roles.append(f"  • {role.name} (position: {role.position})")
                if role.position >= bot_top_role.position:
                    cannot_assign.append(f"  ❌ {role.name} (position {role.position} >= bot {bot_top_role.position})")

        embed.add_field(name=f"🎭 RNG Roles ({len(rng_roles)}/{len(roles_list)})", value="\n".join(rng_roles[:10]) + ("\n..." if len(rng_roles) > 10 else ""), inline=False)

        if cannot_assign:
            embed.add_field(name="⚠️ KHÔNG THỂ GÁN", value="\n".join(cannot_assign), inline=False)
            embed.color = discord.Color.red()
        else:
            embed.add_field(name="✅ Kết quả", value="Bot có đủ quyền gán TẤT CẢ role RNG!", inline=False)
            embed.color = discord.Color.green()

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="resetall", description="⚠️ XÓA TẤT CẢ dữ liệu người chơi, history, collection, missions. KHÔNG THỂ HOÀN TÁC.")
    async def reset_all_data(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message("❌ Từ chối thực thi.", ephemeral=True)
            return

        # Đếm số dòng trước khi xóa
        async with await self.bot.db_manager.connect() as conn:
            counts = {}
            for table in ["players", "collections", "history", "roll_inventory", "daily_missions", "seasons"]:
                cursor = await conn.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = (await cursor.fetchone())[0]

        # Tạo confirm button
        class ConfirmView(discord.ui.View):
            def __init__(self, bot, caller_id: int, counts: dict):
                super().__init__(timeout=30)
                self.bot = bot
                self.caller_id = caller_id
                self.counts = counts
                self.confirmed = False

            @discord.ui.button(label="⚠️ XÁC NHẬN XÓA TẤT CẢ", style=discord.ButtonStyle.danger)
            async def confirm(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.caller_id:
                    await btn_interaction.response.send_message("❌ Chỉ người gọi mới xác nhận được!", ephemeral=True)
                    return

                self.confirmed = True
                for item in self.children:
                    item.disabled = True
                await btn_interaction.response.edit_message(view=self)

                # Xóa tất cả dữ liệu
                async with await self.bot.db_manager.connect() as conn:
                    await conn.execute("DELETE FROM collections")
                    await conn.execute("DELETE FROM history")
                    await conn.execute("DELETE FROM roll_inventory")
                    await conn.execute("DELETE FROM daily_missions")
                    await conn.execute("DELETE FROM players")
                    await conn.execute("DELETE FROM seasons")
                    await conn.commit()

                embed = discord.Embed(
                    title="🧹 ĐÃ XÓA TẤT CẢ DỮ LIỆU",
                    description="Đã reset toàn bộ hệ thống về trạng thái ban đầu.\n"
                                "Mọi người chơi cần `/roll` lại để tạo profile mới.",
                    color=discord.Color.red()
                )
                embed.add_field(name="📊 Đã xóa", value="\n".join([f"  • {t}: **{c}** dòng" for t, c in self.counts.items()]))
                await btn_interaction.followup.send(embed=embed)

            @discord.ui.button(label="Hủy", style=discord.ButtonStyle.secondary)
            async def cancel(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.caller_id:
                    return
                for item in self.children:
                    item.disabled = True
                await btn_interaction.response.edit_message(content="✅ Đã hủy.", embed=None, view=self)

        embed = discord.Embed(
            title="⚠️ XÁC NHẬN XÓA TẤT CẢ DỮ LIỆU",
            description="Lệnh này sẽ xóa **TOÀN BỘ** dữ liệu. **KHÔNG THỂ HOÀN TÁC**!\n\n"
                        "📊 Sắp xóa:\n" + "\n".join([f"  • {t}: **{c}** dòng" for t, c in counts.items()]),
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=ConfirmView(self.bot, interaction.user.id, counts), ephemeral=True)

    # ==========================================
    # ⚠️ HÀM TEST TẠM - XÓA SAU KHI TEST XONG!
    # ==========================================
    @app_commands.command(name="admintest", description="TEST: Kiểm tra bot hoạt động (chỉ admin 819822563588964383)")
    async def admin_test(self, interaction: discord.Interaction):
        if interaction.user.id != 819822563588964383:
            await interaction.response.send_message("❌ Chỉ dành cho admin test!", ephemeral=True)
            return

        # Kiểm tra toàn diện
        status_lines = []

        # 1. Kết nối Discord
        status_lines.append(f"✅ **Gateway**: {round(self.bot.latency * 1000)}ms")

        # 2. Database
        try:
            async with await self.bot.db_manager.connect() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM players")
                player_count = (await cursor.fetchone())[0]
                cursor = await conn.execute("SELECT COUNT(*) FROM history")
                history_count = (await cursor.fetchone())[0]
            status_lines.append(f"✅ **Database**: {player_count} players, {history_count} rolls")
        except Exception as e:
            status_lines.append(f"❌ **Database**: {e}")

        # 3. Config
        try:
            version = self.config_service.get("version", "?")
            roles = len(self.config_service.get_roles_list())
            status_lines.append(f"✅ **Config**: v{version}, {roles} roles")
        except Exception as e:
            status_lines.append(f"❌ **Config**: {e}")

        # 4. Server info
        guild = interaction.guild
        if guild:
            status_lines.append(f"✅ **Server**: {guild.name} ({guild.member_count} members)")
            bot_member = guild.me
            status_lines.append(f"✅ **Bot roles**: {len(bot_member.roles)} roles, top: {bot_member.top_role.name}")

        # 5. Cogs loaded
        cog_names = list(self.bot.cogs.keys())
        status_lines.append(f"✅ **Cogs**: {len(cog_names)} loaded")

        embed = discord.Embed(
            title="🔧 ADMIN TEST - SYSTEM CHECK",
            description="\n".join(status_lines),
            color=discord.Color.green()
        )
        embed.set_footer(text="Hàm test tạm - Xóa sau khi test xong!")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))