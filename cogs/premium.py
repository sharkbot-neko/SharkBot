from discord.ext import commands
import discord

class PremiumCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> PremiumCog")

async def setup(bot):
    await bot.add_cog(PremiumCog(bot))