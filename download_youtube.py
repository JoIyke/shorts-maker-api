import sys
import json
import argparse
import ssl
import yt_dlp

# THE ULTIMATE SSL HAMMER: Forces Python to bypass all SSL certificate checks
ssl._create_default_https_context = ssl._create_unverified_context

def download_video(url, output_file="output.mp4"):
    print(f"Downloading YouTube URL via native API: {url}")
    
    # Configure yt-dlp natively
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_file,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    
    # Execute download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    print("Download complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--payload_file', default='payload.json')
    args = parser.parse_args()

    with open(args.payload_file, 'r') as f:
        payload = json.load(f)

    yt_url = payload.get('url') or payload.get('youtube_url')
    if not yt_url:
        print("Error: No YouTube URL provided in payload.")
        sys.exit(1)

    download_video(yt_url, "output.mp4")
