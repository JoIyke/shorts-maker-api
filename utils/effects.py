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

def apply_post_processing(input_video, output_video, payload, total_duration, res_w=1080, res_h=1920, logo_file=None):
    """Applies flawless glowing animations, Logo Rider, and captions."""
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
        color = color.lower()

        color_map = {
            'yellow': 'yellow@0.95', 'cyan': 'cyan@0.95', 'magenta': 'magenta@0.95',
            'red': 'red@0.95', 'green': 'green@0.95', 'white': 'white@0.95'
        }
        core_c = color_map.get(color, 'yellow@0.95')

        if style == 'perimeter':
            p_total = 2 * (res_w + res_h)
            thick = 14
            
            d_expr = f"({p_total}*min(t,{total_duration})/{total_duration})"
            
            # FIXED: Added :d={total_duration} so they don't generate infinite frames!
            filters.append(f"color=c={core_c}:s={res_w}x{thick}:d={total_duration} [c_top]")
            filters.append(f"color=c={core_c}:s={thick}x{res_h}:d={total_duration} [c_right]")
            filters.append(f"color=c={core_c}:s={res_w}x{thick}:d={total_duration} [c_bot]")
            filters.append(f"color=c={core_c}:s={thick}x{res_h}:d={total_duration} [c_left]")
            
            x_top = f"-{res_w}+clip({d_expr},0,{res_w})"
            filters.append(f"{stream_idx}[c_top]overlay=x='{x_top}':y=0:shortest=1 [v1]")
            
            y_right = f"-{res_h}+clip({d_expr}-{res_w},0,{res_h})"
            filters.append(f"[v1][c_right]overlay=x={res_w-thick}:y='{y_right}':shortest=1 [v2]")
            
            x_bot = f"{res_w}-clip({d_expr}-{res_w}-{res_h},0,{res_w})"
            filters.append(f"[v2][c_bot]overlay=x='{x_bot}':y={res_h-thick}:shortest=1 [v3]")
            
            y_left = f"{res_h}-clip({d_expr}-2*{res_w}-{res_h},0,{res_h})"
            filters.append(f"[v3][c_left]overlay=x=0:y='{y_left}':shortest=1 [v_prog]")
            stream_idx = "[v_prog]"

            # THE LOGO RIDER
            if logo_file:
                logo_size = 90
                offset = logo_size / 2
                filters.append(f"[1:v]scale={logo_size}:{logo_size},format=rgba [logo]")
                
                logo_x = f"clip({d_expr},0,{res_w})-clip({d_expr}-{res_w}-{res_h},0,{res_w})"
                logo_y = f"clip({d_expr}-{res_w},0,{res_h})-clip({d_expr}-2*{res_w}-{res_h},0,{res_h})"
                
                filters.append(f"{stream_idx}[logo]overlay=x='({logo_x})-{offset}':y='({logo_y})-{offset}':shortest=1 [v_logo]")
                stream_idx = "[v_logo]"

        else: # neon_bottom or neon_top
            # FIXED: Added :d={total_duration}
            filters.append(f"color=c={core_c}:s={res_w}x12:d={total_duration} [c_bot]")
            x_bot = f"-{res_w}+{res_w}*min(t,{total_duration})/{total_duration}"
            y_pos = res_h-12 if style == 'neon_bottom' else 0
            filters.append(f"{stream_idx}[c_bot]overlay=x='{x_bot}':y={y_pos}:shortest=1 [v_prog]")
            stream_idx = "[v_prog]"

    # 2. Add Subtitles
    raw_words = payload.get('words', [])
    if raw_words:
        sub_file = captions.generate_ass_subtitles(raw_words, caption_style=payload.get('caption_style', 'hormozi'), res_x=res_w, res_y=res_h)
        if sub_file and os.path.exists(sub_file):
            filters.append(f"{stream_idx}ass={sub_file} [vout]")
            stream_idx = "[vout]"

    if not filters:
        os.rename(input_video, output_video)
        return output_video

    filter_complex = ";".join(filters)
    print(f"Applying Post-Processing Engine...")
    
    cmd = ["ffmpeg", "-y", "-i", input_video]
    
    if logo_file:
        # FIXED: Tell FFmpeg to loop the static logo image so it lasts the whole video!
        cmd.extend(["-loop", "1", "-t", str(total_duration), "-i", logo_file]) 
        
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", stream_idx, "-map", "0:a?",
        "-c:v", "libx264", "-c:a", "copy", 
        "-shortest", # FIXED: Failsafe to force stop when the audio/video ends
        output_video
    ])
    subprocess.run(cmd, check=True)
    return output_video
