import subprocess

def render(input_file, output_file, start, end, args):
    print("Applying Basic Crop Design...")
    vf_filter = "crop=ih*9/16:ih"
    
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
