import os
import subprocess
import urllib.request
from utils import captions

def render(payload, output_file="output.mp4"):
    print("Executing Audio Slideshow Short Generator...")

    # 1. Determine Aspect Ratio / Resolution
    aspect_ratio = payload.get('aspect_ratio', '9:16')
    if aspect_ratio == '1:1':
        res_w, res_h = 1080, 1080
    elif aspect_ratio == '16:9':
        res_w, res_h = 1920, 1080
    else:  # Default 9:16 vertical
        res_w, res_h = 1080, 1920

    print(f"Target resolution: {res_w}x{res_h} ({aspect_ratio})")

    # 2. Download the Pre-Cut Audio / Media File
    audio_file = "input_audio.mp4"
    print("Downloading audio media...")
    subprocess.run([
        "yt-dlp", 
        "-f", "bestaudio[ext=m4a]/bestaudio/best", 
        "-o", audio_file, 
        payload['url']
    ], check=True)

    # 3. Process Each Image Slide
    slides = payload.get('slides', [])
    rendered_slides = []

    print(f"Processing {len(slides)} image slides...")
    for idx, slide in enumerate(slides):
        img_url = slide.get('image_url')
        start = float(slide.get('start', 0.0))
        end = float(slide.get('end', 0.0))
        duration = max(0.1, end - start)

        # Download image
        local_img = f"temp_img_{idx}.jpg"
        print(f"Downloading slide {idx + 1}: {img_url} ({duration}s)")
        
        # Using a browser User-Agent so image hosts don't block the request
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(local_img, 'wb') as out_file:
            out_file.write(response.read())

        # Convert image into a video segment of exact duration and aspect ratio
        slide_video = f"slide_{idx}.mp4"
        vf_filter = f"scale={res_w}:{res_h}:force_original_aspect_ratio=increase,crop={res_w}:{res_h}"
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-t", str(duration),
            "-i", local_img,
            "-vf", vf_filter,
            "-r", "30",
            "-pix_fmt", "yuv420p",
            slide_video
        ]
        subprocess.run(ffmpeg_cmd, check=True)
        rendered_slides.append(slide_video)

    # 4. Stitch All Image Slides Together
    concat_list = "slideshow_concat.txt"
    with open(concat_list, "w") as f:
        for s in rendered_slides:
            f.write(f"file '{s}'\n")

    slideshow_video = "slideshow_raw.mp4"
    subprocess.run([
        "ffmpeg", "-y", 
        "-f", "concat", "-safe", "0", 
        "-i", concat_list, 
        "-c", "copy", 
        slideshow_video
    ], check=True)

    # 5. Merge Stitched Slides with the Audio Track
    combined_media = "slideshow_with_audio.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", slideshow_video,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        combined_media
    ], check=True)

    # 6. Burn Captions
    raw_words = payload.get('words', [])
    caption_style = payload.get('caption_style', 'hormozi')
    sub_file = captions.generate_ass_subtitles(raw_words, caption_style=caption_style, res_x=res_w, res_y=res_h)

    if sub_file and os.path.exists(sub_file):
        print("Burning captions onto final audio slideshow...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", combined_media,
            "-vf", f"ass={sub_file}",
            "-c:a", "copy",
            output_file
        ], check=True)
    else:
        os.rename(combined_media, output_file)

    print("Audio Slideshow generated successfully!")
