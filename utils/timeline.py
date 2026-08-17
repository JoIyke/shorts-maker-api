import os
import subprocess
import ssl
import yt_dlp
from utils import captions

# THE ULTIMATE SSL HAMMER
ssl._create_default_https_context = ssl._create_unverified_context

def download_with_ytdlp(url, output_path, format_str="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"):
    """Helper function to download videos using native yt-dlp API"""
    print(f"Downloading {url} to {output_path}")
    ydl_opts = {
        'format': format_str,
        'outtmpl': output_path,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

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
    
    # 1. Download Main Video natively
    download_with_ytdlp(payload['url'], raw_video)
    
    # Download bottom gameplay video natively
    if payload.get('design') == 'brain_rot' and payload.get('bottom_url'):
        payload['bottom_file'] = "bottom.mp4"
        download_with_ytdlp(payload['bottom_url'], payload['bottom_file'], format_str="bestvideo[ext=mp4]/best")

    def render_part(start_sec, end_sec, prefix):
        out_name = f"{prefix}_rendered.mp4"
        design_module.render(raw_video, out_name, start_sec, end_sec, payload)
        return out_name, (end_sec - start_sec)

    cumulative_offset_ms = 0.0
    adjusted_words = []
    raw_words = payload.get('words', [])

    if payload.get('hook'):
        print("Processing Hook segment...")
        h_start, h_end = extract_bounds(payload['hook'])
        h_file, h_dur = render_part(h_start, h_end, "hook")
        rendered_segments.append(h_file)
        cumulative_offset_ms += (h_dur * 1000)

    if payload.get('intro_url'):
        print("Processing Intro...")
        intro_file = "intro_rendered.mp4"
        download_with_ytdlp(payload['intro_url'], "raw_intro.mp4", format_str="bestvideo[ext=mp4]/best")
        subprocess.run(["ffmpeg", "-y", "-i", "raw_intro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", intro_file], check=True)
        rendered_segments.append(intro_file)

    clips = payload.get('clips', [])
    for idx, clip in enumerate(clips):
        print(f"Processing Body Clip {idx + 1}/{len(clips)}...")
        c_start, c_end = extract_bounds(clip)
        c_file, c_dur = render_part(c_start, c_end, f"body_{idx}")
        rendered_segments.append(c_file)

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

    if payload.get('outro_url'):
        print("Processing Outro...")
        outro_file = "outro_rendered.mp4"
        download_with_ytdlp(payload['outro_url'], "raw_outro.mp4", format_str="bestvideo[ext=mp4]/best")
        subprocess.run(["ffmpeg", "-y", "-i", "raw_outro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", outro_file], check=True)
        rendered_segments.append(outro_file)

    print("Stitching all segments together...")
    concat_list = "concat_list.txt"
    with open(concat_list, "w") as f:
        for seg in rendered_segments:
            f.write(f"file '{seg}'\n")

    stitched_file = "stitched_master.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", stitched_file], check=True)

    final_output = "output.mp4"
    caption_style = payload.get('caption_style', 'hormozi')
    sub_file = captions.generate_ass_subtitles(adjusted_words, caption_style=caption_style)

    if sub_file and os.path.exists(sub_file):
        print("Burning captions onto final 1080x1920 master video...")
        subprocess.run(["ffmpeg", "-y", "-i", stitched_file, "-vf", f"ass={sub_file}", "-c:a", "copy", final_output], check=True)
    else:
        os.rename(stitched_file, final_output)

    print("Pipeline Complete! Output video ready.")
