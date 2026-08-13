import subprocess

def render(input_file, output_file, start, end, args):
    print("Applying Brain-Rot Split Screen Design...")
    
    # -stream_loop -1 loops the bottom video forever
    # filter_complex maps the two videos:
    # [0:v] is the main video. We crop it to 1080x960.
    # [1:v] is the bottom video. We crop it to 1080x960.
    # [vtop][vbot]vstack stacks them vertically to make 1080x1920.
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-to", str(end),
        "-i", input_file,
        "-stream_loop", "-1", 
        "-i", args.bottom_file",
        "-filter_complex", 
        "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[vtop];"
        "[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[vbot];"
        "[vtop][vbot]vstack[vout]",
        "-map", "[vout]", # Use the stacked video
        "-map", "0:a",    # Use ONLY the audio from the main video (Input 0)
        "-c:a", "aac",
        "-shortest",      # Cut the video when the main video's timeframe ends
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
