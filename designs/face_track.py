import cv2
import subprocess
import mediapipe.solutions.face_detection as mp_face_detection

def render(input_file, output_file, start, end, args):
    print("Executing Smart AI Face Tracking...")

    # 1. Open Video
    cap = cv2.VideoCapture(input_file)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
    crop_w = int(height * 9 / 16)

    start_frame = int(float(start) * fps)
    end_frame = int(float(end) * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Explicitly initialize MediaPipe AI Face Detection
    face_detector = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    frame_face_data = [] # Stores face locations per sample
    curr_frame = start_frame
    sample_rate = 10  # Sample every 10th frame for speed

    while cap.isOpened() and curr_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if (curr_frame - start_frame) % sample_rate == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detector.process(rgb_frame)

            if results.detections:
                faces = []
                for det in results.detections:
                    bbox = det.location_data.relative_bounding_box
                    x_center = bbox.xmin + (bbox.width / 2.0)
                    faces.append(x_center)
                # Sort faces from Left to Right across the screen
                faces.sort()
                frame_face_data.append(faces)
            else:
                frame_face_data.append([]) # 0 faces detected

        curr_frame += 1

    cap.release()

    # 2. Determine average face count across the clip
    counts = [len(f) for f in frame_face_data]
    avg_face_count = round(sum(counts) / len(counts)) if counts else 0

    print(f"Smart AI Analysis Complete: Detected average of {avg_face_count} face(s).")

    # RULE 1: 0 Faces Detected (Audience / B-Roll / Slides)
    if avg_face_count == 0:
        print("Mode: Blurred Background Fallback (No faces found)")
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];"
            "[0:v]scale=1080:-1[fg];"
            "[bg][fg]overlay=0:(H-h)/2[vout]"
        )
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-to", str(end),
            "-i", input_file, "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "0:a", "-c:a", "aac", output_file
        ]

    # RULE 2: 1 Face Detected (Solo Speaker)
    elif avg_face_count == 1:
        print("Mode: Solo Face Tracking")
        all_x = [f[0] for f in frame_face_data if len(f) > 0]
        avg_x_percent = sum(all_x) / len(all_x) if all_x else 0.5
        target_x_center = int(avg_x_percent * width)
        
        crop_x = target_x_center - (crop_w // 2)
        crop_x = max(0, min(crop_x, width - crop_w))

        vf_filter = f"crop={crop_w}:{height}:{crop_x}:0"
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-to", str(end),
            "-i", input_file, "-vf", vf_filter, "-c:a", "aac", output_file
        ]

    # RULE 3: 2 Faces Detected (Interview / Dual Stack)
    elif avg_face_count == 2:
        print("Mode: Dual Stack (Left person top, Right person bottom)")
        left_faces = [f[0] for f in frame_face_data if len(f) >= 2]
        right_faces = [f[1] for f in frame_face_data if len(f) >= 2]

        avg_left = (sum(left_faces) / len(left_faces)) if left_faces else 0.25
        avg_right = (sum(right_faces) / len(right_faces)) if right_faces else 0.75

        x1 = max(0, min(int(avg_left * width) - (height // 2), width - height))
        x2 = max(0, min(int(avg_right * width) - (height // 2), width - height))

        filter_complex = (
            f"[0:v]crop={height}:{height}:{x1}:0,scale=1080:960[top];"
            f"[0:v]crop={height}:{height}:{x2}:0,scale=1080:960[bot];"
            f"[top][bot]vstack[vout]"
        )
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-to", str(end),
            "-i", input_file, "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "0:a", "-c:a", "aac", output_file
        ]

    # RULE 4: 3+ Faces Detected (Panel / Speaker + Group)
    else:
        print("Mode: Speaker + Group Shot (Primary speaker top, full video bottom)")
        all_faces = [f for frame in frame_face_data for f in frame]
        avg_main_face = sum(all_faces) / len(all_faces) if all_faces else 0.5
        
        x1 = max(0, min(int(avg_main_face * width) - (height // 2), width - height))

        filter_complex = (
            f"[0:v]crop={height}:{height}:{x1}:0,scale=1080:960[top];"
            f"[0:v]scale=1080:960:force_original_aspect_ratio=decrease,pad=1080:960:(ow-iw)/2:(oh-ih)/2:black[bot];"
            f"[top][bot]vstack[vout]"
        )
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-to", str(end),
            "-i", input_file, "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "0:a", "-c:a", "aac", output_file
        ]

    # Execute FFmpeg Command
    subprocess.run(ffmpeg_cmd, check=True)
    print("Smart Face Tracking Render Complete!")
