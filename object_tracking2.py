import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
from sort import Sort
import tempfile

# --- PAGE CONFIG ---
st.set_page_config(page_title="Object Detection and Tracking", layout="wide")

# --- HEADING ---
st.markdown("""
    <h1 style='text-align: center; color: #4CAF50; font-size: 50px;'>
        Object Detection and Tracking
    </h1>
""", unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Settings")
source = st.sidebar.selectbox("Select Video Source", ["Webcam", "Upload Video"])
conf_thresh = st.sidebar.slider("Detection Confidence", 0.1, 1.0, 0.5, 0.05)

# Dropdown for common classes
common_classes = ["person","car","bicycle","dog","cat","bus","truck"]
selected_classes = st.sidebar.multiselect(
    "Select Classes to Track (from common list)",
    common_classes
)

# Text input for custom classes
custom_classes_input = st.sidebar.text_input(
    "Or enter additional custom classes (comma separated)"
)
if custom_classes_input:
    custom_classes = [cls.strip() for cls in custom_classes_input.split(",")]
else:
    custom_classes = []

# Combine both
track_classes = list(set(selected_classes + custom_classes))

snapshot_btn = st.sidebar.button("📸 Capture Snapshot")
record_btn = st.sidebar.button("⏺️ Start/Stop Recording")

# --- LOAD YOLO MODEL ---
model = YOLO("yolov8s-seg.pt")  # YOLOv8 segmentation model
tracker = Sort()
colors = {}

# --- LAYOUT ---
col1, col2 = st.columns([3,1])
video_placeholder = col1.empty()
stats_placeholder = col2.empty()

frame_count = 0
recording = False
out = None

# --- VIDEO CAPTURE ---
cap = None
if source == "Webcam":
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not open webcam.")
        st.stop()
elif source == "Upload Video":
    uploaded_file = st.sidebar.file_uploader("Upload Video", type=["mp4","avi","mov"])
    if uploaded_file:
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_video.write(uploaded_file.read())
        temp_video_path = temp_video.name
        cap = cv2.VideoCapture(temp_video_path)
    else:
        st.warning("Please upload a video file.")
        st.stop()

# --- MAIN LOOP ---
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    detections = []

    # YOLO detection + segmentation
    results = model(frame, conf=conf_thresh)[0]

    # --- Segmentation masks ---
    if hasattr(results, "masks") and results.masks is not None:
        masks = results.masks.xy
        for mask_obj in masks:
            mask_img = np.zeros(frame.shape[:2], dtype=np.uint8)
            pts = np.array(mask_obj, dtype=np.int32)
            cv2.fillPoly(mask_img, [pts], 255)
            color = tuple(np.random.randint(0, 255, 3).tolist())
            colored_mask = np.zeros_like(frame, dtype=np.uint8)
            colored_mask[:, :] = color
            frame = cv2.addWeighted(frame, 1.0,
                                    cv2.bitwise_and(colored_mask, colored_mask, mask=mask_img),
                                    0.5, 0)

    # --- Bounding boxes ---
    for r in results.boxes:
        x1, y1, x2, y2 = map(int, r.xyxy[0])
        conf = float(r.conf[0])
        cls_id = int(r.cls[0])
        label = model.names[cls_id]

        if track_classes and label not in track_classes:
            continue

        detections.append([x1, y1, x2, y2, conf])
        if label not in colors:
            colors[label] = tuple(np.random.randint(0, 255, 3).tolist())
        color = colors[label]

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # --- SORT tracking ---
    object_ids = []
    if len(detections) > 0:
        dets = np.array(detections)
        tracked = tracker.update(dets)
        for x1, y1, x2, y2, obj_id in tracked:
            object_ids.append(int(obj_id))
            cv2.putText(frame, f"ID:{int(obj_id)}", (int(x1), int(y2)+20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

    # --- Display frame ---
    video_placeholder.image(frame, channels="BGR")

    # --- Stats ---
    class_counts = {}
    for r in results.boxes:
        cls_id = int(r.cls[0])
        label = model.names[cls_id]
        if track_classes and label not in track_classes:
            continue
        class_counts[label] = class_counts.get(label,0)+1

    stats_text = f"Frame: {frame_count}\nDetected Objects: {len(detections)}\nActive IDs: {object_ids if object_ids else 'None'}\n"
    if class_counts:
        stats_text += "Objects per Class:\n"
        for k,v in class_counts.items():
            stats_text += f" • {k}: {v}\n"
    stats_placeholder.text(stats_text)

    # --- Snapshot ---
    if snapshot_btn:
        cv2.imwrite("snapshot.jpg", frame)
        st.sidebar.success("✅ Snapshot captured!")
        snapshot_btn = False

    # --- Recording ---
    if record_btn and not recording:
        recording = True
        out_file = "recorded_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_file, fourcc, 20.0, (frame.shape[1], frame.shape[0]))
        st.sidebar.success(f"⏺️ Recording started: {out_file}")
    elif record_btn and recording:
        recording = False
        if out:
            out.release()
        st.sidebar.success(f"⏹️ Recording stopped. Saved: {out_file}")
        record_btn = False

    if recording and out:
        out.write(frame)

cap.release()
if recording and out:
    out.release()
