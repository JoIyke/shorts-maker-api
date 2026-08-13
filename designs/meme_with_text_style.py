import subprocess

def render(input_file, output_file, start, end, args):
    print(f"Applying Meme With Text Design... Top: {args.top_text} | Bottom: {args.bottom_text}")
    
    # 1. Pad to square, place video in center.
    # 2. Draw Top Text
    # 3. Draw Bottom Text
    # Note: We are expecting 'font.ttf' to be downloaded by GitHub Actions
    
    vf_filter = (
        "scale=1080:-1,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black,"
        f"drawtext=fontfile=font.ttf:text='{args.top_text}':fontcolor=white:fontsize=85:borderw=3:bordercolor=black:x=(w-text_w)/2:y=80,"
        f"drawtext=fontfile=font.ttf:text='{args.bottom_text}':fontcolor=white:fontsize=85:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-text_h-80"
    )
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-to", str(end),
        "-i", input_file,
        "-vf", vf_filter,
        "-c:a", "aac",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
