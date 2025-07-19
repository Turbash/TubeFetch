import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from ytdownloader import get_available_qualities, download_youtube_video, get_video_info_with_sizes, find_best_quality_for_size_limit
import asyncio
from mega import Mega
import urllib.parse

load_dotenv()
TOKEN = os.getenv('TOKEN')
MEGA_EMAIL = os.getenv('MEGA_EMAIL')
MEGA_PASSWORD = os.getenv('MEGA_PASSWORD')

def upload_to_mega(filepath):
    """Upload to MEGA with credentials - no size limits, permanent storage"""
    try:
        print(f"DEBUG: Uploading to MEGA: {filepath}")
        
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"DEBUG: File size for MEGA upload: {file_size_mb:.1f}MB")
        
        mega = Mega()
        m = mega.login(MEGA_EMAIL, MEGA_PASSWORD)
        
        file_handle = m.upload(filepath)
        
        link = m.get_upload_link(file_handle)
        
        print(f"DEBUG: MEGA upload successful: {link}")
        return link
        
    except Exception as e:
        print(f"MEGA upload exception: {e}")
        return None

# Bot setup

intents = discord.Intents.default()
intents.message_content = True

class TubeFetchBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="tubefetch!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
    
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        raise error

bot = TubeFetchBot()

@bot.event
async def on_guild_join(guild):
    intro = (
        "👋 Hi! I'm TubeFetch, your YouTube video downloader bot.\n"
        "Use `/fetch` to download videos, `/qualities` to see available qualities, and `/subtitles` to see available subtitles.\n"
        "Type `/help` for a list of all commands and usage instructions!"
    )
    channel = guild.system_channel
    if channel is None or not channel.permissions_for(guild.me).send_messages:
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                channel = c
                break
    if channel:
        await channel.send(intro)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.tree.command(name="help", description="Show TubeFetch command documentation")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**TubeFetch Bot Commands:**\n"
        "• `/fetch url:<YouTube URL> quality:<quality> subtitles:<true/false> language:<lang>`\n"
        " Download a YouTube video at the specified quality and (optionally) subtitles.\n"
        "• `/qualities url:<YouTube URL>`\n"
        " List available video qualities for a YouTube link.\n"
        "• `/subtitles url:<YouTube URL>`\n"
        " List available subtitle languages for a YouTube link.\n"
        "• `/help`\n"
        " Show this help message.\n"
        "\n"
        "• **Note:** If the video is too large for Discord, you'll get a MEGA download link (permanent)."
    )
    await interaction.response.send_message(help_text, ephemeral=True)

@bot.tree.command(name="qualities", description="List available video qualities and subtitles for a YouTube link")
@app_commands.describe(url="The YouTube video URL")
async def qualities(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("Fetching available qualities...", ephemeral=True)
    loop = asyncio.get_running_loop()
    try:
        qualities, subtitles = await loop.run_in_executor(None, get_available_qualities, url)
        qualities_list = [q for q in qualities if q not in ("best", "worst")]
        msg = f"Available qualities: {', '.join(qualities_list) or 'None'}"
    except Exception as e:
        msg = f"Error fetching qualities: {e}"
    await interaction.followup.send(msg, ephemeral=True)

@bot.tree.command(name="subtitles", description="List available subtitle languages for a YouTube link")
@app_commands.describe(url="The YouTube video URL")
async def subtitles(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("Checking available subtitles...", ephemeral=True)
    loop = asyncio.get_running_loop()
    try:
        _, subtitles = await loop.run_in_executor(None, get_available_qualities, url)
        if subtitles:
            langs = ', '.join(subtitles.keys())
            msg = f"Available subtitle languages: {langs}"
        else:
            msg = "No subtitles available for this video."
    except Exception as e:
        msg = f"Error fetching subtitles: {e}"
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
    loop = asyncio.get_running_loop()
    files_to_delete = []
    try:
        await interaction.followup.send("Checking video size and available qualities...")
        video_info = await loop.run_in_executor(None, get_video_info_with_sizes, url)
        quality_info, available_subtitles, video_title = video_info
        
        user_quality = quality.lower()
        
        requested_size_mb = None
        if user_quality in quality_info and quality_info[user_quality]:
            requested_size_mb = quality_info[user_quality]['size_mb']
        elif user_quality.isdigit() and f"{user_quality}p" in quality_info:
            quality = f"{user_quality}p"
            if quality_info[quality]:
                requested_size_mb = quality_info[quality]['size_mb']
        elif user_quality in ['best', 'worst']:
            quality = user_quality
        else:
            quality = 'best'
        
        MAX_DISCORD_MB = 25
        
        if requested_size_mb and requested_size_mb > MAX_DISCORD_MB:
            await interaction.followup.send(
                f"📹 Video will be {requested_size_mb:.1f}MB - too large for Discord.\n"
                f"☁️ Will upload to MEGA after download."
            )

        await interaction.followup.send(f"⬬ Downloading '{video_title}' at {quality} quality...")
        filename = await loop.run_in_executor(None, download_youtube_video, url, quality, subtitles, language)
        print(f"DEBUG: download_youtube_video returned filename: {filename}")
        print(f"DEBUG: os.path.exists({filename}): {os.path.exists(filename) if filename else 'N/A'}")

        if filename and os.path.exists(filename):
            files_to_delete.append(filename)
            file_size = os.path.getsize(filename)
            subtitle_file = None
            if subtitles:
                base, _ = os.path.splitext(filename)
                for ext in [f".{language}.vtt", f".{language}.srt"]:
                    subfile = f"{base}{ext}"
                    if os.path.exists(subfile):
                        subtitle_file = subfile
                        files_to_delete.append(subfile)
                        break
            try:
                if file_size < 25 * 1024 * 1024:
                    files_to_send = [discord.File(filename)]
                    if subtitle_file:
                        files_to_send.append(discord.File(subtitle_file))
                    await interaction.followup.send(files=files_to_send)
                else:
                    await interaction.followup.send("Video is large, uploading to MEGA...")
                    link = await loop.run_in_executor(None, upload_to_mega, filename)
                    if link:
                        await interaction.followup.send(f"Video is too large for Discord. Download it here: {link}\n(Hosted on MEGA - permanent)")
                    else:
                        await interaction.followup.send("Upload failed")
            except Exception:
                await interaction.followup.send("Video was downloaded but could not be sent. The file has been deleted from the server.")
            finally:
                for f in files_to_delete:
                    if os.path.exists(f):
                        os.remove(f)
        else:
            await interaction.followup.send(
                f"Failed to download the video. Please check the URL, quality, or subtitle language.\n"
                f"DEBUG: filename={filename}, exists={os.path.exists(filename) if filename else 'N/A'}"
            )
    except Exception as e:
        await interaction.followup.send("An unexpected error occurred. Please try again or contact the bot admin.")
    finally:
        for f in files_to_delete:
            if os.path.exists(f):
                os.remove(f)
bot.run(TOKEN)