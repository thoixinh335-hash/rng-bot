import discord
from discord.ext import commands
import random
import asyncio

# ==========================================
# DANH SÁCH CÁC ĐỊA ĐIỂM BÍ MẬT (Có thể thêm bớt tùy thích)
# ==========================================
LOCATIONS = [
    "Trạm Không Gian 🚀", "Bãi Biển Royal 🏖️", "Rạp Xiếc Trung Ương 🎪", 
    "Bệnh Viện Tâm Thần 🏥", "Khách Sạn 5 Sao 🏨", "Nhà Hàng Pháp 🍽️", 
    "Trường Học 🏫", "Căn Cứ Quân Sự 🪖", "Tàu Ngầm Hạt Nhân ⚓", 
    "Sân Bay Quốc Tế ✈️", "Đảo Hoang Ký 🏝️", "Phim Trường Hollywood 🎬"
]

class SpyfallGame:
    def __init__(self, host, channel):
        self.host = host
        self.channel = channel
        self.players = []       
        self.spy = None         
        self.location = ""      
        self.votes = {}         
        self.voted_users = set() 
        self.is_started = False

# ==========================================
# 1. GIAO DIỆN PHÒNG CHỜ (JOIN GAME)
# ==========================================
class SpyfallJoinView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=180) 
        self.game = game

    @discord.ui.button(label="🙋‍♂️ Tham Gia", style=discord.ButtonStyle.success, custom_id="spy_join")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.game.players:
            await interaction.response.send_message("⚠️ Cậu đã ở trong phòng chờ rồi nhé!", ephemeral=True)
            return
        
        if self.game.is_started:
            await interaction.response.send_message("❌ Ván đấu đã bắt đầu mất rồi, hẹn cậu ván sau nha!", ephemeral=True)
            return

        self.game.players.append(interaction.user)
        await interaction.response.send_message("✅ Đã ghi danh thành công! Vui lòng kiểm tra chắc chắn rằng cậu **đang MỞ DM (Tin nhắn riêng)** để nhận mật thư từ Bot.", ephemeral=True)
        await self.update_lobby_message(interaction)

    @discord.ui.button(label="🏃‍♂️ Rời Phòng", style=discord.ButtonStyle.secondary, custom_id="spy_leave")
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.game.players:
            await interaction.response.send_message("⚠️ Cậu chưa tham gia phòng chờ này.", ephemeral=True)
            return

        self.game.players.remove(interaction.user)
        await interaction.response.send_message("👋 Đã rời phòng chờ.", ephemeral=True)
        await self.update_lobby_message(interaction)

    @discord.ui.button(label="🚀 Bắt Đầu", style=discord.ButtonStyle.danger, custom_id="spy_start")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.game.host:
            await interaction.response.send_message("❌ Chỉ có chủ phòng mới có quyền nhấn Bắt đầu ván đấu!", ephemeral=True)
            return

        if len(self.game.players) < 3:
            await interaction.response.send_message("⚠️ Game này cần tối thiểu **3 người chơi** trở lên mới vui cậu ơi!", ephemeral=True)
            return

        self.game.is_started = True
        self.stop() 
        
        self.game.location = random.choice(LOCATIONS)
        self.game.spy = random.choice(self.game.players)

        failed_dms = []
        for player in self.game.players:
            try:
                embed = discord.Embed(title="🕵️‍♂️ MẬT THƯ ĐIỆP VIÊN NẰM VÙNG", color=discord.Color.purple())
                if player == self.game.spy:
                    embed.description = (
                        "🔴 **BẠN LÀ ĐIỆP VIÊN (SPY)!**\n\n"
                        "⚠️ Bạn **KHÔNG BIẾT** địa điểm hôm nay là gì.\n"
                        "🎯 **Nhiệm vụ:** Hãy chú ý lắng nghe câu hỏi và câu trả lời của mọi người để đoán ra địa điểm bí mật, đồng thời trả lời khéo léo để không ai nghi ngờ bạn!\n\n"
                        f"🗺️ *Gợi ý danh sách địa điểm của ván này để cậu dễ chém gió:* \n`" + ", ".join(LOCATIONS) + "`"
                    )
                    embed.set_thumbnail(url="https://media.tenor.com/P0_8O_u0v7gAAAAi/love-letters-love.gif")
                else:
                    embed.description = (
                        "🔵 **BẠN LÀ CƯ DÂN CHÍNH THỨC!**\n\n"
                        f"🎯 Địa điểm bí mật của ván này là: **{self.game.location}**\n\n"
                        "🔎 **Nhiệm vụ:** Hãy đặt những câu hỏi thông minh liên quan đến địa điểm này để tìm ra kẻ đang ngơ ngác 'chém gió' (Điệp viên), nhưng đừng hỏi quá lộ liễu kẻo Điệp viên đoán ra địa điểm nhé!"
                    )
                await player.send(embed=embed)
            except discord.Forbidden:
                failed_dms.append(player.mention)

        start_embed = discord.Embed(
            title="🕵️‍♂️ GAME BẮT ĐẦU: ĐIỆP VIÊN NẰM VÙNG!",
            description=(
                f"🎲 **Tổng số người chơi:** {len(self.game.players)} cư dân.\n"
                f"🤫 Mật thư vai trò đã được gửi vào DM của từng người.\n\n"
                f"💬 **Luật chơi:** Mọi người hãy lần lượt đặt câu hỏi xoay vòng cho nhau. "
                f"Thời gian thảo luận tự do bắt đầu! Khi đã nghi ngờ ai, hãy kéo xuống chọn tên ở thanh menu **Tố Giác** bên dưới."
            ),
            color=discord.Color.dark_red()
        )
        if failed_dms:
            start_embed.add_field(name="⚠️ Cảnh báo khóa DM:", value=f"Các bạn sau đang khóa DM nên không nhận được vai trò: {', '.join(failed_dms)}.", inline=False)
        
        await interaction.message.edit(embed=start_embed, view=SpyfallGameView(self.game))

    async def update_lobby_message(self, interaction):
        player_list = "\n".join([f"• {p.mention}" for p in self.game.players]) if self.game.players else "*Chưa có ai tham gia...*"
        embed = discord.Embed(
            title="🕵️‍♂️ PHÒNG CHỜ: ĐIỆP VIÊN NẰM VÙNG",
            description=(
                f"👑 **Chủ phòng:** {self.game.host.mention}\n\n"
                f"👥 **Danh sách cư dân đăng ký ({len(self.game.players)}):**\n{player_list}\n\n"
                "👉 Bấm nút **Tham Gia** để nhận mật thư vai trò ẩn danh!"
            ),
            color=discord.Color.gold()
        )
        await interaction.message.edit(embed=embed, view=self)

# ==========================================
# 2. GIAO DIỆN TRONG TRẬN (TỐ GIÁC / VOTE)
# ==========================================
class SpyfallDropdown(discord.ui.Select):
    def __init__(self, game):
        self.game = game
        options = [
            discord.SelectOption(label=player.display_name, value=str(player.id), emoji="👤")
            for player in game.players
        ]
        super().__init__(placeholder="Chọn người cậu nghi ngờ là Điệp Viên...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user not in self.game.players:
            await interaction.response.send_message("❌ Cậu không tham gia ván đấu này nên không có quyền bỏ phiếu!", ephemeral=True)
            return

        if interaction.user.id in self.game.voted_users:
            await interaction.response.send_message("⚠️ Cậu đã bỏ phiếu xong rồi, không được thay đổi đâu nè.", ephemeral=True)
            return

        voted_id = int(self.values[0])
        self.game.voted_users.add(interaction.user.id)
        self.game.votes[voted_id] = self.game.votes.get(voted_id, 0) + 1

        voted_user = interaction.guild.get_member(voted_id)
        await interaction.response.send_message(f"✅ Cậu đã bỏ phiếu bí mật tố giác **{voted_user.display_name}**!", ephemeral=True)

        if len(self.game.voted_users) == len(self.game.players):
            await self.view.end_game_voting(interaction)

class SpyfallGameView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
        self.add_item(SpyfallDropdown(self.game))

    async def end_game_voting(self, interaction: discord.Interaction):
        if not self.game.votes:
            return

        max_votes = max(self.game.votes.values())
        most_voted_ids = [k for k, v in self.game.votes.items() if v == max_votes]

        end_embed = discord.Embed(title="🏁 KẾT QUẢ ĐẤU TRƯỜNG ĐIỆP VIÊN", color=discord.Color.blue())
        
        vote_details = ""
        for uid, count in self.game.votes.items():
            u = interaction.guild.get_member(uid)
            if u: vote_details += f"• **{u.display_name}**: {count} phiếu\n"
        end_embed.add_field(name="📊 Bảng tổng sắp phiếu bầu:", value=vote_details, inline=False)

        if len(most_voted_ids) > 1:
            end_embed.description = f"💥 Server bị chia rẽ phiếu bầu! Điệp viên thực sự là {self.game.spy.mention}.\n\n🏆 **ĐIỆP VIÊN CHIẾN THẮNG TRONG GANG TẤC!**"
            end_embed.color = discord.Color.red()
        else:
            final_suspect_id = most_voted_ids[0]
            if final_suspect_id == self.game.spy.id:
                end_embed.description = f"🎉 Chúc mừng dân làng! Hội đồng đã bỏ phiếu chính xác Điệp viên nằm vùng: {self.game.spy.mention}!\n\n🏆 **CƯ DÂN ROYAL CITY CHIẾN THẮNG!**"
                end_embed.add_field(name="🗺️ Địa điểm bí mật hôm nay:", value=f"💥 **{self.game.location}**")
                end_embed.color = discord.Color.green()
            else:
                wrong_user = interaction.guild.get_member(final_suspect_id)
                end_embed.description = f"💔 Thảm kịch! Hội đồng đã bỏ phiếu oan cho công dân lương thiện {wrong_user.mention}.\n\n🕵️‍♂️ Điệp viên thực sự là {self.game.spy.mention} đã trốn thoát thành công!\n🏆 **ĐIỆP VIÊN CHIẾN THẮNG TRỌN VẸN!**"
                end_embed.add_field(name="🗺️ Địa điểm bí mật hôm nay:", value=f"💥 **{self.game.location}**")
                end_embed.color = discord.Color.red()

        for item in self.children:
            item.disabled = True
        
        await interaction.channel.send(embed=end_embed)
        cog = interaction.client.get_cog("SpyfallCog")
        if cog and interaction.channel.id in cog.active_games:
            del cog.active_games[interaction.channel.id]

# ==========================================
# 3. PHÂN HỆ CHÍNH (ĐÃ ĐỔI TÊN LỆNH THÀNH /DIEPVIEN)
# ==========================================
class SpyfallCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {} 

    @commands.hybrid_command(name="diepvien", description="Mở một phòng chờ chơi game Điệp Viên Nằm Vùng (Spyfall)")
    async def spyfall_command(self, ctx: commands.Context):
        channel_id = ctx.channel.id
        
        if channel_id in self.active_games:
            await ctx.send("⚠️ Kênh này đang có một ván game đang diễn ra rồi cậu ơi!")
            return

        new_game = SpyfallGame(host=ctx.author, channel=ctx.channel)
        self.active_games[channel_id] = new_game

        embed = discord.Embed(
            title="🕵️‍♂️ PHÒNG CHỜ: ĐIỆP VIÊN NẰM VÙNG",
            description=(
                f"👑 **Chủ phòng:** {ctx.author.mention}\n\n"
                "👥 **Danh sách cư dân đăng ký (1):**\n• *Chưa có thêm ai tham gia...*\n\n"
                "👉 Hãy nhấn vào nút **Tham Gia** bên dưới để ghi danh vào mật thư hệ thống!"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Royal City Game Center • Cần tối thiểu 3 người chơi 🦉")
        
        new_game.players.append(ctx.author)
        await ctx.send(embed=embed, view=SpyfallJoinView(new_game))

async def setup(bot):
    await bot.add_cog(SpyfallCog(bot))