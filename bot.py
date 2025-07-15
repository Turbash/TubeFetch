import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from ytdownloader import get_available_qualities, download_youtube_video, get_video_info_with_sizes, find_best_quality_for_size_limit
import requests
import asyncio

import urllib.parse

def upload_to_gofile(filepath):
    """Upload to gofile.io with API token for better limits and permanent storage"""
    try:
        print(f"DEBUG: Uploading to gofile.io: {filepath}")
        
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"DEBUG: File size for upload: {file_size_mb:.1f}MB")
        
        # Longer timeout for larger files
        timeout = max(600, int(600 + (file_size_mb / 100) * 60))
        print(f"DEBUG: Using timeout: {timeout} seconds")
        
        upload_url = "https://upload.gofile.io/uploadfile"
        
        # Prepare headers and data for API token
        headers = {}
        data = {}
        
        if GOFILE_API_TOKEN:
            headers['Authorization'] = f'Bearer {GOFILE_API_TOKEN}'
            print("DEBUG: Using GoFile API token for permanent storage")
            # With API token, we can specify additional options
        else:
            print("DEBUG: Using GoFile without token (guest upload)")
        
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                upload_url, 
                files=files,
                data=data,
                headers=headers,
                timeout=timeout,
                stream=True 
            )
        
        print(f"DEBUG: gofile.io response status: {response.status_code}")
        print(f"DEBUG: gofile.io response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                download_page = data['data']['downloadPage']
                print(f"DEBUG: gofile.io upload successful: {download_page}")
                return download_page
        
        print(f"DEBUG: gofile.io upload failed: {response.text}")
        return None
        
    except Exception as e:
        print(f"gofile.io upload exception: {e}")
        return None

def upload_to_fileio_fallback(filepath):
    """Simple file.io upload as fallback (no API token)"""
    try:
        print(f"DEBUG: Trying file.io fallback for {filepath}")
        
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {
                'expires': '14d',  # 14 days for free
                'maxDownloads': '100',  # Lower limit for free
                'autoDelete': 'true'
            }
            response = requests.post(
                'https://file.io/',
                files=files,
                data=data,
                timeout=300
            )
        
        print(f"DEBUG: file.io response status: {response.status_code}")
        print(f"DEBUG: file.io response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                link = data.get('link')
                print(f"DEBUG: file.io upload successful: {link}")
                return link
        print(f"DEBUG: file.io upload failed: {response.text}")
        return None
    except Exception as e:
        print(f"file.io upload exception: {e}")
        return None

def upload_large_file(filepath):
    """Upload large file with GoFile API token - much higher limits"""
    file_size = os.path.getsize(filepath)
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"DEBUG: File size: {file_size_mb:.1f}MB")
    
    # GoFile with API token has much higher limits (5GB+)
    MAX_UPLOAD_SIZE_MB = 2000 if GOFILE_API_TOKEN else 500  # 2GB with token, 500MB without
    
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        print(f"DEBUG: File too large: {file_size_mb:.1f}MB > {MAX_UPLOAD_SIZE_MB}MB")
        return None, f"File too large ({file_size_mb:.1f}MB). Max size: {MAX_UPLOAD_SIZE_MB}MB. Try a lower quality."
    
    # Try GoFile first (higher limits with API token)
    link = upload_to_gofile(filepath)
    if link:
        if GOFILE_API_TOKEN:
            return link, "GoFile.io with API (permanent)"
        else:
            return link, "GoFile.io (10 days)"
    
    # Fallback to file.io for smaller files
    if file_size_mb <= 100:  
        link = upload_to_fileio_fallback(filepath)
        if link:
            return link, "file.io (14 days)"
    
    return None, "Upload failed - try a lower quality."

load_dotenv()
TOKEN = os.getenv('TOKEN')
GOFILE_API_TOKEN = os.getenv('API_TOKEN')  # GoFile.io API token

intents = discord.Intents.default()
intents.message_content = True

class TubeFetchBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

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
        "• **Note:** If the video is too large for Discord, you'll get a temporary download link."
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
        MAX_UPLOAD_MB = 2000 if GOFILE_API_TOKEN else 500  # 2GB with GoFile API token
        
        if requested_size_mb:
            if requested_size_mb > MAX_UPLOAD_MB:
                best_quality, best_size = await loop.run_in_executor(None, find_best_quality_for_size_limit, quality_info, MAX_UPLOAD_MB)
                if best_quality:
                    await interaction.followup.send(
                        f"⚠️ Requested quality ({user_quality}) would be {requested_size_mb:.1f}MB (too large for hosting).\n"
                        f"🔄 Automatically using {best_quality} instead ({best_size:.1f}MB)."
                    )
                    quality = best_quality
                else:
                    await interaction.followup.send(
                        f"❌ Video is too large in all available qualities. Even the smallest quality exceeds {MAX_UPLOAD_MB}MB limit."
                    )
                    return
            elif requested_size_mb > MAX_DISCORD_MB:
                await interaction.followup.send(
                    f"📹 Video will be {requested_size_mb:.1f}MB - too large for Discord.\n"
                    f"☁️ Will upload to cloud storage after download."
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
                    await interaction.followup.send("Video is large, uploading to cloud storage...")
                    upload_result = await loop.run_in_executor(None, upload_large_file, filename)
                    link, service = upload_result
                    if link:
                        await interaction.followup.send(f"Video is too large for Discord. Download it here: {link}\n(Hosted on {service})")
                    else:
                        await interaction.followup.send(f"Upload failed: {service}")
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