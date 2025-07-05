from ytdownloader import download_youtube_video
import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True

class TubeFetchBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = TubeFetchBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.tree.command(name="fetch", description="Download a YouTube video and upload it here")
@app_commands.describe(url="The YouTube video URL")
async def fetch(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("Downloading video, please wait...", ephemeral=True)
    filename = download_youtube_video(url)
    if filename:
        try:
            await interaction.followup.send(file=discord.File(filename))
        except Exception as e:
            await interaction.followup.send(f"Failed to send the file: {e}")
        finally:
            os.remove(filename)
    else:
        await interaction.followup.send("Failed to download the video. Please check the URL and try again.")

bot.run(TOKEN)