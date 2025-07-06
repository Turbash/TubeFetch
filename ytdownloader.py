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
    import time
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': get_format_string(quality),
    }
    if subtitles:
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = [subtitle_lang]
        ydl_opts['subtitlesformat'] = 'best'

    try:
        before = set(os.listdir('.'))
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'downloaded_video')
            ext = info.get('ext', None)
            # 1. Try yt-dlp's prepare_filename with ext
            base_filename = ydl.prepare_filename(info)
            if ext:
                merged_filename = os.path.splitext(base_filename)[0] + f".{ext}"
                if os.path.exists(merged_filename):
                    return os.path.abspath(merged_filename)
            # 2. Try base_filename itself
            if os.path.exists(base_filename):
                return os.path.abspath(base_filename)
            # 3. Try any new file created after download started
            after = set(os.listdir('.'))
            new_files = list(after - before)
            if new_files:
                # Pick the newest file that matches the title
                candidates = [f for f in new_files if title in f]
                if candidates:
                    newest = max(candidates, key=os.path.getmtime)
                    return os.path.abspath(newest)
                # Fallback: just return the newest file
                newest = max(new_files, key=os.path.getmtime)
                return os.path.abspath(newest)
            # 4. Fallback: return the most recently modified video file
            video_exts = ('.mp4', '.webm', '.mkv')
            video_files = [f for f in os.listdir('.') if f.endswith(video_exts)]
            if video_files:
                newest = max(video_files, key=os.path.getmtime)
                return os.path.abspath(newest)
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