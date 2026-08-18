import random
import subprocess
import json
import os
import urllib.request
from utils import captions, emojis

VIBRANT_TRANSITIONS = [
    'slideleft', 'slideright', 'circlecrop', 
    'wipeleft', 'wiperight', 'radial', 
    'smoothleft', 'fade', 'dissolve'
]

PROGRESS_COLORS = ['yellow', 'cyan', 'magenta', 'red', 'green', 'white']

WAVEFORM_STYLES = ['bars_neon', 'waves_cyan', 'waves_fire', 'spectrum_dots', 'ahistogram_glow']

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
    for i in range(len(segment_files)):
        v_filter += f"[{i}:v]setpts=PTS-STARTPTS[vpts{i}];"

    a_filter = ""
    cumulative_offset = segment_durations[0] - trans_dur

    for i in range(1, len(segment_files)):
        current_t = random.choice(VIBRANT_TRANSITIONS) if transition_type == 'random' else transition_type
        print(f"Cut {i}: Applying '{current_t}' transition...")

        v_in1 = "[vpts0]" if i == 1 else f"[v{i-1}]"
        v_in2 = f"[vpts{i}]"
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

def prepare_logo(logo_url, size=70):
    if not logo_url:
        return None
    try:
        raw_logo = "temp_raw_logo.png"
        formatted_logo = "formatted_logo.png"
        req = urllib.request.Request(logo_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(raw_logo, 'wb') as out_file:
            out_file.write(response.read())

        cmd = [
            "ffmpeg", "-y", "-i", raw_logo,
            "-vf", f"scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=black@0",
            "-pix_fmt", "rgba", formatted_logo
        ]
        subprocess.run(cmd, check=True)
        return formatted_logo
    except Exception as e:
        print(f"Warning: Failed to process logo ({e}).")
        return None

def build_waveform_filter(style="random", width=460, height=240):
    """Generates dramatic, high-energy voice-reactive audio visualizers."""
    if not style or style == "random":
        style = random.choice(WAVEFORM_STYLES)
        print(f"Random Dramatic Waveform Style Selected: '{style}'")
    else:
        style = style.lower()

    # Pre-amp: Boosts audio feeding the visualizer by 3.5x for massive, punchy bounce
    pre_amp = "volume=1.5,"

    if style == 'waves_cyan':
        # Glowing double-amplitude voice envelope
        wv_gen = f"{pre_amp}showwaves=s={width}x{height}:mode=p2p:scale=cbrt:draw=full:colors=0x00FFFF@0.95|0xFFFFFF@1.0"
    elif style == 'waves_fire':
        # Fiery neon peak envelope
        wv_gen = f"{pre_amp}showwaves=s={width}x{height}:mode=p2p:scale=cbrt:draw=full:colors=0xFF3300@0.95|0xFFFF00@1.0"
    elif style == 'spectrum_dots':
        # Voice-focused floating particle dots
        wv_gen = f"{pre_amp}showfreqs=s={width}x{height}:mode=dot:fscale=log:fmin=80:fmax=4200:ascale=cbrt:colors=0x14FF39|0x00FFFF"
    elif style == 'ahistogram_glow':
        # High-intensity spectral cloud
        wv_gen = f"{pre_amp}showwavespeaks=s={width}x{height}:mode=p2p:color=0x00FFFF|0xFF00FF"
    else: # bars_neon (default)
        # Voice-focused equalizer bars spanning the full width
        wv_gen = f"{pre_amp}showfreqs=s={width}x{height}:mode=bar:fscale=log:fmin=80:fmax=4200:ascale=cbrt:colors=0x00FFFF|0xFF00FF"

    return f"{wv_gen},format=rgba,colorkey=0x000000:0.1:0.1[wv]"

def apply_post_processing(input_video, output_video, payload, total_duration, res_w=1080, res_h=1920):
    filters = []
    stream_idx = "[0:v]"
    extra_inputs = []

    # 1. Setup Progress Bar Animation
    prog_config = payload.get('progress_bar', True)
    if isinstance(prog_config, bool):
        prog_config = {'enabled': prog_config}

    style = 'perimeter'
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
        anim_dur = total_duration

        if style == 'perimeter':
            p_total = 2 * (res_w + res_h)
            t_top = anim_dur * res_w / p_total
            t_right = anim_dur * res_h / p_total
            t_bot = anim_dur * res_w / p_total
            t_left = anim_dur * res_h / p_total
            thick = 14
            
            filters.append(f"color=c={core_c}:s={res_w}x{thick}:r=30:d={total_duration} [c_top]")
            filters.append(f"color=c={core_c}:s={thick}x{res_h}:r=30:d={total_duration} [c_right]")
            filters.append(f"color=c={core_c}:s={res_w}x{thick}:r=30:d={total_duration} [c_bot]")
            filters.append(f"color=c={core_c}:s={thick}x{res_h}:r=30:d={total_duration} [c_left]")
            
            x_top = f"-{res_w}+{res_w}*min(t,{t_top})/{t_top}"
            filters.append(f"{stream_idx}[c_top]overlay=x='{x_top}':y=0:eof_action=repeat [v1]")
            
            x_right = f"{res_w-thick}"
            y_right = f"-{res_h}+{res_h}*min(max(t-{t_top},0),{t_right})/{t_right}"
            filters.append(f"[v1][c_right]overlay=x='{x_right}':y='{y_right}':eof_action=repeat [v2]")
            
            x_bot = f"{res_w}-{res_w}*min(max(t-{t_top}-{t_right},0),{t_bot})/{t_bot}"
            y_bot = f"{res_h-thick}"
            filters.append(f"[v2][c_bot]overlay=x='{x_bot}':y='{y_bot}':eof_action=repeat [v3]")
            
            x_left = "0"
            y_left = f"{res_h}-{res_h}*min(max(t-{t_top}-{t_right}-{t_bot},0),{t_left})/{t_left}"
            filters.append(f"[v3][c_left]overlay=x='{x_left}':y='{y_left}':eof_action=repeat [v_prog]")
            
            stream_idx = "[v_prog]"

            # 2. LOGO RIDING PERIMETER
            logo_url = payload.get('logo_url') or payload.get('branding', {}).get('logo_url')
            if logo_url:
                logo_size = int(payload.get('logo_size', 70))
                logo_file = prepare_logo(logo_url, size=logo_size)
                if logo_file and os.path.exists(logo_file):
                    extra_inputs.extend(["-i", logo_file])
                    logo_input_idx = len(extra_inputs) // 2

                    w_max = res_w - logo_size
                    h_max = res_h - logo_size
                    half_s = logo_size // 2

                    t1 = t_top
                    t2 = t_top + t_right
                    t3 = t_top + t_right + t_bot

                    lx = (
                        f"if(lte(t,{t1:.3f}),min({w_max},max(0,{res_w}*t/{t_top:.3f}-{half_s})),"
                        f"if(lte(t,{t2:.3f}),{w_max},"
                        f"if(lte(t,{t3:.3f}),max(0,min({w_max},{res_w}-{res_w}*(t-{t2:.3f})/{t_bot:.3f}-{half_s})),0)))"
                    )
                    ly = (
                        f"if(lte(t,{t1:.3f}),0,"
                        f"if(lte(t,{t2:.3f}),min({h_max},max(0,{res_h}*(t-{t1:.3f})/{t_right:.3f}-{half_s})),"
                        f"if(lte(t,{t3:.3f}),{h_max},"
                        f"max(0,min({h_max},{res_h}-{res_h}*(t-{t3:.3f})/{t_left:.3f}-{half_s})))))"
                    )

                    filters.append(f"{stream_idx}[{logo_input_idx}:v]overlay=x='{lx}':y='{ly}':eof_action=repeat [v_logo]")
                    stream_idx = "[v_logo]"
            
        else: # neon_bottom
            filters.append(f"color=c={core_c}:s={res_w}x12:r=30:d={total_duration} [c_bot]")
            x_bot = f"-{res_w}+{res_w}*min(t,{anim_dur})/{anim_dur}"
            filters.append(f"{stream_idx}[c_bot]overlay=x='{x_bot}':y={res_h-12}:eof_action=repeat [v_prog]")
            stream_idx = "[v_prog]"

    # 3. Transparent Floating Audio Waveform (If requested)
    wv_config = payload.get('waveform', False)
    if wv_config:
        wv_style = wv_config if isinstance(wv_config, str) else payload.get('waveform_style', 'random')
        wv_width = int(res_w * 0.82)
        wv_height = 160
        wv_filter_str = build_waveform_filter(style=wv_style, width=wv_width, height=wv_height)
        
        filters.append(f"[0:a]{wv_filter_str}")
        
        # Positioned cleanly above the subtitle space
        wv_x = f"(W-{wv_width})/2"
        wv_y = int(res_h - (res_h * 0.15) - wv_height - 180)
        
        filters.append(f"{stream_idx}[wv]overlay=x='{wv_x}':y={wv_y}:eof_action=repeat [v_wave]")
        stream_idx = "[v_wave]"

    # 4. Clean Subtitles & Animated Floating Emoji Stickers
    raw_words = payload.get('words', [])
    if raw_words:
        sub_file, emoji_events = captions.generate_ass_subtitles(
            raw_words, 
            caption_style=payload.get('caption_style', 'random'), 
            res_x=res_w, 
            res_y=res_h
        )

        if emoji_events:
            unique_hexes = list(set([ev['hex'] for ev in emoji_events]))
            emoji_file_map = {}
            for h in unique_hexes:
                f_png = emojis.fetch_emoji_png(h, size=140)
                if f_png and os.path.exists(f_png):
                    extra_inputs.extend(["-i", f_png])
                    input_idx = len(extra_inputs) // 2
                    emoji_file_map[h] = input_idx

            emoji_size = 140
            base_y = int(res_h - (res_h * 0.15) - emoji_size - 90)

            for ev_idx, ev in enumerate(emoji_events):
                h = ev['hex']
                if h in emoji_file_map:
                    in_idx = emoji_file_map[h]
                    c_idx = ev['chunk_idx']
                    c_len = ev['chunk_len']

                    if c_len == 1:
                        ex = int((res_w - emoji_size) / 2)
                    elif c_len == 2:
                        offset = -160 if c_idx == 0 else 160
                        ex = int((res_w - emoji_size) / 2 + offset)
                    else: # 3 words
                        if c_idx == 0:
                            offset = -240
                        elif c_idx == 1:
                            offset = 0
                        else:
                            offset = 240
                        ex = int((res_w - emoji_size) / 2 + offset)

                    s_t = ev['start']
                    e_t = ev['end']
                    out_tag = f"[v_em_{ev_idx}]"
                    bounce_y = f"{base_y}-50*max(0,sin(min(3.14159,max(0,t-{s_t:.3f})*12.56)))*max(0,1-min(1,max(0,t-{s_t:.3f})/0.25))"
                    
                    filters.append(
                        f"{stream_idx}[{in_idx}:v]overlay="
                        f"x={ex}:y='{bounce_y}':"
                        f"enable='between(t,{s_t:.3f},{e_t:.3f})':eof_action=repeat {out_tag}"
                    )
                    stream_idx = out_tag

        if sub_file and os.path.exists(sub_file):
            filters.append(f"{stream_idx}ass={sub_file} [vout]")
            stream_idx = "[vout]"

    if not filters:
        os.rename(input_video, output_video)
        return output_video

    filter_complex = ";".join(filters)
    print(f"Applying Post-Processing Engine with Waveform & Floating Emojis...")
    
    cmd = [
        "ffmpeg", "-y", "-i", input_video,
        *extra_inputs,
        "-filter_complex", filter_complex,
        "-map", stream_idx, "-map", "0:a?",
        "-c:v", "libx264", "-c:a", "copy", output_video
    ]
    subprocess.run(cmd, check=True)
    return output_video
