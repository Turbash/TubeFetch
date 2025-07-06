# TubeFetch

TubeFetch is a Discord bot that allows users to download YouTube videos directly from Discord, with support for video quality selection, subtitle downloads, and large file handling.

---

## Features

- **Slash Commands** for a modern Discord experience
- **Choose video quality** (e.g., 360p, 720p, best, worst)
- **List available qualities and subtitles** for any YouTube video
- **Download subtitles** in your preferred language
- **Handles Discord file size limits**: uploads large files to [transfer.sh](https://transfer.sh) and provides a temporary download link
- **Ephemeral responses** for privacy
- **Robust error handling** and file cleanup

---

## Commands

- `/fetch url:<YouTube URL> quality:<quality> subtitles:<true/false> language:<lang>`
  - Download a YouTube video at the specified quality and (optionally) subtitles.
- `/qualities url:<YouTube URL>`
  - List available video qualities for a YouTube link.
- `/subtitles url:<YouTube URL>`
  - List available subtitle languages for a YouTube link.
- `/help`
  - Show help and usage instructions.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/TubeFetch.git
cd TubeFetch
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your Discord bot token

- Create a `.env` file in the project root:
  ```
  TOKEN=your_discord_bot_token_here
  ```

### 4. Run the bot

```bash
python3 bot.py
```

---

## Notes

- If a video is too large for Discord, TubeFetch will upload it to [transfer.sh](https://transfer.sh) and provide a temporary download link (valid for 14 days).
- The bot introduces itself when joining a new server.
- All commands are slash commands for ease of use.

---

## License

MIT License

---

## Contributing

Pull requests and suggestions are welcome! Please open an issue or submit a PR.

---

## Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading
- [discord.py](https://github.com/Rapptz/discord.py) for Discord integration
- [transfer.sh](https://transfer.sh) for temporary file hosting

---

**Enjoy downloading YouTube videos right from your Discord server!**