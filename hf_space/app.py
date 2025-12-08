# -----------------------------
# Imports
# -----------------------------
import os
import io
import cv2
import torch
import numpy as np
import requests
import json
import base64
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
from pymongo import MongoClient
import segmentation_models_pytorch as smp
import albumentations as A
from albumentations.pytorch.transforms import ToTensorV2

# -----------------------------
# Configuration
# -----------------------------
app = Flask(__name__, static_folder='static/assets', template_folder='templates')
CORS(app)

# Environment Variables (Set these in HF Space Settings)
MONGO_URI = os.getenv("MONGO_URI")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = 'vessels1.p.rapidapi.com'

# MongoDB Setup
mongo_client = None
VesselCache = None
VesselHistory = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client.get_default_database()
        VesselCache = db['vesselcaches']
        VesselHistory = db['vesselhistories']
        # Create TTL index for Cache (24h)
        VesselCache.create_index("cachedAt", expireAfterSeconds=86400)
        print("Connected to MongoDB")
    except Exception as e:
        print(f"MongoDB Connection Failed: {e}")

# Global Model Vars
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
best_threshold = 0.65

# -----------------------------
# Model Logic (Existing)
# -----------------------------
def load_model():
    global model, best_threshold
    net = smp.DeepLabV3Plus(
        encoder_name="resnet50",
        encoder_weights="imagenet",
        in_channels=3,
        classes=1
    ).to(device)

    # Checkpoints
    checkpoint_files = ["deeplabv3p_best.pth", "spillguard_enhanced_final.pth"]
    for ckpt_file in checkpoint_files:
        if os.path.exists(ckpt_file):
            try:
                print(f"Loading model from {ckpt_file}...")
                checkpoint = torch.load(ckpt_file, map_location=device)
                if "model_state_dict" in checkpoint:
                    net.load_state_dict(checkpoint["model_state_dict"])
                    best_threshold = float(checkpoint.get("best_threshold", best_threshold))
                else:
                    net.load_state_dict(checkpoint, strict=False)
                
                net.eval()
                model = net
                print(f"Model loaded. Threshold: {best_threshold}")
                return
            except Exception as e:
                print(f"Failed to load {ckpt_file}: {e}")

    print("Warning: No trained model found.")
    net.eval()
    model = net

load_model()

def preprocess_image(image):
    IMG_SIZE = 512
    if isinstance(image, Image.Image):
        image = image.convert("RGB")
        img_array = np.array(image)
    else:
        img_array = image

    if img_array.ndim == 3:
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        img_gray = img_array

    img_gray = img_gray.astype(np.float32)
    if img_gray.max() > 1.0: img_gray /= 255.0

    img_3ch = np.stack([img_gray, img_gray, img_gray], axis=2)

    transform = A.Compose([
        A.LongestMaxSize(max_size=IMG_SIZE, interpolation=cv2.INTER_CUBIC),
        A.PadIfNeeded(IMG_SIZE, IMG_SIZE, border_mode=cv2.BORDER_REFLECT_101),
        A.ToFloat(max_value=1.0),
        ToTensorV2(),
    ])
    transformed = transform(image=img_3ch)
    return transformed["image"].unsqueeze(0).to(device), img_gray

# -----------------------------
# Backend Logic (Ported from Node.js)
# -----------------------------
NAME_TO_MMSI = {
    'EVER GIVEN': '353136000',
    'COMPASS': '244110352',
    'EVERGREEN': '353136000'
}

def fetch_weather(lat, lon):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"
        }
        resp = requests.get(url, params=params)
        return resp.json()
    except Exception as e:
        print(f"Weather error: {e}")
        return {}

def fetch_satellite_image(lat, lon):
    try:
        url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},17/1000x600?access_token={MAPBOX_ACCESS_TOKEN}"
        resp = requests.get(url)
        return resp.content # Bytes
    except Exception as e:
        print(f"Mapbox error: {e}")
        return None

def run_ml_inference(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        ow, oh = image.size
        img_tensor, _ = preprocess_image(image)
        
        with torch.no_grad():
            logits = model(img_tensor)
            prob = torch.sigmoid(logits)[0, 0].cpu().numpy()
        
        prob_resized = cv2.resize(prob, (ow, oh), interpolation=cv2.INTER_LINEAR)
        mask = (prob_resized >= best_threshold).astype(np.uint8)
        
        # Stats
        total_px = mask.size
        oil_px = int(mask.sum())
        oil_pct = (oil_px / total_px) * 100 if total_px > 0 else 0
        is_spill = oil_pct > 1.0

        # Overlay
        orig_arr = np.array(image.convert("RGB"))
        gray_bg = cv2.cvtColor(orig_arr, cv2.COLOR_RGB2GRAY)
        gray_bg_rgb = cv2.cvtColor(gray_bg, cv2.COLOR_GRAY2RGB)
        overlay = gray_bg_rgb.copy()
        overlay[mask == 1] = [255, 0, 0]
        blended = cv2.addWeighted(gray_bg_rgb, 0.7, overlay, 0.3, 0)
        
        pil_res = Image.fromarray(blended)
        buf = io.BytesIO()
        pil_res.save(buf, format="PNG")
        res_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        return {
            'is_spill': is_spill,
            'oil_percentage': oil_pct,
            'confidence': float(prob_resized.max()),
            'analysisImage': res_b64
        }
    except Exception as e:
        print(f"ML Error: {e}")
        return {'error': str(e)}

@app.route('/api/vessel-position', methods=['GET'])
def get_vessel_position():
    query = request.args.get('name')
    if not query: return jsonify({'error': 'Name/MMSI required'}), 400

    mmsi = query if query.isdigit() and len(query) == 9 else NAME_TO_MMSI.get(query.upper())
    if not mmsi: return jsonify({'error': 'Vessel not found'}), 404

    # 1. Check Cache
    if VesselCache is not None:
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        cached = VesselCache.find_one({"mmsi": mmsi, "cachedAt": {"$gte": one_day_ago}}, sort=[("cachedAt", -1)])
        
        if cached:
            print("Cache HIT")
            sat_img = fetch_satellite_image(cached['latitude'], cached['longitude'])
            ml_data = run_ml_inference(sat_img) if sat_img else None
            
            resp_data = {
                "name": cached['name'], "mmsi": mmsi, "imo": cached['imo'],
                "latitude": cached['latitude'], "longitude": cached['longitude'],
                "speed": 0, "course": cached['cog'], "timestamp": cached['timestamp'],
                "weather": cached.get('weather'), "weatherDescription": cached.get('weatherdescription'),
                "temperature": cached.get('temperature'), "windspeed": cached.get('windspeed'),
                "humidity": cached.get('humidity'), "satelliteImage": base64.b64encode(sat_img).decode('utf-8') if sat_img else None,
                "oilSpillData": ml_data
            }
            return jsonify(resp_data)

    # 2. Fetch API
    print("Cache MISS - Fetching RapidAPI")
    try:
        api_url = f"https://vessels1.p.rapidapi.com/vessels/{mmsi}"
        headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}
        # Note: In production you would call the real API. For demo we skip complex parsing if key not working.
        
        # MOCK FALLBACK for safety if API key fails or quota exceeded
        # (Implementing simplified fetch)
        resp = requests.get(api_url, headers=headers)
        if resp.status_code != 200:
             raise Exception(f"RapidAPI Error: {resp.status_code}")
        
        data = resp.json().get('data', {})
        # Extract fields (simplified)
        vessel_data = {
            "mmsi": str(data.get('mmsi', mmsi)),
            "name": data.get('name', 'Unknown'),
            "imo": data.get('imo', 0),
            "latitude": float(data.get('last_position', {}).get('latitude', 0)),
            "longitude": float(data.get('last_position', {}).get('longitude', 0)),
            "course": float(data.get('last_position', {}).get('course', 0)),
            "timestamp": datetime.utcnow()
        }

        # Weather
        w_data = fetch_weather(vessel_data['latitude'], vessel_data['longitude'])
        
        # Satellite
        sat_img = fetch_satellite_image(vessel_data['latitude'], vessel_data['longitude'])
        ml_data = run_ml_inference(sat_img) if sat_img else None

        # Save to DB
        if VesselCache is not None:
            cache_entry = {
                "mmsi": mmsi, "name": vessel_data['name'], "imo": vessel_data['imo'],
                "latitude": vessel_data['latitude'], "longitude": vessel_data['longitude'],
                "cog": vessel_data['course'], "timestamp": vessel_data['timestamp'],
                "cachedAt": datetime.utcnow(),
                "weather": w_data.get('weather', [{}])[0].get('main'),
                "weatherdescription": w_data.get('weather', [{}])[0].get('description'),
                "temperature": w_data.get('main', {}).get('temp'),
                "windspeed": w_data.get('wind', {}).get('speed'),
                "humidity": w_data.get('main', {}).get('humidity')
            }
            VesselCache.insert_one(cache_entry)

        return jsonify({
            **vessel_data,
            "weather": w_data.get('weather', [{}])[0].get('main'),
            "weatherDescription": w_data.get('weather', [{}])[0].get('description'),
            "temperature": w_data.get('main', {}).get('temp'),
            "windspeed": w_data.get('wind', {}).get('speed'),
            "humidity": w_data.get('main', {}).get('humidity'),
            "satelliteImage": base64.b64encode(sat_img).decode('utf-8') if sat_img else None,
            "oilSpillData": ml_data
        })

    except Exception as e:
        print(f"API Fetch Error: {e}")
        return jsonify({'error': 'Failed to fetch data'}), 500

# -----------------------------
# Static Files (Frontend)
# -----------------------------
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Serve assets from 'static/assets'
    if os.path.exists(os.path.join('static/assets', path)):
         return send_from_directory('static/assets', path)
    return send_from_directory('templates', path) # Fallback

if __name__ == '__main__':
    print("Starting Full Stack App on port 7860...")
    app.run(host='0.0.0.0', port=7860, debug=False)

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
    print("Starting Flask ML Service on port 7860...")
    app.run(host='0.0.0.0', port=7860, debug=False)
