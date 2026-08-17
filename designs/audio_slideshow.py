import os
import subprocess
import urllib.request
from utils import captions, effects

def get_media_duration(file_path):
    """Probes the exact duration of an audio or video file in seconds."""
    cmd = [
        "ffprobe", "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def render(payload, output_file="output.mp4"):
    print("Executing Audio Slideshow Short Generator with Transitions & Progress Glow...")

    # 1. Determine Resolution / Aspect Ratio
    aspect_ratio = payload.get('aspect_ratio', '9:16')
    if aspect_ratio == '1:1':
        res_w, res_h = 1080, 1080
    elif aspect_ratio == '16:9':
        res_w, res_h = 1920, 1080
    else:  # Default 9:16
        res_w, res_h = 1080, 1920

    # 2. Download Media Audio
    audio_file = "input_audio.mp4"
    print("Downloading audio media...")
    subprocess.run([
        "yt-dlp", 
        "-f", "bestaudio[ext=m4a]/bestaudio/best", 
        "-o", audio_file, 
        payload['url']
    ], check=True)

    # Get exact audio duration so the video never cuts early
    total_audio_duration = get_media_duration(audio_file)
    print(f"Total audio duration: {total_audio_duration:.2f}s")

    # 3. Process Each Image Slide
    slides = payload.get('slides', [])
    rendered_slides = []
    slide_durations = []
    
    transition_style = payload.get('transition', 'random')
    trans_dur = 0.4 if transition_style == 'none' else 0.4

    print(f"Processing {len(slides)} image slides with transition: {transition_style}...")
    
# NEW: Download Logo if provided
    logo_file = None
    if payload.get('logo_url'):
        print("Downloading Branding Logo...")
        logo_file = "brand_logo.png"
        req = urllib.request.Request(payload['logo_url'], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(logo_file, 'wb') as out_file:
            out_file.write(response.read())

    # Check if Auto-Zoom is enabled
    auto_zoom = payload.get('auto_zoom', True)

    for idx, slide in enumerate(slides):
        img_url = slide.get('image_url')
        start = float(slide.get('start', 0.0))
        end = float(slide.get('end', 0.0))
        
        if idx == len(slides) - 1 and end < total_audio_duration:
            end = total_audio_duration

        base_duration = max(0.5, end - start)
        render_duration = base_duration + (trans_dur if (idx < len(slides) - 1 and trans_dur > 0) else 0.0)

        local_img = f"temp_img_{idx}.jpg"
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(local_img, 'wb') as out_file:
            out_file.write(response.read())

        slide_video = f"slide_{idx}.mp4"
        
        # DYNAMIC AUTO-ZOOM (KEN BURNS) LOGIC
        if auto_zoom:
            w_lg = int(res_w * 1.5)
            h_lg = int(res_h * 1.5)
            base_filter = f"scale={w_lg}:{h_lg}:force_original_aspect_ratio=increase,crop={w_lg}:{h_lg}"
            
            frames = int(render_duration * 30)
            movements = [
                f"zoompan=z='min(pzoom+0.0015,1.2)':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d={frames}:s={res_w}x{res_h}", # Zoom In
                f"zoompan=z='1.1':x='x+1.5':y='ih/2-(ih/zoom)/2':d={frames}:s={res_w}x{res_h}", # Pan Right
                f"zoompan=z='1.1':x='x-1.5':y='ih/2-(ih/zoom)/2':d={frames}:s={res_w}x{res_h}", # Pan Left
                f"zoompan=z='1.1':x='iw/2-(iw/zoom)/2':y='y+1.5':d={frames}:s={res_w}x{res_h}"  # Pan Down
            ]
            import random
            vf_filter = f"{base_filter},{random.choice(movements)}"
        else:
            vf_filter = f"scale={res_w}:{res_h}:force_original_aspect_ratio=increase,crop={res_w}:{res_h}"
        
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-loop", "1", "-t", str(render_duration),
            "-i", local_img, "-vf", vf_filter, "-r", "30", "-pix_fmt", "yuv420p", slide_video
        ]
        subprocess.run(ffmpeg_cmd, check=True)
        rendered_slides.append(slide_video)
        slide_durations.append(render_duration)

    # 4. Stitch Slides with Transitions
    slideshow_video = "slideshow_stitched.mp4"
    effects.stitch_with_transitions(rendered_slides, slide_durations, transition_style, slideshow_video)

    # 5. Merge Stitched Slides with Audio
    combined_media = "slideshow_with_audio.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", slideshow_video, "-i", audio_file,
        "-c:v", "libx264", "-c:a", "aac", "-t", str(total_audio_duration), combined_media
    ], check=True)

    # 6. Post-Processing: Progress Bar, Logo Rider & Captions
    effects.apply_post_processing(combined_media, output_file, payload, total_audio_duration, res_w, res_h, logo_file=logo_file)

    print("Audio Slideshow generated successfully with all effects!")
