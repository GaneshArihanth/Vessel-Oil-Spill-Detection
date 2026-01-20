---
title: Spillguard Oil Detection
emoji: 🌍
colorFrom: purple
colorTo: gray
sdk: gradio
sdk_version: 5.49.0
app_file: app.py
pinned: false
---
# 🛢️ **AI SpillGuard – Intelligent Oil Spill Detection System**
# 🚀 *Deep Learning powered environmental monitoring for marine safety*

---

## 🌍 Overview
**AI SpillGuard** is an advanced deep learning system designed to detect oil spills in **Synthetic Aperture Radar (SAR)** satellite images.  
It leverages **DeepLabV3+ (ResNet50)** architecture trained on custom SAR datasets, with advanced preprocessing, threshold optimization, and postprocessing for accurate segmentation.

The system provides:
- ✅ **Automatic detection of oil spill regions**
- 🎯 **Dynamic threshold tuning** for optimal precision/recall balance
- 🌊 **Real-time visualization** with probability heatmaps and overlay masks
- 🧠 **Deployable web interface** (via **Gradio + Hugging Face Spaces**)

---

## 🧠 Model Highlights
| Component | Description |
|------------|--------------|
| **Architecture** | DeepLabV3+ (ResNet50 backbone) |
| **Framework** | PyTorch + Segmentation Models PyTorch |
| **Input Type** | SAR (Grayscale → 3-Channel Tensor) |
| **Loss Function** | BCE + Dice Hybrid Loss |
| **Optimization** | AdamW + CosineAnnealingLR |
| **Key Metrics** | Dice Coefficient, mIoU, Precision, Recall |
| **Threshold** | Optimized at `t = 0.65` for best Dice (~0.92) |

---

## 🧩 Features
✅ Upload any **SAR image (any size)** – the model automatically rescales and normalizes  
✅ **Threshold slider** to adjust detection sensitivity  
✅ **Overlay view** highlighting detected oil regions in red  
✅ **Statistical summary** of detection confidence and oil coverage percentage  
✅ **Interactive Gradio UI** – lightweight and deployable anywhere  

---

## 🖼️ Web Interface Preview
| Upload SAR Image | Probability Heatmap | Binary Mask | Oil Spill Overlay |
|:----------------:|:-------------------:|:------------:|:-----------------:|
| ![Input](https://huggingface.co/datasets/hf-internal-testing/example-images/resolve/main/satellite.jpg) | ![Heatmap](https://huggingface.co/datasets/hf-internal-testing/example-images/resolve/main/heatmap.jpg) | ![Mask](https://huggingface.co/datasets/hf-internal-testing/example-images/resolve/main/mask.jpg) | ![Overlay](https://huggingface.co/datasets/hf-internal-testing/example-images/resolve/main/overlay.jpg) |

---

## ⚙️ Installation

If you want to test locally (no deployment needed):

```bash
git clone https://huggingface.co/spaces/<your_username>/SpillGuard
cd SpillGuard
pip install -r requirements.txt
python app.py

Then visit:
http://127.0.0.1:7860

## 🧠 How It Works

1.SAR Preprocessing
   --Converts image to grayscale
   --Normalizes intensities (1–99 percentile clipping)
   --Expands to 3 channels (for ResNet backbone compatibility)

2.Model Inference
   --DeepLabV3+ predicts oil probability map (512×512)
   --Resized back to original image dimensions

3.Post-Processing
   --Threshold applied to obtain binary segmentation
   --Overlay generated for intuitive visualization
   --Key statistics displayed (oil area %, confidence, severity)

🧭 Project Structure

SpillGuard/
│
├── app.py                # Main Gradio App (ready for Hugging Face)
├── requirements.txt       # Dependencies list
├── deeplabv3p_best.pth    # Trained model weights


💡 Future Enhancements

   🌐 Integrate with real-time Sentinel-1 satellite APIs
   📦 Deploy a lightweight version for on-board drone inference
   🔔 Add anomaly detection & alert system
   📈 Include confidence heatmaps as downloadable results


🧑‍💻 Author

Developed by: Dilshad Ali
Field: Artificial Intelligence & Deep Learning
Focus: Environmental AI, Computer Vision, and Remote Sensing
GitHub: https://github.com/dilshadalikhan2004