import os
import io
import cv2
import torch
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import base64
import segmentation_models_pytorch as smp
import albumentations as A
from albumentations.pytorch.transforms import ToTensorV2

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# -----------------------------
# Global Settings & Model
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
best_threshold = 0.65

def load_model():
    global model, best_threshold
    # Define model architecture
    net = smp.DeepLabV3Plus(
        encoder_name="resnet50",
        encoder_weights="imagenet",
        in_channels=3,
        classes=1
    ).to(device)

    # Checkpoints to look for
    checkpoint_files = [
        "deeplabv3p_best.pth",
        "spillguard_enhanced_final.pth",
        "spillguard_best.pth",
        os.path.join(os.path.dirname(__file__), "deeplabv3p_best.pth")
    ]

    for ckpt_file in checkpoint_files:
        if os.path.exists(ckpt_file):
            try:
                print(f"Loading model from {ckpt_file}...")
                checkpoint = torch.load(ckpt_file, map_location=device)
                
                if "model_state_dict" in checkpoint:
                    net.load_state_dict(checkpoint["model_state_dict"])
                    best_threshold = float(checkpoint.get("best_threshold", best_threshold))
                elif "model" in checkpoint:
                    state_dict = checkpoint["model"]
                    if isinstance(state_dict, dict):
                        net.load_state_dict(state_dict)
                    else:
                        net.load_state_dict({k: v.to(device) for k, v in state_dict.items()})
                    best_threshold = float(checkpoint.get("best_threshold", best_threshold))
                else:
                    net.load_state_dict(checkpoint, strict=False)
                
                net.eval()
                model = net
                print(f"Model loaded successfully. Threshold: {best_threshold}")
                return
            except Exception as e:
                print(f"Failed to load {ckpt_file}: {e}")

    print("Warning: No trained model found. Using untrained model.")
    net.eval()
    model = net

# Load model on startup
load_model()

# -----------------------------
# Preprocessing Logic
# -----------------------------
def preprocess_image(image):
    IMG_SIZE = 512
    if isinstance(image, Image.Image):
        if image.mode in ("RGBA", "LA"):
            image = image.convert("RGB")
        img_array = np.array(image)
    else:
        img_array = image

    # Grayscale conversion
    if img_array.ndim == 3:
        if img_array.shape[2] == 4:
            img_array = img_array[..., :3]
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        img_gray = img_array

    # Normalize
    img_gray = img_gray.astype(np.float32)
    if img_gray.max() > 1.0:
        img_gray /= 255.0

    # Percentile stretching (SAR-like)
    lo, hi = np.percentile(img_gray, [1, 99])
    if hi > lo:
        img_gray = np.clip(img_gray, lo, hi)
        img_gray = (img_gray - lo) / max(hi - lo, 1e-6)
    else:
        mmin, mptp = float(img_gray.min()), float(np.ptp(img_gray))
        img_gray = (img_gray - mmin) / (mptp + 1e-6)

    # Replicate to 3 channels
    img_3ch = np.stack([img_gray, img_gray, img_gray], axis=2)

    # Transforms
    transform = A.Compose([
        A.LongestMaxSize(max_size=IMG_SIZE, interpolation=cv2.INTER_CUBIC),
        A.PadIfNeeded(IMG_SIZE, IMG_SIZE, border_mode=cv2.BORDER_REFLECT_101),
        A.ToFloat(max_value=1.0),
        ToTensorV2(),
    ])
    transformed = transform(image=img_3ch)
    img_tensor = transformed["image"].unsqueeze(0).to(device)
    return img_tensor, img_gray

# -----------------------------
# API Endpoint
# -----------------------------
@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500

    try:
        data = request.json
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        image = Image.open(io.BytesIO(image_data))
        
        # Original dims
        ow, oh = image.size

        # Inference
        img_tensor, _ = preprocess_image(image)
        with torch.no_grad():
            logits = model(img_tensor)
            prob = torch.sigmoid(logits)[0, 0].cpu().numpy()

        # Resize probability map back to original size
        prob_resized = cv2.resize(prob, (ow, oh), interpolation=cv2.INTER_LINEAR)
        
        # Create mask
        mask = (prob_resized >= best_threshold).astype(np.uint8)
        
        # Calculate statistics
        total_px = mask.size
        oil_px = int(mask.sum())
        oil_pct = (oil_px / total_px) * 100 if total_px > 0 else 0
        
        is_spill = oil_pct > 1.0  # Detection criteria

        # Create visualization (Overlay)
        # Convert original to RGB array
        orig_arr = np.array(image.convert("RGB"))
        
        # Create Grayscale background for better visualization
        gray_bg = cv2.cvtColor(orig_arr, cv2.COLOR_RGB2GRAY)
        gray_bg_rgb = cv2.cvtColor(gray_bg, cv2.COLOR_GRAY2RGB)
        
        # Red overlay on spill areas
        overlay = gray_bg_rgb.copy()
        overlay[mask == 1] = [255, 0, 0]  # Red
        
        # Blend
        blended = cv2.addWeighted(gray_bg_rgb, 0.7, overlay, 0.3, 0)
        
        # Convert result to base64
        pil_result = Image.fromarray(blended)
        buf = io.BytesIO()
        pil_result.save(buf, format="PNG")
        result_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return jsonify({
            'is_spill': is_spill,
            'oil_percentage': oil_pct,
            'confidence': float(prob_resized.max()),
            'annotated_image': result_b64,
            'details': {
                'threshold': best_threshold,
                'oil_pixels': oil_px,
                'total_pixels': total_px
            }
        })

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask ML Service on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True)
