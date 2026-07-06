import discord
from discord.ext import commands
from discord import app_commands


class AvatarCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Lấy avatar của bạn hoặc người khác. Hỗ trợ nhiều định dạng.")
    @app_commands.describe(user="Người dùng muốn lấy avatar (mặc định là bạn)")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user

        # Lấy avatar URLs theo nhiều size
        avatar_256 = target.display_avatar.with_size(256).url
        avatar_512 = target.display_avatar.with_size(512).url
        avatar_1024 = target.display_avatar.with_size(1024).url

        # Check global avatar vs server avatar
        is_server_avatar = False
        if interaction.guild:
            member = interaction.guild.get_member(target.id)
            if member and member.guild_avatar:
                is_server_avatar = True
                server_avatar = member.guild_avatar.with_size(1024).url

        embed = discord.Embed(
            title=f"🖼️ Avatar của {target.name}",
            color=discord.Color.blue()
        )
        embed.set_image(url=avatar_1024)
        embed.set_thumbnail(url=target.default_avatar.url)

        # Links tải các size
        download_links = (
            f"[1024px]({avatar_1024}) • "
            f"[512px]({avatar_512}) • "
            f"[256px]({avatar_256})"
        )

        # Check loại avatar
        avatar_type = "Global Avatar"
        if is_server_avatar:
            avatar_type = "Server Avatar"
        if target.avatar is None:
            avatar_type = "Default Avatar"

        embed.add_field(name="📐 Links tải", value=download_links, inline=False)
        embed.add_field(name="📋 Loại", value=avatar_type, inline=True)
        embed.add_field(name="🆔 User ID", value=f"`{target.id}`", inline=True)

        if is_server_avatar:
            embed.add_field(name="🎭 Server Avatar", value=f"[1024px]({server_avatar})", inline=False)

        if target.banner:
            embed.add_field(name="🎨 Banner", value=f"[Link]({target.banner.with_size(512).url})", inline=False)

        embed.set_footer(text=f"Yêu cầu bởi {interaction.user.name}")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AvatarCog(bot))