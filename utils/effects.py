import random
import subprocess
import json
import os

VIBRANT_TRANSITIONS = [
    'slideleft', 'slideright', 'circlecrop', 
    'wipeleft', 'wiperight', 'radial', 
    'smoothleft', 'fade', 'dissolve'
]

PROGRESS_COLORS = ['yellow', 'cyan', 'magenta', 'red', 'green', 'white']

def has_audio_stream(file_path):
    """Checks if a media file contains an audio stream."""
    try:
        cmd = [
            "ffprobe", "-v", "error", 
            "-show_entries", "stream=codec_type", 
            "-of", "json", file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        streams = json.loads(res.stdout).get("streams", [])
        return any(s.get("codec_type") == "audio" for s in streams)
    except Exception:
        return False

def get_transition_choice(requested_transition):
    """Returns a valid transition. If 'random' or missing, picks randomly."""
    if not requested_transition or requested_transition == 'random':
        chosen = random.choice(VIBRANT_TRANSITIONS)
        print(f"Random Transition Selected: {chosen}")
        return chosen
    return requested_transition

def stitch_with_transitions(segment_files, segment_durations, transition_type="random", output_file="stitched_master.mp4"):
    """Stitches video segments with xfade (and acrossfade if audio exists)."""
    if len(segment_files) == 1:
        os.rename(segment_files[0], output_file)
        return output_file

    t_choice = get_transition_choice(transition_type)

    if t_choice == 'none':
        concat_list = "concat_list.txt"
        with open(concat_list, "w") as f:
            for s in segment_files:
                f.write(f"file '{s}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_file], check=True)
        return output_file

    # Check if inputs have audio
    has_audio = has_audio_stream(segment_files[0])

    trans_dur = 0.4  # 0.4s transition duration
    inputs = []
    for f in segment_files:
        inputs.extend(["-i", f])

    v_filter = ""
    a_filter = ""
    cumulative_offset = segment_durations[0] - trans_dur

    for i in range(1, len(segment_files)):
        v_in1 = "[0:v]" if i == 1 else f"[v{i-1}]"
        v_in2 = f"[{i}:v]"
        v_out = f"[v{i}]" if i < len(segment_files) - 1 else "[vout]"
        
        v_filter += f"{v_in1}{v_in2}xfade=transition={t_choice}:duration={trans_dur}:offset={cumulative_offset:.2f}{v_out};"

        if has_audio:
            a_in1 = "[0:a]" if i == 1 else f"[a{i-1}]"
            a_in2 = f"[{i}:a]"
            a_out = f"[a{i}]" if i < len(segment_files) - 1 else "[aout]"
            a_filter += f"{a_in1}{a_in2}acrossfade=d={trans_dur}{a_out};"

        if i < len(segment_files) - 1:
            cumulative_offset += (segment_durations[i] - trans_dur)

    filter_complex = v_filter + a_filter

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        output_file
    ]

    # If inputs had audio, map the audio output
    if has_audio:
        ffmpeg_cmd.insert(-2, "-map")
        ffmpeg_cmd.insert(-2, "[aout]")
        ffmpeg_cmd.insert(-2, "-c:a")
        ffmpeg_cmd.insert(-2, "aac")

    subprocess.run(ffmpeg_cmd, check=True)
    return output_file

def build_progress_bar_filter(total_duration, config, res_w=1080, res_h=1920):
    """Generates FFmpeg drawbox filter with 'perimeter' and 'random' color defaults."""
    if not config:
        return None

    if isinstance(config, bool):
        if not config:
            return None
        config = {'enabled': True}

    if not config.get('enabled', True):
        return None

    style = config.get('style') or 'perimeter'
    color = config.get('color') or 'random'

    if color == 'random':
        color = random.choice(PROGRESS_COLORS)
        print(f"Random Progress Bar Color Selected: {color}")
    else:
        color = color.lower()

    glow = config.get('glow', True)

    color_map = {
        'yellow': ('yellow@0.95', 'yellow@0.35'),
        'cyan': ('cyan@0.95', 'cyan@0.35'),
        'magenta': ('magenta@0.95', 'magenta@0.35'),
        'red': ('red@0.95', 'red@0.35'),
        'green': ('green@0.95', 'green@0.35'),
        'white': ('white@0.95', 'white@0.35')
    }
    core_c, glow_c = color_map.get(color, ('yellow@0.95', 'yellow@0.35'))

    # Option 1: 4-Edge Perimeter Tracer (DEFAULT)
    if style == 'perimeter':
        p_total = 2 * (res_w + res_h)
        thick = 12
        t_top = f"drawbox=x=0:y=0:w='min({res_w}, {p_total}*t/{total_duration})':h={thick}:color={core_c}:t=fill"
        t_right = f"drawbox=x={res_w-thick}:y=0:w={thick}:h='max(0, min({res_h}, ({p_total}*t/{total_duration})-{res_w}))':color={core_c}:t=fill"
        t_bot = f"drawbox=x='max(0, {res_w}-max(0, ({p_total}*t/{total_duration})-{res_w+res_h}))':y={res_h-thick}:w='min({res_w}, max(0, ({p_total}*t/{total_duration})-{res_w+res_h}))':h={thick}:color={core_c}:t=fill"
        t_left = f"drawbox=x=0:y='max(0, {res_h}-max(0, ({p_total}*t/{total_duration})-{2*res_w+res_h}))':w={thick}:h='min({res_h}, max(0, ({p_total}*t/{total_duration})-{2*res_w+res_h}))':color={core_c}:t=fill"
        return f"{t_top},{t_right},{t_bot},{t_left}"

    # Option 2: Neon Bottom Laser Bar
    elif style == 'neon_bottom':
        filters = []
        if glow:
            filters.append(f"drawbox=x=0:y={res_h-22}:w='{res_w}*t/{total_duration}':h=22:color={glow_c}:t=fill")
        filters.append(f"drawbox=x=0:y={res_h-12}:w='{res_w}*t/{total_duration}':h=12:color={core_c}:t=fill")
        return ",".join(filters)

    # Option 3: Neon Top Laser Bar
    elif style == 'neon_top':
        filters = []
        if glow:
            filters.append(f"drawbox=x=0:y=0:w='{res_w}*t/{total_duration}':h=22:color={glow_c}:t=fill")
        filters.append(f"drawbox=x=0:y=0:w='{res_w}*t/{total_duration}':h=12:color={core_c}:t=fill")
        return ",".join(filters)

    return None
