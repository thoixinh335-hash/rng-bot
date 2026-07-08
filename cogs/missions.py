import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

CHAT_TARGET = 30       # 30 tin nhắn
ROLL_TARGET = 3        # 3 lần roll
VOICE_TARGET = 1800    # 30 phút (giây)


class MissionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._voice_join_times: dict[int, float] = {}  # user_id -> timestamp

    async def _get_or_create(self, user_id: int) -> dict:
        """Lấy hoặc tạo mới bản ghi nhiệm vụ hôm nay"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        async with await self.bot.db_manager.connect() as conn:
            conn.row_factory = lambda cursor, row: dict(
                zip([col[0] for col in cursor.description], row)
            )
            async with conn.execute(
                "SELECT * FROM daily_missions WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if not row or row["date"] != today:
                # Tạo mới hoặc reset nếu sang ngày mới
                await conn.execute(
                    "INSERT OR REPLACE INTO daily_missions (user_id, chat_count, roll_count, voice_seconds, date, free_rolls) "
                    "VALUES (?, 0, 0, 0, ?, 0)",
                    (user_id, today),
                )
                await conn.commit()
                return {
                    "user_id": user_id, "chat_count": 0, "roll_count": 0,
                    "voice_seconds": 0, "date": today, "free_rolls": 0
                }

            return row

    def _check_mission_complete(self, data: dict) -> tuple[int, bool, bool, bool]:
        """Trả về (số mission đã hoàn thành, chat_done, roll_done, voice_done)"""
        chat_done = data["chat_count"] >= CHAT_TARGET
        roll_done = data["roll_count"] >= ROLL_TARGET
        voice_done = data["voice_seconds"] >= VOICE_TARGET
        return sum([chat_done, roll_done, voice_done]), chat_done, roll_done, voice_done

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        today = datetime.utcnow().strftime("%Y-%m-%d")
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute(
                "SELECT chat_count, date FROM daily_missions WHERE user_id = ?",
                (message.author.id,),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                await conn.execute(
                    "INSERT INTO daily_missions (user_id, chat_count, roll_count, voice_seconds, date, free_rolls) "
                    "VALUES (?, 1, 0, 0, ?, 0)",
                    (message.author.id, today),
                )
            elif row[1] != today:
                await conn.execute(
                    "UPDATE daily_missions SET chat_count=1, roll_count=0, voice_seconds=0, date=?, free_rolls=0 WHERE user_id=?",
                    (today, message.author.id),
                )
            else:
                await conn.execute(
                    "UPDATE daily_missions SET chat_count = chat_count + 1 WHERE user_id = ?",
                    (message.author.id,),
                )
            await conn.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        now = datetime.utcnow().timestamp()

        # Vào voice (hoặc chuyển kênh)
        if after.channel and (not before.channel or before.channel != after.channel):
            # Nếu đang ở kênh cũ thì ghi nhận thời gian trước khi chuyển
            if before.channel and before.channel != after.channel:
                join_time = self._voice_join_times.pop(member.id, None)
                if join_time:
                    elapsed = int(now - join_time)
                    if elapsed >= 5:
                        await self._add_voice_seconds(member.id, elapsed)
            self._voice_join_times[member.id] = now

        # Rời voice
        elif before.channel and not after.channel:
            join_time = self._voice_join_times.pop(member.id, None)
            if join_time:
                elapsed = int(now - join_time)
                if elapsed >= 5:
                    await self._add_voice_seconds(member.id, elapsed)

    async def _add_voice_seconds(self, user_id: int, seconds: int):
        """Cộng dồn số giây voice vào daily_missions"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute(
                "SELECT voice_seconds, date FROM daily_missions WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                await conn.execute(
                    "INSERT INTO daily_missions (user_id, chat_count, roll_count, voice_seconds, date, free_rolls) "
                    "VALUES (?, 0, 0, ?, ?, 0)",
                    (user_id, seconds, today),
                )
            elif row[1] != today:
                await conn.execute(
                    "UPDATE daily_missions SET voice_seconds=?, chat_count=0, roll_count=0, date=?, free_rolls=0 WHERE user_id=?",
                    (seconds, today, user_id),
                )
            else:
                await conn.execute(
                    "UPDATE daily_missions SET voice_seconds = voice_seconds + ? WHERE user_id = ?",
                    (seconds, user_id),
                )
            await conn.commit()

    @app_commands.command(name="missions", description="Xem tiến độ nhiệm vụ hàng ngày và lượt roll free.")
    async def missions(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user = interaction.user
        data = await self._get_or_create(user.id)

        completed, chat_done, roll_done, voice_done = self._check_mission_complete(data)

        def bar(current: int, target: int, done: bool) -> str:
            if done:
                return f"✅ **Hoàn thành!** ({current}/{target})"
            return f"⬜ {current}/{target}"

        embed = discord.Embed(
            title=f"📋 NHIỆM VỤ HÀNG NGÀY - {user.name}",
            description=f"Reset lúc **0h UTC** mỗi ngày\n🎁 Mỗi nhiệm vụ hoàn thành = **+1 lượt roll free**\n\n"
                        f"🆓 Lượt roll free hiện có: **{data['free_rolls']}**",
            color=discord.Color.blue()
        )

        embed.add_field(
            name=f"💬 Chat {data['chat_count']}/{CHAT_TARGET} tin nhắn",
            value=bar(data["chat_count"], CHAT_TARGET, chat_done),
            inline=False
        )
        embed.add_field(
            name=f"🎰 Roll {data['roll_count']}/{ROLL_TARGET} lần",
            value=bar(data["roll_count"], ROLL_TARGET, roll_done),
            inline=False
        )

        voice_mins = data["voice_seconds"] // 60
        target_mins = VOICE_TARGET // 60
        embed.add_field(
            name=f"🎤 Voice {voice_mins}/{target_mins} phút",
            value=bar(data["voice_seconds"], VOICE_TARGET, voice_done),
            inline=False
        )

        # Kiểm tra boost
        boost_role_id = self.bot.config_service.get("boost_role_id", 0)
        has_boost = False
        if boost_role_id and interaction.guild:
            member = interaction.guild.get_member(user.id)
            if member:
                has_boost = any(r.id == boost_role_id for r in member.roles)

        if has_boost:
            embed.add_field(
                name="⚡ Boost Server",
                value="✅ **+1 slot vĩnh viễn** mỗi lần roll",
                inline=False
            )

        embed.set_footer(text=f"Hoàn thành: {completed}/3 nhiệm vụ")
        await interaction.followup.send(embed=embed)

    async def use_free_roll(self, user_id: int) -> bool:
        """Dùng 1 lượt roll free. Tự động claim mission đã hoàn thành. Trả về True nếu dùng được."""
        # Tự động claim free rolls từ mission đã hoàn thành
        await self.claim_free_rolls(user_id)

        async with await self.bot.db_manager.connect() as conn:
            # Lấy free_rolls hiện tại
            async with conn.execute(
                "SELECT free_rolls FROM daily_missions WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                current_free = row[0] if row else 0

            if current_free > 0:
                await conn.execute(
                    "UPDATE daily_missions SET free_rolls = free_rolls - 1 WHERE user_id = ?",
                    (user_id,),
                )
                await conn.commit()
                return True

        return False

    async def add_roll_count(self, user_id: int):
        """+1 roll count cho nhiệm vụ"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        async with await self.bot.db_manager.connect() as conn:
            async with conn.execute(
                "SELECT roll_count, date FROM daily_missions WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()

            if not row:
                await conn.execute(
                    "INSERT INTO daily_missions (user_id, chat_count, roll_count, voice_seconds, date, free_rolls) "
                    "VALUES (?, 0, 1, 0, ?, 0)",
                    (user_id, today),
                )
            elif row[1] != today:
                await conn.execute(
                    "UPDATE daily_missions SET roll_count=1, chat_count=0, voice_seconds=0, date=?, free_rolls=0 WHERE user_id=?",
                    (today, user_id),
                )
            else:
                await conn.execute(
                    "UPDATE daily_missions SET roll_count = roll_count + 1 WHERE user_id = ?",
                    (user_id,),
                )
            await conn.commit()

    async def claim_free_rolls(self, user_id: int) -> int:
        """Claim free rolls từ mission đã hoàn thành. Trả về số vừa claim."""
        data = await self._get_or_create(user_id)
        completed, chat_done, roll_done, voice_done = self._check_mission_complete(data)

        # Tính số mission mới hoàn thành (chưa claim)
        # Mỗi mission done = 1 free_roll. free_rolls đang lưu trong DB là số đã claim.
        # Ta cần biết đã claim bao nhiêu để tránh claim lại
        already_claimed = data["free_rolls"]

        # Nếu đã claim đủ 3 rồi thì thôi
        if already_claimed >= 3:
            return 0

        new_claims = completed - already_claimed
        if new_claims <= 0:
            return 0

        async with await self.bot.db_manager.connect() as conn:
            await conn.execute(
                "UPDATE daily_missions SET free_rolls = ? WHERE user_id = ?",
                (completed, user_id),
            )
            await conn.commit()

        return new_claims

    def has_boost(self, interaction: discord.Interaction) -> bool:
        """Kiểm tra user có boost server không"""
        boost_role_id = self.bot.config_service.get("boost_role_id", 0)
        if not boost_role_id or not interaction.guild:
            return False
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False
        return any(r.id == boost_role_id for r in member.roles)


async def setup(bot: commands.Bot):
    await bot.add_cog(MissionsCog(bot))
