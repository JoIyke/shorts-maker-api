import os
import subprocess
import argparse

# Import our design specialists
from designs import crop_basic, meme_style

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--design', required=True)
    # We can add custom text for memes later!
    parser.add_argument('--top_text', default="WAIT FOR IT") 
    args = parser.parse_args()

    print(f"Starting job: {args.url} | Design: {args.design}")

    # 1. Download Video
    print("Downloading video...")
    download_cmd = [
        "yt-dlp", 
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", 
        "-o", "input.mp4", 
        args.url
    ]
    subprocess.run(download_cmd, check=True)

    # 2. Route to the correct design specialist
    input_file = "input.mp4"
    output_file = "output.mp4"

    if args.design == 'crop':
        crop_basic.render(input_file, output_file, args.start, args.end, args)
    elif args.design == 'meme':
        meme_style.render(input_file, output_file, args.start, args.end, args)
    else:
        print(f"Unknown design '{args.design}'. Defaulting to basic crop.")
        crop_basic.render(input_file, output_file, args.start, args.end, args)

    print("Director: Rendering complete!")

if __name__ == "__main__":
    main()
