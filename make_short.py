import os
import subprocess
import argparse

# 1. Setup the inputs we will receive from n8n
parser = argparse.ArgumentParser()
parser.add_argument('--url', required=True, help='Link to YouTube or MP4')
parser.add_argument('--start', required=True, help='Start time in seconds')
parser.add_argument('--end', required=True, help='End time in seconds')
parser.add_argument('--design', default='crop', help='crop or meme')
args = parser.parse_args()

print(f"Starting job: {args.url} from {args.start}s to {args.end}s")

# 2. Download the video using yt-dlp (Bulletproof format selection)
print("Downloading video...")
download_cmd = [
    "yt-dlp", 
    # This string safely handles YouTube split streams OR single files like Google Drive
    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", 
    "-o", "input.mp4", 
    args.url
]
subprocess.run(download_cmd, check=True)

# 3. Determine the FFmpeg Design
if args.design == 'crop':
    # This crops the center of the video to 9:16
    vf_filter = "crop=ih*9/16:ih"
elif args.design == 'meme':
    # This makes a square video with black bars on top and bottom
    vf_filter = "scale=1080:-1,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black"
else:
    vf_filter = "crop=ih*9/16:ih"

# 4. Run the FFmpeg command to cut and crop
print("Processing video with FFmpeg...")
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-ss", str(args.start),
    "-to", str(args.end),
    "-i", "input.mp4",
    "-vf", vf_filter,
    "-c:a", "aac",  # Changed from 'copy' to 'aac' so it works safely with Google Drive files
    "output.mp4"
]
subprocess.run(ffmpeg_cmd, check=True)

print("Success! output.mp4 is ready.")
