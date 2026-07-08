import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ Thiếu DISCORD_BOT_TOKEN trong .env!")


class CleanupBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        pass

    async def on_ready(self):
        print("🚀 Đã đăng nhập, bắt đầu cleanup slash commands...")

        print("🗑️ Đang xóa GLOBAL slash commands...")
        self.tree.clear_commands(guild=None)
        global_result = await self.tree.sync()
        print(f"   ✅ Global commands còn lại: {len(global_result)}")

        # Xóa guild commands cho từng guild
        for guild in self.guilds:
            print(f"🗑️ Đang xóa GUILD commands cho: {guild.name}")
            self.tree.clear_commands(guild=guild)
            guild_result = await self.tree.sync(guild=guild)
            print(f"   ✅ Guild '{guild.name}' commands còn lại: {len(guild_result)}")

        print("\n🎉 ĐÃ XÓA SẠCH TOÀN BỘ SLASH COMMANDS!")
        print("👉 Hãy tắt script này và chạy lại main.py để sync guild commands mới.")
        await self.close()


bot = CleanupBot()
bot.run(TOKEN)