import os
import subprocess
from utils import captions

def process_timeline(payload, design_module):
    raw_video = "main_input.mp4"
    rendered_segments = []
    
    # 1. Download Main Video
    subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "-o", raw_video, payload['url']], check=True)
    
    # Download bottom gameplay video if brain_rot design
    if payload.get('design') == 'brain_rot' and payload.get('bottom_url'):
        payload['bottom_file'] = "bottom.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", payload['bottom_file'], payload['bottom_url']], check=True)

    # Helper function to crop and render a segment using our design modules
    def render_part(start, end, prefix):
        out_name = f"{prefix}_rendered.mp4"
        design_module.render(raw_video, out_name, start, end, payload)
        return out_name, (float(end) - float(start))

    cumulative_offset_ms = 0.0
    adjusted_words = []
    raw_words = payload.get('words', [])

    # A. Process Hook (If provided)
    if payload.get('hook'):
        h_start = payload['hook']['start']
        h_end = payload['hook']['end']
        h_file, h_dur = render_part(h_start, h_end, "hook")
        rendered_segments.append(h_file)
        cumulative_offset_ms += (h_dur * 1000)

    # B. Process Intro (If provided)
    if payload.get('intro_url'):
        intro_file = "intro_rendered.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", "raw_intro.mp4", payload['intro_url']], check=True)
        # Format intro to 1080x1920
        subprocess.run(["ffmpeg", "-y", "-i", "raw_intro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", intro_file], check=True)
        rendered_segments.append(intro_file)
        # Add intro duration to offset (assuming intro duration ~ 3s or get via ffmpeg)

    # C. Process Body Clips
    clips = payload.get('clips', [])
    for idx, clip in enumerate(clips):
        c_start = clip['start']
        c_end = clip['end']
        c_file, c_dur = render_part(c_start, c_end, f"body_{idx}")
        rendered_segments.append(c_file)

        # Filter & Adjust Word Timestamps for this specific clip
        c_start_ms = float(c_start) * 1000
        c_end_ms = float(c_end) * 1000

        for w in raw_words:
            if c_start_ms <= w['start'] <= c_end_ms:
                # Calculate relative offset in new combined timeline
                relative_start = w['start'] - c_start_ms
                relative_end = w['end'] - c_start_ms
                adjusted_words.append({
                    "text": w['text'],
                    "start": int(relative_start + cumulative_offset_ms),
                    "end": int(relative_end + cumulative_offset_ms)
                })

        cumulative_offset_ms += (c_dur * 1000)

    # D. Process Outro (If provided)
    if payload.get('outro_url'):
        outro_file = "outro_rendered.mp4"
        subprocess.run(["yt-dlp", "-f", "bestvideo[ext=mp4]/best", "-o", "raw_outro.mp4", payload['outro_url']], check=True)
        subprocess.run(["ffmpeg", "-y", "-i", "raw_outro.mp4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black", "-c:a", "aac", outro_file], check=True)
        rendered_segments.append(outro_file)

    # 2. Stitch All 9:16 Rendered Segments Together
    print("Stitching segments together...")
    concat_list = "concat_list.txt"
    with open(concat_list, "w") as f:
        for seg in rendered_segments:
            f.write(f"file '{seg}'\n")

    stitched_file = "stitched_master.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", stitched_file], check=True)

    # 3. Generate Subtitles and Burn Captions onto Final Master Video
    final_output = "output.mp4"
    caption_style = payload.get('caption_style', 'hormozi')
    sub_file = captions.generate_ass_subtitles(adjusted_words, caption_style=caption_style)

    if sub_file and os.path.exists(sub_file):
        print("Burning captions onto final 1080x1920 master video...")
        subprocess.run(["ffmpeg", "-y", "-i", stitched_file, "-vf", f"ass={sub_file}", "-c:a", "copy", final_output], check=True)
    else:
        # If no words/captions, output the stitched file directly
        os.rename(stitched_file, final_output)

    print("Pipeline Complete! Output ready.")
