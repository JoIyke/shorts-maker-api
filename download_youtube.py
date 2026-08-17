import sys
import subprocess
import argparse

def download_video(url, output_file="output.mp4"):
    print(f"Downloading YouTube URL: {url}")
    
    # Bypass YouTube datacenter IP blocking using the Android/Web player client
    cmd = [
        "yt-dlp",
        "--extractor-args", "youtube:player_client=android,web",
        "--no-check-certificates",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", output_file,
        url
    ]
    
    subprocess.run(cmd, check=True)
    print("Download complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--payload_file', default='payload.json')
    args = parser.parse_args()

    import json
    with open(args.payload_file, 'r') as f:
        payload = json.load(f)

    yt_url = payload.get('url') or payload.get('youtube_url')
    if not yt_url:
        print("Error: No YouTube URL provided in payload.")
        sys.exit(1)

    download_video(yt_url, "output.mp4")
