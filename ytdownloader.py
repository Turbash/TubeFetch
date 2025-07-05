import yt_dlp
import os

def download_youtube_video(url, output_template='downloaded_video.%(ext)s'):
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for ext in ['mp4', 'webm', 'mkv']:
        filename = f'downloaded_video.{ext}'
        if os.path.exists(filename):
            return filename
    return None

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    download_youtube_video(url)