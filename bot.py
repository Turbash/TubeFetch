from ytdownloader import download_youtube_video
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.command()
async def fetch(ctx, url:str):
    await ctx.send("Downloading video, please wait...")
    filename = download_youtube_video(url)
    if filename:
        try:
            await ctx.send(file=discord.File(filename))
        except Exception as e:
            await ctx.send(f"Failed to send the file: {e}")
        finally:
            os.remove(filename)
    else:
        await ctx.send("Failed to download the video. Please check the URL and try again.")

bot.run(TOKEN)