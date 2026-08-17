import random
import subprocess
import json
import os
from utils import captions

VIBRANT_TRANSITIONS = [
    'slideleft', 'slideright', 'circlecrop', 
    'wipeleft', 'wiperight', 'radial', 
    'smoothleft', 'fade', 'dissolve'
]

PROGRESS_COLORS = ['yellow', 'cyan', 'magenta', 'red', 'green', 'white']

def has_audio_stream(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", file_path]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        streams = json.loads(res.stdout).get("streams", [])
        return any(s.get("codec_type") == "audio" for s in streams)
    except Exception:
        return False

def stitch_with_transitions(segment_files, segment_durations, transition_type="random", output_file="stitched_master.mp4"):
    if len(segment_files) == 1:
        os.rename(segment_files[0], output_file)
        return output_file

    if transition_type == 'none':
        concat_list = "concat_list.txt"
        with open(concat_list, "w") as f:
            for s in segment_files:
                f.write(f"file '{s}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_file], check=True)
        return output_file

    has_audio = has_audio_stream(segment_files[0])
    trans_dur = 0.4
    inputs = []
    for f in segment_files:
        inputs.extend(["-i", f])

    v_filter = ""
    a_filter = ""
    cumulative_offset = segment_durations[0] - trans_dur

    # FIXED: Random transition chosen PER CUT
    for i in range(1, len(segment_files)):
        current_t = random.choice(VIBRANT_TRANSITIONS) if transition_type == 'random' else transition_type
        print(f"Cut {i}: Applying '{current_t}' transition...")

        v_in1 = "[0:v]" if i == 1 else f"[v{i-1}]"
        v_in2 = f"[{i}:v]"
        v_out = f"[v{i}]" if i < len(segment_files) - 1 else "[vout]"
        
        v_filter += f"{v_in1}{v_in2}xfade=transition={current_t}:duration={trans_dur}:offset={cumulative_offset:.2f}{v_out};"

        if has_audio:
            a_in1 = "[0:a]" if i == 1 else f"[a{i-1}]"
            a_in2 = f"[{i}:a]"
            a_out = f"[a{i}]" if i < len(segment_files) - 1 else "[aout]"
            a_filter += f"{a_in1}{a_in2}acrossfade=d={trans_dur}{a_out};"

        if i < len(segment_files) - 1:
            cumulative_offset += (segment_durations[i] - trans_dur)

    filter_complex = v_filter + a_filter

    ffmpeg_cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-c:v", "libx264"
    ]
    if has_audio:
        ffmpeg_cmd.extend(["-map", "[aout]", "-c:a", "aac"])
    ffmpeg_cmd.append(output_file)

    subprocess.run(ffmpeg_cmd, check=True)
    return output_file


def apply_post_processing(input_video, output_video, payload, total_duration, res_w=1080, res_h=1920):
    """Applies glowing animations and captions via complex filters."""
    filters = []
    stream_idx = "[0:v]"

    # 1. Setup Progress Bar Animation
    prog_config = payload.get('progress_bar', True)
    if isinstance(prog_config, bool):
        prog_config = {'enabled': prog_config}

    if prog_config and prog_config.get('enabled', True):
        style = prog_config.get('style', 'perimeter')
        color = prog_config.get('color', 'random')
        if color == 'random':
            color = random.choice(PROGRESS_COLORS)
            print(f"Random Glow Color Selected: {color}")
        color = color.lower()

        color_map = {
            'yellow': 'yellow@0.95', 'cyan': 'cyan@0.95', 'magenta': 'magenta@0.95',
            'red': 'red@0.95', 'green': 'green@0.95', 'white': 'white@0.95'
        }
        core_c = color_map.get(color, 'yellow@0.95')

        # FIXED: Slide solid blocks across the screen for flawless animation
        if style == 'perimeter':
            p_total = 2 * (res_w + res_h)
            t_top = total_duration * res_w / p_total
            t_right = total_duration * res_h / p_total
            t_bot = total_duration * res_w / p_total
            t_left = total_duration * res_h / p_total
            thick = 14
            
            filters.append(f"color=c={core_c}:s={res_w}x{thick} [c_top]")
            filters.append(f"color=c={core_c}:s={thick}x{res_h} [c_right]")
            filters.append(f"color=c={core_c}:s={res_w}x{thick} [c_bot]")
            filters.append(f"color=c={core_c}:s={thick}x{res_h} [c_left]")
            
            # Top edge (Grows Left to Right)
            x_top = f"-{res_w}+{res_w}*min(t,{t_top})/{t_top}"
            filters.append(f"{stream_idx}[c_top]overlay=x='{x_top}':y=0:shortest=1 [v1]")
            
            # Right edge (Grows Top to Bottom)
            x_right = f"{res_w-thick}"
            y_right = f"-{res_h}+{res_h}*min(max(t-{t_top},0),{t_right})/{t_right}"
            filters.append(f"[v1][c_right]overlay=x='{x_right}':y='{y_right}':shortest=1 [v2]")
            
            # Bottom edge (Grows Right to Left)
            x_bot = f"{res_w}-{res_w}*min(max(t-{t_top}-{t_right},0),{t_bot})/{t_bot}"
            y_bot = f"{res_h-thick}"
            filters.append(f"[v2][c_bot]overlay=x='{x_bot}':y='{y_bot}':shortest=1 [v3]")
            
            # Left edge (Grows Bottom to Top)
            x_left = "0"
            y_left = f"{res_h}-{res_h}*min(max(t-{t_top}-{t_right}-{t_bot},0),{t_left})/{t_left}"
            filters.append(f"[v3][c_left]overlay=x='{x_left}':y='{y_left}':shortest=1 [v_prog]")
            
            stream_idx = "[v_prog]"
            
        else: # neon_bottom
            filters.append(f"color=c={core_c}:s={res_w}x12 [c_bot]")
            x_bot = f"-{res_w}+{res_w}*t/{total_duration}"
            filters.append(f"{stream_idx}[c_bot]overlay=x='{x_bot}':y={res_h-12}:shortest=1 [v_prog]")
            stream_idx = "[v_prog]"

    # 2. Add Subtitles
    raw_words = payload.get('words', [])
    if raw_words:
        sub_file = captions.generate_ass_subtitles(raw_words, caption_style=payload.get('caption_style', 'hormozi'), res_x=res_w, res_y=res_h)
        if sub_file and os.path.exists(sub_file):
            # ASS filter can be chained as a simple video filter
            filters.append(f"{stream_idx}ass={sub_file} [vout]")
            stream_idx = "[vout]"

    if not filters:
        os.rename(input_video, output_video)
        return output_video

    # If the last filter didn't map to [vout], we just map to whatever the last stream_idx is
    filter_complex = ";".join(filters)
    print(f"Applying Post-Processing Engine...")
    
    cmd = [
        "ffmpeg", "-y", "-i", input_video,
        "-filter_complex", filter_complex,
        "-map", stream_idx, "-map", "0:a?",
        "-c:v", "libx264", "-c:a", "copy", output_file
    ]
    subprocess.run(cmd, check=True)
    return output_video
