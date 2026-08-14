import subprocess

def render(input_file, output_file, start, end, args):
    print("Applying Basic Crop Design...")
    
    # Safely scale to cover 1080x1920 then center-crop, working on ANY input resolution
    vf_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    
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
