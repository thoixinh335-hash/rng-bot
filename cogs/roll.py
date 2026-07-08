import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from services.config_service import ConfigService

# ============== BUTTON VIEW CHỌN SLOT ==============
class RollChoiceView(discord.ui.View):
    def __init__(self, cog, user_id: int, slots: list[dict]):
        super().__init__(timeout=3600)  # 1 giờ timeout
        self.cog = cog
        self.user_id = user_id
        self.slots = slots
        self.chosen = False

        # Tạo button cho mỗi slot
        for i, role in enumerate(slots, 1):
            button = discord.ui.Button(
                label=f"Slot {i}",
                style=discord.ButtonStyle.primary,
                custom_id=f"pick_{i}",
                emoji=role.get("emoji", "🎲")
            )
            button.callback = self._make_callback(i)
            self.add_item(button)

    def _make_callback(self, slot: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Chỉ người roll mới được chọn!", ephemeral=True)
                return
            if self.chosen:
                await interaction.response.send_message("⚠️ Bạn đã chọn rồi!", ephemeral=True)
                return

            self.chosen = True
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            await self.cog._apply_choice(interaction, slot)
        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class RollCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_service = ConfigService()

    async def _cleanup_expired_inventory(self, user_id: int):
        async with await self.bot.db_manager.connect() as conn:
            cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            await conn.execute(
                "DELETE FROM roll_inventory WHERE user_id = ? AND created_at < ?",
                (user_id, cutoff)
            )
            await conn.commit()

    async def _get_inventory(self, user_id: int) -> list[dict]:
        await self._cleanup_expired_inventory(user_id)
        roles_list = self.config_service.get_roles_list()
        roles_dict = {r["role_id"]: r for r in roles_list}

        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute(
                "SELECT slot, role_id, created_at FROM roll_inventory WHERE user_id = ? ORDER BY slot",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()

        result = []
        for row in rows:
            role = roles_dict.get(row[1])
            if role:
                result.append({
                    "slot": row[0],
                    "role": role,
                    "created_at": row[2]
                })
        return result

    async def _save_inventory(self, user_id: int, roles: list[dict]):
        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("DELETE FROM roll_inventory WHERE user_id = ?", (user_id,))
            now = datetime.utcnow().isoformat()
            for i, role in enumerate(roles, 1):
                await conn.execute(
                    "INSERT INTO roll_inventory (user_id, role_id, slot, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, role["role_id"], i, now)
                )
            await conn.commit()

    @app_commands.command(name="roll", description="Quay tối đa 3 lần và chọn 1 danh hiệu để nhận. Hồi chiêu mỗi 3 giờ.")
    @app_commands.describe(count="Số lượt quay (1-3, mặc định 1)")
    async def roll(self, interaction: discord.Interaction, count: int = 1):
        # Defer NGAY LẬP TỨC để tránh interaction timeout (Unknown interaction)
        await interaction.response.defer()

        if count < 1 or count > 3:
            await interaction.followup.send("❌ Số lượt quay phải từ **1 đến 3**.", ephemeral=True)
            return

        user = interaction.user
        player_service = self.bot.player_service
        rng_engine = self.bot.rng_engine
        season_service = self.bot.season_service

        await season_service.check_and_update_season()
        player = await player_service.get_player(user.id)

        if not player:
            roles_list = self.config_service.get_roles_list()
            player = await player_service.create_player(user.id, user.name, roles_list[0])

        missions_cog = self.bot.get_cog("MissionsCog")
        used_mission_free = False

        if missions_cog and await missions_cog.use_free_roll(user.id):
            used_mission_free = True

        if not used_mission_free:
            roll_limit = self.config_service.get("roll_limit", 3)
            limit_hours = self.config_service.get("roll_limit_hours", 3)
            rolls_used = player.get("rolls_used", 0) or 0
            window_start_str = player.get("rolls_window_start")

            now = datetime.utcnow()
            window_expired = True
            if window_start_str:
                try:
                    window_start = datetime.fromisoformat(window_start_str)
                    elapsed = (now - window_start).total_seconds()
                    if elapsed < limit_hours * 3600:
                        window_expired = False
                except Exception:
                    window_expired = True

            if window_expired:
                rolls_used = 0

            if rolls_used >= roll_limit:
                if window_start_str and not window_expired:
                    try:
                        window_start = datetime.fromisoformat(window_start_str)
                        window_end = window_start + timedelta(hours=limit_hours)
                        remaining = (window_end - now).total_seconds()
                        hours = int(remaining // 3600)
                        minutes = int((remaining % 3600) // 60)
                        seconds = int(remaining % 60)
                    except Exception:
                        hours = minutes = seconds = 0
                else:
                    hours = minutes = seconds = 0

                embed = discord.Embed(
                    title="⚠️ ĐÃ HẾT LƯỢT QUAY",
                    description=f"Bạn đã dùng hết {roll_limit} lượt quay trong {limit_hours} tiếng qua.\n\n⏱️ Reset sau: {hours:02d} giờ {minutes:02d} phút {seconds:02d} giây",
                    color=discord.Color.from_rgb(255, 75, 75)
                )
                embed.set_footer(text=f"Giới hạn: {roll_limit} lượt / {limit_hours} tiếng")
                await interaction.followup.send(embed=embed)
                return

        existing = await self._get_inventory(user.id)
        if existing:
            slot_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            inventory_text = ""
            for item in existing:
                role = item["role"]
                inventory_text += f"{slot_emojis[item['slot']-1]} **Slot {item['slot']}**: {role['emoji']} {role['name']}\n"

            embed = discord.Embed(
                title="⚠️ BẠN CÓ INVENTORY CHƯA CHỌN!",
                description=f"Đây là các danh hiệu bạn đang có:\n\n{inventory_text}\nDùng `/pick <số>` hoặc click nút để chọn.",
                color=discord.Color.orange()
            )
            slots_roles = [item["role"] for item in existing]
            view = RollChoiceView(self, user.id, slots_roles)
            await interaction.followup.send(embed=embed, view=view)
            return

        has_boost = missions_cog and missions_cog.has_boost(interaction)
        boost_slot_role = None
        if has_boost:
            async with await self.bot.db_manager.connect() as conn:
                async with conn.execute(
                    "SELECT boost_slot_role_id FROM players WHERE user_id = ?",
                    (user.id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    boost_slot_role_id = row[0] if row and row[0] else None
            if boost_slot_role_id:
                roles_list = self.config_service.get_roles_list()
                boost_slot_role = next((r for r in roles_list if r["role_id"] == boost_slot_role_id), None)

        rolled_roles = rng_engine.roll_multi(player["lucky"], count=count)
        if has_boost:
            count += 1  
            if boost_slot_role:
                rolled_roles.append(boost_slot_role)

        await self._save_inventory(user.id, rolled_roles)

        if missions_cog:
            await missions_cog.add_roll_count(user.id)

        async with await self.bot.db_manager.connect() as conn:
            now_iso = datetime.utcnow().isoformat()
            ws = player.get("rolls_window_start")
            limit_hours_cfg = self.config_service.get("roll_limit_hours", 3)
            window_valid = False
            if ws:
                try:
                    ws_dt = datetime.fromisoformat(ws)
                    elapsed = (datetime.utcnow() - ws_dt).total_seconds()
                    if elapsed < limit_hours_cfg * 3600:
                        window_valid = True
                except Exception:
                    pass

            if window_valid:
                await conn.execute(
                    "UPDATE players SET total_rolls = total_rolls + 1, rolls_used = rolls_used + 1, last_roll = ?, updated_at = ? WHERE user_id = ?",
                    (now_iso, now_iso, user.id)
                )
            else:
                await conn.execute(
                    "UPDATE players SET total_rolls = total_rolls + 1, rolls_used = 1, rolls_window_start = ?, last_roll = ?, updated_at = ? WHERE user_id = ?",
                    (now_iso, now_iso, now_iso, user.id)
                )
            await conn.commit()

        boost_text = " ⚡+1 Boost" if has_boost else ""
        free_text = " 🆓 Free Roll (Mission)!" if used_mission_free else ""

        pick_commands = " | ".join(f"`/pick {i}`" for i in range(1, len(rolled_roles) + 1))
        embed = discord.Embed(
            title=f"🎰 KHO BÁU VÒNG QUAY - CHỌN 1 TRONG {len(rolled_roles)}",
            description=f"{user.mention} vừa mở kho báu!{free_text}{boost_text}\n\n{pick_commands}\n\n⏰ **Hết hạn sau 1 tiếng!**",
            color=discord.Color.gold()
        )

        slot_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        ticks = '`' * 3
        for i, role in enumerate(rolled_roles):
            color_hex = role.get("embed_color", "0xFFFFFF").replace("0x", "")
            val_text = f"{ticks}yaml\nRank: {role['rank']}/30\nTỷ lệ: 1/{role['chance']:,}\nMàu: #{color_hex}\n{ticks}"
            embed.add_field(
                name=f"{slot_emojis[i]} SLOT {i+1}: {role['emoji']} {role['name']}",
                value=val_text,
                inline=True
            )

        embed.set_footer(text=f"Luck hiện tại: +{player['lucky']}%  •  Nhấn nút bên dưới hoặc gõ /pick <số>")
        view = RollChoiceView(self, user.id, rolled_roles)
        await interaction.followup.send(embed=embed, view=view)

    async def _apply_choice(self, interaction: discord.Interaction, slot: int):
        user = interaction.user
        player_service = self.bot.player_service
        role_manager = self.bot.role_manager
        announcement_service = self.bot.announcement_service

        inventory = await self._get_inventory(user.id)
        if not inventory:
            await interaction.followup.send("📭 Kho báu trống hoặc đã hết hạn.")
            return

        chosen = None
        for item in inventory:
            if item["slot"] == slot:
                chosen = item
                break

        if not chosen:
            slots_available = ", ".join(str(i["slot"]) for i in inventory)
            await interaction.followup.send(f"❌ Slot {slot} không tồn tại. Có: {slots_available}")
            return

        async with await self.bot.db_manager.connect() as conn:
            await conn.execute("DELETE FROM roll_inventory WHERE user_id = ?", (user.id,))
            await conn.commit()

        chosen_role = chosen["role"]
        player = await player_service.get_player(user.id)
        is_highest = chosen_role["rank"] > player["highest_rank"]

        galactic_rank = self.config_service.get("galactic_rank", 19)
        if chosen_role["rank"] < galactic_rank:
            next_lucky = player["lucky"] + 1
        else:
            next_lucky = 0

        await player_service.process_roll_transaction(
            user_id=user.id, username=user.name,
            rolled_role=chosen_role, is_highest=is_highest,
            next_lucky=next_lucky
        )

        try:
            member = interaction.guild.get_member(user.id)
            if not member:
                member = await interaction.guild.fetch_member(user.id)
            if member:
                await role_manager.update_discord_roles(member, chosen_role["role_id"])
        except Exception as e:
            print(f"Lỗi cấp vai trò Discord: {e}")

        try:
            await announcement_service.broadcast_roll(user, chosen_role)
        except Exception:
            pass

        color = int(chosen_role["embed_color"], 16)
        embed = discord.Embed(
            title="✅ ĐÃ CHỌN DANH HIỆU",
            description=f"{user.mention} đã chọn slot **{slot}**:\n\n{chosen_role['emoji']} **{chosen_role['name'].upper()}**",
            color=color
        )
        embed.add_field(name="🎲 TỶ LỆ GỐC", value=f"`1/{chosen_role['chance']:,}`", inline=True)
        embed.add_field(name="⭐ RANK", value=f"`{chosen_role['rank']}/30`", inline=True)
        embed.add_field(name="🔮 LUCK LƯỢT SAU", value=f"`+{next_lucky}%`" if next_lucky > 0 else "`Reset (0%)`", inline=True)

        if is_highest:
            embed.add_field(name="🏆 KỶ LỤC MỚI!", value="Đây là danh hiệu cao nhất bạn từng đạt được!", inline=False)

        unpicked = [item for item in inventory if item["slot"] != slot]
        if unpicked:
            unpicked_text = ", ".join(f"{item['role']['emoji']} **{item['role']['name']}**" for item in unpicked)
            embed.add_field(name="🗑️ ĐÃ HỦY BỎ", value=unpicked_text, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pick", description="Chọn 1 danh hiệu từ inventory sau khi roll.")
    @app_commands.describe(slot="Số slot bạn muốn chọn")
    async def pick(self, interaction: discord.Interaction, slot: int):
        if slot < 1:
            await interaction.response.send_message("❌ Số slot phải từ **1** trở lên.", ephemeral=True)
            return
        await interaction.response.defer()
        await self._apply_choice(interaction, slot)

    @app_commands.command(name="inventory", description="Xem kho báu hiện tại - các danh hiệu đang chờ bạn chọn.")
    async def inventory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user = interaction.user
        inventory = await self._get_inventory(user.id)

        if not inventory:
            embed = discord.Embed(
                title="📭 KHO BÁU TRỐNG",
                description="Bạn chưa có inventory nào. Hãy dùng `/roll` để quay trước nhé!",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"🎒 KHO BÁU CỦA {user.name.upper()}",
            description=f"Bạn có **{len(inventory)}** danh hiệu đang chờ chọn:\n\n⏰ Tự động xóa sau **1 tiếng** kể từ lúc roll.",
            color=discord.Color.gold()
        )

        slot_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        ticks = '`' * 3
        for item in inventory:
            role = item["role"]
            slot = item["slot"]
            color_hex = role.get("embed_color", "0xFFFFFF").replace("0x", "")
            val_text = f"{ticks}yaml\nRank: {role['rank']}/30\nTỷ lệ: 1/{role['chance']:,}\nMàu: #{color_hex}\n{ticks}"
            embed.add_field(
                name=f"{slot_emojis[slot-1]} SLOT {slot}: {role['emoji']} {role['name']}",
                value=val_text,
                inline=True
            )

        slots_roles = [item["role"] for item in inventory]
        view = RollChoiceView(self, user.id, slots_roles)
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(RollCog(bot))