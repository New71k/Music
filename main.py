import os
import logging
import asyncio
from discord.ext import commands
from music import Music

logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix="!!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}!")

@bot.command()
@commands.is_owner()
async def sync(ctx, guild=None):
    if guild is None:
        await bot.tree.sync()
    else:
        await bot.tree.sync(guild=discord.Object(id=int(guild)))
    await ctx.send("**Comandos sincronizados com sucesso!**")

async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        token = input("Insira o token do seu bot: ").strip()
    
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(token)

asyncio.run(main())
