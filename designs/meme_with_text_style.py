import subprocess

def render(input_file, output_file, start, end, args):
    top_text = str(args.get('top_text', 'WAIT FOR IT')).replace("'", "")
    bottom_text = str(args.get('bottom_text', '🤯')).replace("'", "")
    
    print(f"Applying Meme With Text Design... Top: {top_text} | Bottom: {bottom_text}")

    vf_filter = (
        "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black,"
        f"drawtext=fontfile=font.ttf:text='{top_text}':fontcolor=white:fontsize=75:borderw=3:bordercolor=black:x=(w-text_w)/2:y=80,"
        f"drawtext=fontfile=font.ttf:text='{bottom_text}':fontcolor=white:fontsize=75:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-text_h-80"
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
