import os
import subprocess
from utils import captions, effects

def parse_time(val):
    if val is None:
        return 0.0
    val = float(val)
    if val > 10000:
        val = val / 1000.0
    return val

def extract_bounds(clip):
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
    segment_durations = []
    
    # 1. Download Main Video
    subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-o", raw_video, payload['url']], check=True)
    
    if payload.get('design') == 'brain_rot' and payload.get('bottom_url'):
        payload['bottom_file'] = "bottom.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", payload['bottom_file'], payload['bottom_url']], check=True)

    def render_part(start_sec, end_sec, prefix):
        out_name = f"{prefix}_rendered.mp4"
        design_module.render(raw_video, out_name, start_sec, end_sec, payload)
        dur = end_sec - start_sec
        return out_name, dur

    cumulative_offset_ms = 0.0
    adjusted_words = []
    raw_words = payload.get('words', [])

    # A. Hook
    if payload.get('hook'):
        h_start, h_end = extract_bounds(payload['hook'])
        h_file, h_dur = render_part(h_start, h_end, "hook")
        rendered_segments.append(h_file)
        segment_durations.append(h_dur)
        cumulative_offset_ms += (h_dur * 1000)

    # B. Intro
    if payload.get('intro_url'):
        intro_file = "intro_rendered.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", "raw_intro.mp4", payload['intro_url']], check=True)
        subprocess.run(["ffmpeg", "-y", "-i", "raw_intro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", intro_file], check=True)
        rendered_segments.append(intro_file)
        segment_durations.append(3.0)

    # C. Body Clips
    clips = payload.get('clips', [])
    for idx, clip in enumerate(clips):
        c_start, c_end = extract_bounds(clip)
        c_file, c_dur = render_part(c_start, c_end, f"body_{idx}")
        rendered_segments.append(c_file)
        segment_durations.append(c_dur)

        c_start_ms = c_start * 1000.0
        c_end_ms = c_end * 1000.0

        for w in raw_words:
            w_start = float(w['start'])
            w_end = float(w['end'])
            if c_start_ms <= w_start <= c_end_ms:
                relative_start = w_start - c_start_ms
                relative_end = w_end - c_start_ms
                adjusted_words.append({
                    "text": w['text'],
                    "start": int(relative_start + cumulative_offset_ms),
                    "end": int(relative_end + cumulative_offset_ms)
                })

        cumulative_offset_ms += (c_dur * 1000)

    # D. Outro
    if payload.get('outro_url'):
        outro_file = "outro_rendered.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", "raw_outro.mp4", payload['outro_url']], check=True)
        subprocess.run(["ffmpeg", "-y", "-i", "raw_outro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", outro_file], check=True)
        rendered_segments.append(outro_file)
        segment_durations.append(3.0)

# 2. Stitch with Vibrant Transitions (Default: 'random')
    transition_style = payload.get('transition', 'random')
    stitched_file = "stitched_master.mp4"
    effects.stitch_with_transitions(rendered_segments, segment_durations, transition_type=transition_style, output_file=stitched_file)

    # 3. Post-Processing: Progress Bar Perimeter & Captions
    total_video_duration = sum(segment_durations)
    final_output = "output.mp4"
    
    effects.apply_post_processing(stitched_file, final_output, payload, total_video_duration)

    print("Pipeline Complete! Video ready.")
