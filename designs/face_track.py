import cv2
import mediapipe as mp
import subprocess

def render(input_file, output_file, start, end, args):
    print("Applying AI Face Tracking Design...")

    # 1. Open the video to read dimensions and frame rate
    cap = cv2.VideoCapture(input_file)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Target 9:16 crop width
    crop_w = int(height * 9 / 16)

    # Calculate frame positions
    start_frame = int(float(start) * fps)
    end_frame = int(float(end) * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # Initialize MediaPipe AI Face Detection
    mp_face = mp.solutions.face_detection
    face_detection = mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    x_centers = []
    curr_frame = start_frame
    sample_rate = 10  # Sample 1 out of every 10 frames to make detection lightning fast

    print("Scanning video frames for faces...")
    while cap.isOpened() and curr_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if (curr_frame - start_frame) % sample_rate == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)

            if results.detections:
                # Get the first/main face detected
                best_detection = results.detections[0]
                bbox = best_detection.location_data.relative_bounding_box
                
                # Calculate normalized X center (0.0 to 1.0)
                face_x_center = bbox.xmin + (bbox.width / 2.0)
                x_centers.append(face_x_center)

        curr_frame += 1

    cap.release()

    # 2. Determine target X coordinate
    if x_centers:
        avg_x_percent = sum(x_centers) / len(x_centers)
        target_x_center = int(avg_x_percent * width)
        print(f"Face detected! Calculated X center: {target_x_center}px")
    else:
        target_x_center = int(width / 2)
        print("No face detected in clip. Falling back to center crop.")

    # 3. Calculate crop offset so face is centered
    crop_x = target_x_center - (crop_w // 2)

    # Clamp crop_x so the crop box never goes off screen edges
    crop_x = max(0, min(crop_x, width - crop_w))

    # 4. Render with FFmpeg using dynamic X offset
    vf_filter = f"crop={crop_w}:{height}:{crop_x}:0"
    print(f"Applying FFmpeg filter: {vf_filter}")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-to", str(end),
        "-i", input_file,
        "-vf", vf_filter,
        "-c:a", "aac",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
