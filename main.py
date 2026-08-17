import json
import argparse
from designs import crop_basic, meme_style, meme_with_text_style, brain_rot, face_track, raw_cut, audio_slideshow
from utils import timeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--payload_file', default='payload.json')
    args = parser.parse_args()

    # Load JSON Payload
    with open(args.payload_file, 'r') as f:
        payload = json.load(f)

    design_name = payload.get('design', 'crop')
    print(f"Director Starting Job: {payload.get('job_id')} | Design: {design_name}")

    # Special handling for Audio Slideshow
    if design_name == 'audio_slideshow':
        audio_slideshow.render(payload, "output.mp4")
        return

    # Standard Video Pipeline
    design_map = {
        'crop': crop_basic,
        'meme': meme_style,
        'meme_text': meme_with_text_style,
        'brain_rot': brain_rot,
        'face_track': face_track,
        'raw_cut': raw_cut
    }

    design_module = design_map.get(design_name, crop_basic)
    timeline.process_timeline(payload, design_module)

if __name__ == "__main__":
    main()
