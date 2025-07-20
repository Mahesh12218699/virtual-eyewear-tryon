import cv2
import mediapipe as mp
import os

def generate_tryon_images(image_path, output_dir):
    # Load the uploaded photo
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError("Uploaded image not found.")

    # Load glasses (must be PNG with alpha)
    glasses_paths = [
        "static/frames/full_rim.png",
        "static/frames/gold.png",
        "static/frames/silver.png"
    ]
    glasses_images = [cv2.imread(path, cv2.IMREAD_UNCHANGED) for path in glasses_paths]
    for idx, img in enumerate(glasses_images):
        if img is None:
            raise FileNotFoundError(f"Missing frame: {glasses_paths[idx]}")

    # Setup MediaPipe
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    )

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)

    if not results.multi_face_landmarks:
        print("❌ No face detected.")
        return []

    h, w, _ = image.shape
    face_landmarks = results.multi_face_landmarks[0].landmark

    # Get landmarks for placement
    left_edge = face_landmarks[234]
    right_edge = face_landmarks[454]
    nose_bridge = face_landmarks[168]

    x1, y1 = int(left_edge.x * w), int(left_edge.y * h)
    x2, y2 = int(right_edge.x * w), int(right_edge.y * h)
    nx, ny = int(nose_bridge.x * w), int(nose_bridge.y * h)

    eye_center_x = (x1 + x2) // 2
    eye_center_y = ny + int(0.05 * h)
    glasses_width = int(1.1 * abs(x2 - x1))

    saved_images = []

    for i, glasses_img in enumerate(glasses_images):
        output_img = image.copy()

        # Resize and position
        glasses_height = int(glasses_width * glasses_img.shape[0] / glasses_img.shape[1])
        resized_glasses = cv2.resize(glasses_img, (glasses_width, glasses_height))
        top_left = (eye_center_x - glasses_width // 2, eye_center_y - glasses_height // 2)

        for y in range(glasses_height):
            for x in range(glasses_width):
                py, px = top_left[1] + y, top_left[0] + x
                if 0 <= py < output_img.shape[0] and 0 <= px < output_img.shape[1]:
                    alpha = resized_glasses[y, x, 3] / 255.0
                    if alpha > 0:
                        output_img[py, px, :3] = (
                            alpha * resized_glasses[y, x, :3] +
                            (1 - alpha) * output_img[py, px, :3]
                        )

        output_path = os.path.join(output_dir, f"output{i+1}.jpg")
        cv2.imwrite(output_path, output_img)
        saved_images.append(output_path)

    return saved_images
