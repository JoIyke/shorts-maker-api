import os
import subprocess
from utils import captions

def parse_time(val):
    """Safely converts timestamps to seconds, handling milliseconds if needed."""
    if val is None:
        return 0.0
    val = float(val)
    # If time is greater than 10,000, it's in milliseconds (e.g., 12000ms = 12.0s)
    if val > 10000:
        val = val / 1000.0
    return val

def extract_bounds(clip):
    """Extracts start and end times from any dict format or list."""
    if isinstance(clip, dict):
        s = clip.get('start') if clip.get('start') is not None else (clip.get('start_time') or clip.get('start_sec') or clip.get('begin'))
        e = clip.get('end') if clip.get('end') is not None else (clip.get('end_time') or clip.get('end_sec') or clip.get('finish'))
    elif isinstance(clip, (list, tuple)):
        s, e = clip[0], clip[1]
    else:
        s, e = 0, 0
    return parse_time(s), parse_time(e)

def process_timeline(payload, design_module):
    raw_video = "main_input.mp4"
    rendered_segments = []
    
    # 1. Download Main Video (using YouTube datacenter bypass flags)
    print(f"Downloading main video from: {payload['url']}")
    subprocess.run([
        "yt-dlp",
        "--extractor-args", "youtube:player_client=android,web",
        "--no-check-certificates",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", raw_video,
        payload['url']
    ], check=True)
    
    # Download bottom gameplay video if brain_rot design is selected
    if payload.get('design') == 'brain_rot' and payload.get('bottom_url'):
        payload['bottom_file'] = "bottom.mp4"
        print(f"Downloading brain-rot bottom video from: {payload['bottom_url']}")
        subprocess.run([
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android,web",
            "--no-check-certificates",
            "-f", "bestvideo[ext=mp4]/best",
            "-o", payload['bottom_file'],
            payload['bottom_url']
        ], check=True)

    def render_part(start_sec, end_sec, prefix):
        out_name = f"{prefix}_rendered.mp4"
        design_module.render(raw_video, out_name, start_sec, end_sec, payload)
        return out_name, (end_sec - start_sec)

    cumulative_offset_ms = 0.0
    adjusted_words = []
    raw_words = payload.get('words', [])

    # A. Process Hook Segment (If provided)
    if payload.get('hook'):
        print("Processing Hook segment...")
        h_start, h_end = extract_bounds(payload['hook'])
        h_file, h_dur = render_part(h_start, h_end, "hook")
