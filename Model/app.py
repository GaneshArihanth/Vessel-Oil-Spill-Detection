# 🛢️ SpillGuard - AI Oil Spill Detection Interface (Optimized)
import os
import io
import cv2
import torch
import numpy as np
import gradio as gr
import matplotlib.pyplot as plt
from PIL import Image
import segmentation_models_pytorch as smp
import albumentations as A
from albumentations.pytorch.transforms import ToTensorV2

# -----------------------------
# Global Settings
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
best_threshold = 0.65  # fallback; may be overwritten by checkpoint

# -----------------------------
# Model Loader
# -----------------------------
def load_spillguard_model():
    """
    Load DeepLabV3+ (ResNet-50) model trained with 3 input channels.
    Tries multiple checkpoint paths; sets model to eval().
    """
    global best_threshold
    net = smp.DeepLabV3Plus(
        encoder_name="resnet50",
        encoder_weights="imagenet",
        in_channels=3,   # trained for 3 channels
        classes=1
    ).to(device)

    checkpoint_files = [
        "deeplabv3p_best.pth",
        "spillguard_enhanced_final.pth",
        "spillguard_best.pth",
        "/content/drive/MyDrive/oilspill_ckpts/deeplabv3p_best.pth"
    ]

    for ckpt_file in checkpoint_files:
        try:
            if os.path.exists(ckpt_file):
                print(f"🔍 Found model file: {ckpt_file}")
                checkpoint = torch.load(ckpt_file, map_location=device)

                # common save formats
                if "model_state_dict" in checkpoint:
                    net.load_state_dict(checkpoint["model_state_dict"])
                    best_threshold = float(checkpoint.get("best_threshold", best_threshold))
                    print(f"✅ Loaded model_state_dict (best_t={best_threshold})")
                elif "model" in checkpoint:
                    state_dict = checkpoint["model"]
                    if isinstance(state_dict, dict):
                        net.load_state_dict(state_dict)
                    else:
                        net.load_state_dict({k: v.to(device) for k, v in state_dict.items()})
                    # some runs store the best validation dice here; keep fallback
                    best_threshold = float(checkpoint.get("best_threshold", best_threshold))
                    print(f"✅ Loaded model dict (best_t={best_threshold})")
                else:
                    net.load_state_dict(checkpoint, strict=False)
                    print("✅ Loaded direct state_dict")

                net.eval()
                return net
        except Exception as e:
            print(f"⚠️ Failed to load from {ckpt_file}: {e}")

    print("⚠️ No trained model found. Using untrained model for demo.")
    net.eval()
    return net

# -----------------------------
# Preprocessing
# -----------------------------
def preprocess_image(image):
    """
    Convert input to 3-channel SAR-like tensor with percentile normalization.
    Returns:
      - img_tensor: torch tensor [1, 3, H, W] on device
      - img_gray: 2D float32 image in [0,1] (original-res grayscale for stats/overlay)
    """
    IMG_SIZE = 512

    # PIL → numpy
    if isinstance(image, Image.Image):
        # drop alpha if present
        if image.mode in ("RGBA", "LA"):
            image = image.convert("RGB")
        img_array = np.array(image)
    else:
        img_array = image

    # to grayscale (assume RGB if 3 channels)
    if img_array.ndim == 3:
        if img_array.shape[2] == 4:
            img_array = img_array[..., :3]
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        img_gray = img_array

    # normalize [0,1]
    img_gray = img_gray.astype(np.float32)
    if img_gray.max() > 1.0:
        img_gray /= 255.0

    # SAR-like percentile stretch
    lo, hi = np.percentile(img_gray, [1, 99])
    if hi > lo:
        img_gray = np.clip(img_gray, lo, hi)
        img_gray = (img_gray - lo) / max(hi - lo, 1e-6)
    else:
        mmin, mptp = float(img_gray.min()), float(np.ptp(img_gray))
        img_gray = (img_gray - mmin) / (mptp + 1e-6)

    # replicate to 3 channels
    img_3ch = np.stack([img_gray, img_gray, img_gray], axis=2)  # (H, W, 3)

    # resize/pad → tensor
    transform = A.Compose([
        A.LongestMaxSize(max_size=IMG_SIZE, interpolation=cv2.INTER_CUBIC),
        A.PadIfNeeded(IMG_SIZE, IMG_SIZE, border_mode=cv2.BORDER_REFLECT_101),
        A.ToFloat(max_value=1.0),
        ToTensorV2(),
    ])
    transformed = transform(image=img_3ch)
    img_tensor = transformed["image"].unsqueeze(0).to(device)  # [1, 3, H, W]

    return img_tensor, img_gray

# -----------------------------
# Inference + Visualization
# -----------------------------
@torch.no_grad()
def detect_oil_spill(image, threshold):
    """
    Run model inference on the uploaded image and return:
      - result image with panels
      - markdown summary
    """
    global model

    if model is None:
        return None, "❌ Model not loaded. Please restart the interface."

    try:
        # preserve original array for sizing and overlay
        original = np.array(image) if isinstance(image, Image.Image) else image
        if original.ndim == 3 and original.shape[2] == 4:
            original = original[..., :3]
        oh, ow = original.shape[:2]

        # preprocess → [1,3,H,W]
        x, img_gray_proc = preprocess_image(image)  # resized internally
        logits = model(x)                           # [1,1,H,W]
        prob = torch.sigmoid(logits)[0, 0].cpu().numpy()  # (H, W)

        # resize prob back to original size
        prob_resized = cv2.resize(prob, (ow, oh), interpolation=cv2.INTER_LINEAR)
        mask = (prob_resized >= float(threshold)).astype(np.uint8)

        # original to grayscale for overlay
        if original.ndim == 3:
            orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        else:
            orig_gray = original
        if orig_gray.max() > 1:
            orig_gray = (orig_gray.astype(np.float32) / 255.0)

        # overlay
        base = (orig_gray * 255).astype(np.uint8)
        overlay_rgb = cv2.cvtColor(base, cv2.COLOR_GRAY2RGB)
        overlay_colored = overlay_rgb.copy()
        overlay_colored[mask == 1] = [255, 0, 0]
        blended = cv2.addWeighted(overlay_rgb, 0.7, overlay_colored, 0.3, 0)

        # stats
        total_px = mask.size
        oil_px = int(mask.sum())
        oil_pct = 100.0 * oil_px / max(total_px, 1)
        conf_max = float(prob_resized.max())
        conf_mean = float(prob_resized.mean())

        # figure
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("SpillGuard Oil Spill Detection Results", fontsize=16, fontweight="bold")

        axes[0, 0].imshow(orig_gray, cmap="gray")
        axes[0, 0].set_title(f"Input Image ({ow}×{oh})")
        axes[0, 0].axis("off")

        im1 = axes[0, 1].imshow(prob_resized, cmap="hot", vmin=0, vmax=1)
        axes[0, 1].set_title("Oil Spill Probability")
        axes[0, 1].axis("off")
        plt.colorbar(im1, ax=axes[0, 1], fraction=0.046)

        axes[1, 0].imshow(mask, cmap="Reds", vmin=0, vmax=1)
        axes[1, 0].set_title(f"Detection (Threshold: {float(threshold):.2f})")
        axes[1, 0].axis("off")

        axes[1, 1].imshow(blended)
        axes[1, 1].set_title("Oil Spill Overlay")
        axes[1, 1].axis("off")

        plt.tight_layout()

        # to PIL for Gradio
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        plt.close()
        result_image = Image.open(buf)

        results_text = f"""
🛢️ **SpillGuard Detection Results**

📊 **Image Info:**
• Original Size: {ow} × {oh} pixels  
• Processing: Resized to 512×512 for model, results scaled back

📊 **Detection Statistics:**
• Oil Coverage: {oil_pct:.2f}% of image  
• Oil Pixels: {oil_px:,} / {total_px:,}  
• Max Confidence: {conf_max:.3f}  
• Average Probability: {conf_mean:.3f}

🎯 **Assessment:**
• Threshold Used: {float(threshold):.2f}  
• Severity: {'HIGH' if oil_pct > 10 else 'MODERATE' if oil_pct > 5 else 'LOW' if oil_pct > 1 else 'MINIMAL'}

**Status:** {'🚨 OIL SPILL DETECTED' if oil_pct > 1 else '✅ No significant oil detected'}
        """.strip()

        return result_image, results_text

    except Exception as e:
        return None, f"❌ **Error during detection:** {str(e)}"

# -----------------------------
# Gradio UI
# -----------------------------
def create_spillguard_interface():
    with gr.Blocks(title="SpillGuard - Oil Spill Detection System",
                   theme=gr.themes.Soft()) as interface:

        gr.Markdown("""
        # 🛢️ SpillGuard - AI Oil Spill Detection System

        Upload a SAR (Synthetic Aperture Radar) image to detect potential oil spills.
        The model processes at 512×512 and scales results back to the original size.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(label="Upload SAR Image", type="pil", height=300)
                threshold_slider = gr.Slider(0.1, 0.9, value=float(best_threshold),
                                             step=0.05, label="Detection Threshold")
                detect_btn = gr.Button("🔍 Detect Oil Spills", variant="primary", size="lg")

                gr.Markdown("""
                ### Instructions
                1. Upload any size SAR satellite image  
                2. Adjust detection threshold (0.65 recommended)  
                3. Click "Detect Oil Spills"
                """)

            with gr.Column(scale=2):
                result_image = gr.Image(label="Detection Results", height=500)
                result_text = gr.Markdown("Upload an image and click 'Detect Oil Spills' to see results here.")

        detect_btn.click(fn=detect_oil_spill,
                         inputs=[image_input, threshold_slider],
                         outputs=[result_image, result_text])

        gr.Markdown("""
        ---
        ⚠️ Note: This is an AI-based analysis. For critical decisions, please verify with additional sources.
        """)

    return interface

# -----------------------------
# Bootstrap
# -----------------------------
if __name__ == "__main__":
    print("🔄 Initializing SpillGuard...")
    loaded_model = load_spillguard_model()
    if loaded_model is not None:
        model = loaded_model
        print(f"✅ SpillGuard model ready! Using threshold: {best_threshold}")
        app = create_spillguard_interface()
        app.launch(share=True, debug=True)
    else:
        print("❌ Failed to load SpillGuard model.")