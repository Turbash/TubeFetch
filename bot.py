import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from ytdownloader import get_available_qualities, download_youtube_video

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

@bot.tree.command(name="qualities", description="List available video qualities and subtitles for a YouTube link")
@app_commands.describe(url="The YouTube video URL")
async def qualities(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("Fetching available qualities...", ephemeral=True)
    qualities, subtitles = get_available_qualities(url)
    qualities_list = [q for q in qualities if q not in ("best", "worst")]
    msg = f"Available qualities: {', '.join(qualities_list) or 'None'}"
    await interaction.followup.send(msg, ephemeral=True)

@bot.tree.command(name="subtitles", description="List available subtitle languages for a YouTube link")
@app_commands.describe(url="The YouTube video URL")
async def subtitles(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("Checking available subtitles...", ephemeral=True)
    _, subtitles = get_available_qualities(url)
    if subtitles:
        langs = ', '.join(subtitles.keys())
        msg = f"Available subtitle languages: {langs}"
    else:
        msg = "No subtitles available for this video."
    await interaction.followup.send(msg, ephemeral=True)

@bot.tree.command(name="fetch", description="Download a YouTube video at a chosen quality (and subtitles if available)")
@app_commands.describe(
    url="The YouTube video URL",
    quality="Quality (e.g., 360p, 720p, best, worst)",
    subtitles="Download subtitles? (true/false)",
    language="Subtitle language (e.g., en, hi, es)"
)
async def fetch(
    interaction: discord.Interaction,
    url: str,
    quality: str = "best",
    subtitles: bool = False,
    language: str = "en"
):
    await interaction.response.send_message(f"Downloading video at {quality} quality, please wait...", ephemeral=True)
    qualities, _ = get_available_qualities(url)
    user_quality = quality.lower()
    if user_quality in qualities:
        quality = user_quality
    elif user_quality.isdigit() and f"{user_quality}p" in qualities:
        quality = f"{user_quality}p"
    else:
        quality = 'best'
    filename = download_youtube_video(url, quality=quality, subtitles=subtitles, subtitle_lang=language)
    files_to_delete = []
    files_to_send = []
    if filename:
        files_to_delete.append(filename)
        if os.path.getsize(filename) < 25 * 1024 * 1024:
            files_to_send.append(discord.File(filename))
            if subtitles:
                base, _ = os.path.splitext(filename)
                for ext in [f".{language}.vtt", f".{language}.srt"]:
                    subfile = f"{base}{ext}"
                    if os.path.exists(subfile):
                        files_to_send.append(discord.File(subfile))
                        files_to_delete.append(subfile)
                        break
            try:
                await interaction.followup.send(files=files_to_send)
            except Exception as e:
                await interaction.followup.send("Video was downloaded but could not be sent. The file has been deleted from the server.")
            finally:
                for f in files_to_delete:
                    if os.path.exists(f):
                        os.remove(f)
        else:
            await interaction.followup.send("Video downloaded but is too large to send on Discord. The file has been deleted from the server.")
            for f in files_to_delete:
                if os.path.exists(f):
                    os.remove(f)
    else:
        await interaction.followup.send("Failed to download the video. Please check the URL, quality, or subtitle language.")
bot.run(TOKEN)