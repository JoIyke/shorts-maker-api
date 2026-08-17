import os
import random
import subprocess
import urllib.request
from utils import captions, effects

def get_media_duration(file_path):
    """Probes exact duration of an audio or video file in seconds."""
    cmd = [
        "ffprobe", "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def render(payload, output_file="output.mp4"):
    print("Executing Audio Slideshow Short Generator with Fast Zoompan & Effects...")

    # 1. Determine Resolution
    aspect_ratio = payload.get('aspect_ratio', '9:16')
    if aspect_ratio == '1:1':
        res_w, res_h = 1080, 1080
    elif aspect_ratio == '16:9':
        res_w, res_h = 1920, 1080
    else:  # Default 9:16
        res_w, res_h = 1080, 1920

    # 2. Download Audio
    audio_file = "input_audio.mp4"
    print("Downloading audio media...")
    subprocess.run([
        "yt-dlp", 
        "-f", "bestaudio[ext=m4a]/bestaudio/best", 
        "-o", audio_file, 
        payload['url']
    ], check=True)

    total_audio_duration = get_media_duration(audio_file)
    print(f"Total audio duration: {total_audio_duration:.2f}s")

    # 3. Process Each Image Slide
    slides = payload.get('slides', [])
    rendered_slides = []
    slide_durations = []
    
    transition_style = payload.get('transition', 'random')
    trans_dur = 0.0 if transition_style == 'none' else 0.4
    
    enable_zoompan = payload.get('zoompan', False) or payload.get('motion', False) or payload.get('ken_burns', False)
    print(f"Ken Burns Zoompan Motion: {'ENABLED' if enable_zoompan else 'DISABLED'}")

    print(f"Processing {len(slides)} image slides with transition: {transition_style}...")
    
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
        
        if enable_zoompan:
            # FIX: Native 1-input zoompan without '-loop 1' to avoid explosive looping
            num_frames = int(render_duration * 30)
            step = 0.15 / max(1, num_frames)
            
            motion_type = random.choice(['zoom_in', 'zoom_out', 'pan_left', 'pan_right', 'pan_down'])
            print(f"Slide {idx + 1}: Applying fast '{motion_type}' motion...")
            
            if motion_type == 'zoom_in':
                zp_expr = f"z='min(zoom+{step:.6f},1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            elif motion_type == 'zoom_out':
                zp_expr = f"z='max(1.15-{step:.6f}*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            elif motion_type == 'pan_left':
                zp_expr = f"z='1.12':x='(1-(on/{num_frames}))*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
            elif motion_type == 'pan_right':
                zp_expr = f"z='1.12':x='(on/{num_frames})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
            else:  # pan_down
                zp_expr = f"z='1.12':x='iw/2-(iw/zoom/2)':y='(on/{num_frames})*(ih-ih/zoom)'"

            # Lightweight pre-scale (only 15% larger for fast, crisp encoding)
            pre_w = int(res_w * 1.15)
            pre_h = int(res_h * 1.15)
            vf_filter = (
                f"scale={pre_w}:{pre_h}:force_original_aspect_ratio=increase,"
                f"crop={pre_w}:{pre_h},"
                f"zoompan={zp_expr}:d={num_frames}:s={res_w}x{res_h}:fps=30"
            )

            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", local_img,
                "-vf", vf_filter,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                slide_video
            ]
        else:
            # Fast static crop
            vf_filter = f"scale={res_w}:{res_h}:force_original_aspect_ratio=increase,crop={res_w}:{res_h}"
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-t", str(render_duration),
                "-i", local_img,
                "-vf", vf_filter,
                "-r", "30",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                slide_video
            ]

        subprocess.run(ffmpeg_cmd, check=True)
        rendered_slides.append(slide_video)
        slide_durations.append(render_duration)

    # 4. Stitch Slides with Transitions Engine
    slideshow_video = "slideshow_stitched.mp4"
    effects.stitch_with_transitions(
        rendered_slides, 
        slide_durations, 
        transition_type=transition_style, 
        output_file=slideshow_video
    )

    # 5. Merge Stitched Slides with Audio
    combined_media = "slideshow_with_audio.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", slideshow_video,
        "-i", audio_file,
        "-vf", "tpad=stop_mode=clone:stop_duration=5",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-t", str(total_audio_duration),
        combined_media
    ], check=True)

    # 6. Post-Processing: Progress Bar Perimeter & Captions
    effects.apply_post_processing(combined_media, output_file, payload, total_audio_duration, res_w, res_h)

    print("Audio Slideshow generated successfully!")
