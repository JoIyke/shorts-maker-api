import os
import subprocess
import argparse

# Import our design specialists
from designs import crop_basic, meme_style, meme_with_text_style, brain_rot

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--design', required=True)
    
    # New Arguments for Advanced Designs
    parser.add_argument('--top_text', default="WAIT FOR IT") 
    parser.add_argument('--bottom_text', default="🤯🤯🤯") 
    parser.add_argument('--bottom_url', default="") # For Brain-Rot gameplay
    
    args = parser.parse_args()

    print(f"Starting job: {args.url} | Design: {args.design}")

    # 1. Download Main Video
    print("Downloading main video...")
    subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-o", "input.mp4", args.url], check=True)

    # 2. Download Bottom Video (ONLY if Brain-Rot design is selected)
    if args.design == 'brain_rot' and args.bottom_url:
        print("Downloading bottom gameplay video...")
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", "bottom.mp4", args.bottom_url], check=True)

    # 3. Route to the correct design specialist
    input_file = "input.mp4"
    output_file = "output.mp4"

    if args.design == 'crop':
        crop_basic.render(input_file, output_file, args.start, args.end, args)
    elif args.design == 'meme':
        meme_style.render(input_file, output_file, args.start, args.end, args)
    elif args.design == 'meme_text':
        meme_with_text_style.render(input_file, output_file, args.start, args.end, args)
    elif args.design == 'brain_rot':
        brain_rot.render(input_file, output_file, args.start, args.end, args)
    else:
        print(f"Unknown design '{args.design}'. Defaulting to basic crop.")
        crop_basic.render(input_file, output_file, args.start, args.end, args)

if __name__ == "__main__":
    main()
