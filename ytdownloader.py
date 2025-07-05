import yt_dlp
import os

def get_available_qualities(url):
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        qualities = {}
        for f in formats:
            if f.get('vcodec', 'none') != 'none':
                height = f.get('height')
                if height:
                    key = f"{height}p"
                    qualities[key] = height
        qualities['best'] = None
        qualities['worst'] = None
        print("\nAvailable video qualities for this video:")
        for q in sorted(qualities.keys(), key=lambda x: (x != 'best' and x != 'worst', int(x[:-1]) if x[:-1].isdigit() else 9999)):
            print(f"  {q}")
        subtitles = info.get('subtitles', {})
        if subtitles:
            print("\nAvailable subtitle languages:")
            print("  " + ", ".join(subtitles.keys()))
        else:
            print("\nNo subtitles available for this video.")
        return qualities, subtitles
def get_format_string(quality):
    if quality == "best":
        return "bestvideo+bestaudio/best"
    elif quality == "worst":
        return "worstvideo+worstaudio/worst"
    elif quality.endswith("p") and quality[:-1].isdigit():
        height = int(quality[:-1])
        return f"bestvideo[height={height}]+bestaudio/best[height={height}]/best[height={height}]"
    else:
        return "bestvideo+bestaudio/best"

def download_youtube_video(
    url,
    quality='best',
    subtitles=False,
    subtitle_lang='en'
):
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': get_format_string(quality),
    }
    if subtitles:
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = [subtitle_lang]
        ydl_opts['subtitlesformat'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'downloaded_video')
            for ext in ['mp4', 'webm', 'mkv']:
                video_filename = f"{title}.{ext}"
                if os.path.exists(video_filename):
                    if subtitles:
                        subtitle_filename = f"{title}.{subtitle_lang}.vtt"
                        if not os.path.exists(subtitle_filename):
                            subtitle_filename = f"{title}.{subtitle_lang}.srt"
                        if subtitle_filename and os.path.exists(subtitle_filename):
                            print(f"Subtitles downloaded: {subtitle_filename}")
                    return video_filename
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {e}")
    return None

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    qualities, subtitles = get_available_qualities(url)
    print("\nChoose a quality from above (e.g., 360p, 720p, best, worst):")
    user_quality = input("Enter quality: ").lower()
    if user_quality in qualities:
        quality = user_quality
    elif user_quality.isdigit() and f"{user_quality}p" in qualities:
        quality = f"{user_quality}p"
    else:
        quality = 'best'
    sub = False
    lang = 'en'
    if subtitles:
        sub = input("Download subtitles? (y/n): ").lower() == 'y'
        if sub:
            lang = input(f"Subtitle language {list(subtitles.keys())}: ") or 'en'

    filename = download_youtube_video(url, quality=quality, subtitles=sub, subtitle_lang=lang)
    if filename:
        print(f"Downloaded: {filename}")
    else:
        print("Download failed or format not available.")