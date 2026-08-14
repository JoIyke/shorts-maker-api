import subprocess
import textwrap

def render(input_file, output_file, start, end, args):
    raw_top = str(args.get('top_text', 'WHEN YOU FINALLY FIX THE BUG')).replace("'", "").replace(":", " -")
    raw_bottom = str(args.get('bottom_text', 'AND IT WORKS ON THE FIRST TRY 😭')).replace("'", "").replace(":", " -")
    
    # Auto-wrap text every 25 characters so long sentences break into clean lines
    wrapped_top = "\n".join(textwrap.wrap(raw_top, width=24))
    wrapped_bottom = "\n".join(textwrap.wrap(raw_bottom, width=24))
    
    print(f"Applying Meme With Text Design...\nTop:\n{wrapped_top}\nBottom:\n{wrapped_bottom}")

    # Filter breakdown:
    # 1. Scale & Crop video to 1080x1080 square
    # 2. Pad onto a 1080x1920 WHITE vertical canvas (centered at y=420)
    # 3. Draw black text in top white margin (y=120)
    # 4. Draw black text in bottom white margin (y=1560)
    vf_filter = (
        "scale=1080:1080:force_original_aspect_ratio=increase,"
        "crop=1080:1080,"
        "pad=1080:1920:0:420:white,"
        f"drawtext=fontfile=font.ttf:text='{wrapped_top}':fontcolor=black:fontsize=65:line_spacing=15:x=(w-text_w)/2:y=120,"
        f"drawtext=fontfile=font.ttf:text='{wrapped_bottom}':fontcolor=black:fontsize=65:line_spacing=15:x=(w-text_w)/2:y=1560"
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
