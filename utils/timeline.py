import os
import subprocess
from utils import captions, effects

def parse_time(val):
    if val is None:
        return 0.0
    val = float(val)
    if val > 10000:
        val /= 1000.0
    return val

def extract_bounds(clip):
    if isinstance(clip, dict):
        s = clip.get('start', clip.get('start_time', clip.get('start_sec', clip.get('begin', 0))))
        e = clip.get('end', clip.get('end_time', clip.get('end_sec', clip.get('finish', 0))))
    elif isinstance(clip, (list, tuple)):
        s, e = clip[0], clip[1]
    else:
        s, e = 0, 0
    return parse_time(s), parse_time(e)

def process_timeline(payload, design_module):
    raw_video = "main_input.mp4"
    rendered_segments = []
    segment_durations = []
    
    design_name = payload.get('design', 'crop')

    # 1. Download Main Media
    subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-o", raw_video, payload['url']], check=True)
    
    if design_name == 'brain_rot' and payload.get('bottom_url'):
        payload['bottom_file'] = "bottom.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", payload['bottom_file'], payload['bottom_url']], check=True)

    def render_part(start_sec, end_sec, prefix):
        out_name = f"{prefix}_rendered.mp4"
        design_module.render(raw_video, out_name, start_sec, end_sec, payload)
        return out_name, (end_sec - start_sec)

    adjusted_words = []
    raw_words = payload.get('words', [])
    
    transition_style = payload.get('transition', 'random')
    if design_name == 'raw_cut':
        transition_style = 'none'
        
    trans_dur = 0.0 if transition_style == 'none' else 0.4
    current_timeline_ms = 0.0

    def append_segment(file_name, dur, c_start=None, c_end=None):
        nonlocal current_timeline_ms
        # Subtract transition overlap if this isn't the very first clip
        if len(rendered_segments) > 0:
            current_timeline_ms -= (trans_dur * 1000.0)
        
        rendered_segments.append(file_name)
        segment_durations.append(dur)
        
        # Pull words strictly belonging to this clip and offset them
        if c_start is not None and c_end is not None:
            c_start_ms = c_start * 1000.0
            c_end_ms = c_end * 1000.0
            for w in raw_words:
                w_start = float(w['start'])
                w_end = float(w['end'])
                if c_start_ms <= w_start < c_end_ms:
                    rel_s = w_start - c_start_ms
                    rel_e = w_end - c_start_ms
                    adjusted_words.append({
                        "text": w['text'],
                        "start": int(rel_s + current_timeline_ms),
                        "end": int(rel_e + current_timeline_ms)
                    })
        
        current_timeline_ms += (dur * 1000.0)

    # A. Hook
    if payload.get('hook'):
        h_start, h_end = extract_bounds(payload['hook'])
        h_file, h_dur = render_part(h_start, h_end, "hook")
        append_segment(h_file, h_dur, h_start, h_end)

    # B. Intro
    if payload.get('intro_url'):
        intro_file = "intro_rendered.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", "raw_intro.mp4", payload['intro_url']], check=True)
        subprocess.run(["ffmpeg", "-y", "-i", "raw_intro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", intro_file], check=True)
        append_segment(intro_file, 3.0)

    # C. Body Clips
    clips = payload.get('clips', [])
    for idx, clip in enumerate(clips):
        c_start, c_end = extract_bounds(clip)
        c_file, c_dur = render_part(c_start, c_end, f"body_{idx}")
        append_segment(c_file, c_dur, c_start, c_end)

    # D. Outro
    if payload.get('outro_url'):
        outro_file = "outro_rendered.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", "raw_outro.mp4", payload['outro_url']], check=True)
        subprocess.run(["ffmpeg", "-y", "-i", "raw_outro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", outro_file], check=True)
        append_segment(outro_file, 3.0)

    # 2. Stitch Segments
    stitched_file = "stitched_master.mp4"
    effects.stitch_with_transitions(rendered_segments, segment_durations, transition_type=transition_style, output_file=stitched_file)

    # 3. Post-Processing
    final_output = "output.mp4"

    if design_name == 'raw_cut':
        os.rename(stitched_file, final_output)
        print("Raw Cut Pipeline Complete! Media ready.")
    else:
        # Use exact adjusted time!
        total_video_duration = current_timeline_ms / 1000.0
        # FIX: Pass the newly shifted adjusted_words down into the final processing!
        effects.apply_post_processing(stitched_file, final_output, payload, total_video_duration, adjusted_words=adjusted_words)
        print("Pipeline Complete! Video ready.")
