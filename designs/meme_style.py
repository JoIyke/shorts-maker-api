import subprocess

def render(input_file, output_file, start, end, args):
    print("Applying Classic White Meme Design (No Text)...")
    
    # 1. Scale/crop video to 1080x1080 square
    # 2. Pad to 1080x1920 vertical canvas with WHITE background
    # 3. Position the square video at Y=420 (centered vertically)
    vf_filter = (
        "scale=1080:1080:force_original_aspect_ratio=increase,"
        "crop=1080:1080,"
        "pad=1080:1920:0:420:white"
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
