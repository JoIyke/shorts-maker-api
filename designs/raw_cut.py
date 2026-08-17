import subprocess
import json

def has_video_stream(input_file):
    """Checks if the file contains a video track or is pure audio."""
    try:
        cmd = [
            "ffprobe", "-v", "error", 
            "-show_entries", "stream=codec_type", 
            "-of", "json", input_file
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        streams = json.loads(res.stdout).get("streams", [])
        return any(s.get("codec_type") == "video" for s in streams)
    except Exception:
        return True

def render(input_file, output_file, start, end, args):
    print(f"Applying Raw Cut (No styling)... {start}s to {end}s")
    
    is_video = has_video_stream(input_file)

    if is_video:
        # Video cut: re-encode for frame-accurate cuts without altering resolution
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", input_file,
            "-c:v", "libx264",
            "-c:a", "aac",
            output_file
        ]
    else:
        # Audio-only cut: preserve clean audio stream
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", input_file,
            "-c:a", "aac",
            output_file
        ]

    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Segment cut complete: {output_file}")
