import subprocess
import json

def has_real_video(input_file):
    """Checks if the file has a moving video track, completely ignoring album art."""
    try:
        cmd = [
            "ffprobe", "-v", "error", 
            "-show_entries", "stream=codec_name,codec_type", 
            "-of", "json", input_file
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        streams = json.loads(res.stdout).get("streams", [])
        for s in streams:
            # If there is a video stream that IS NOT album art, it's a real video
            if s.get("codec_type") == "video" and s.get("codec_name") not in ["mjpeg", "png", "bmp"]:
                return True
        return False
    except Exception:
        return False

def render(input_file, output_file, start, end, args):
    print(f"Applying Raw Cut (No styling)... {start}s to {end}s")
    
    is_video = has_real_video(input_file)

    if is_video:
        # Video cut: explicit mapping ensures audio codecs don't encode video tracks
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", input_file,
            "-map", "0:v?", "-map", "0:a?",
            "-c:v", "libx264",
            "-c:a", "aac",
            output_file
        ]
    else:
        # Audio-only cut
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", input_file,
            "-map", "0:a?",
            "-c:a", "aac",
            output_file
        ]

    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Segment cut complete: {output_file}")
