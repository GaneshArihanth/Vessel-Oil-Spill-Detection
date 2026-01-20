# 🚢 Vessel Anomaly Detection System 

> **Empowering Maritime Intelligence with Real-Time Data & AI-Powered Surveillance**

**Vessel Anomaly Detection** is a comprehensive maritime tracking and analysis platform designed to provide real-time insights into vessel movements, environmental conditions, and **AI-driven Oil Spill Detection**. By integrating multiple data sources (Satellite, Weather, AIS), it offers a holistic view of maritime activities, aiding in navigation, ecological monitoring, and decision-making.

The application features a modern **React** frontend with glowing interactive cards, a **Node.js** backend for data orchestration, and a **Python/Flask Microservice** for deep-learning-based oil spill analysis.

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)
[![React](https://img.shields.io/badge/React-19.x-blue)](https://react.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-DeepLabV3+-ee4c2c)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/Hugging_Face-Spaces-yellow)](https://huggingface.co/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green)](https://nodejs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)](https://www.mongodb.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4.0-38B2AC)](https://tailwindcss.com/)

---

## 🧐 What is this Project? (For Beginners)

Imagine **Google Maps for ships**, but with a superpower: it can automatically detect **Oil Spills** from space using Artificial Intelligence.

This application does three main things:
1.  **Tracks Ships**: It finds out where a ship is right now using its unique ID (like a license plate).
2.  **Sees from Space**: It captures a satellite photo of that exact location.
3.  **Detects Pollution**: It uses a "Brain" (AI Model) to scan that photo. If it sees an oil spill, it highlights it in red and warns us.

---

## 📚 Glossary: Key Terms Explained

Before you dive into the technical details, here are some terms you might see:

-   **MMSI (Maritime Mobile Service Identity)**:
    -   *Think of it as:* A **Phone Number** for a ship. Every ship has a unique 9-digit number. We use this to find them.
-   **AIS (Automatic Identification System)**:
    -   *Think of it as:* **GPS for ships**. Ships constantly broadcast "I am here!" signals. We listen to these to know their location.
-   **Semantic Segmentation (The AI Part)**:
    -   *Think of it as:* A **Digital Highlighter**. Instead of just saying "There is oil," our AI colors the exact pixels of the image where the oil is, separating it from the water.
-   **API (Application Programming Interface)**:
    -   *Think of it as:* A **Waiter** in a restaurant. We (the customer) ask the waiter (API) for data (food) from the kitchen (Server), and they bring it back to us.

---

## 🌟 Key Features

### 🖥️ Modern User Interface
*   **Interactive Dashboard**: A sleek, dark-themed dashboard with glowing card effects (Aceternity UI).
*   **Visual Analytics**: Real-time visualization of vessel status, weather, and AI analysis.

### 📍 Core Functionality
*   **Real-Time Vessel Tracking**: Track vessels globally by MMSI or Name (via RapidAPI/MarineTraffic).
*   **🛰️ Satellite Visuals**: Fetch high-res satellite imagery from Mapbox for the vessel's current coordinates.
*   **🌤️ Live Weather**: Real-time environmental data (Wind, Temp, Pressure) from OpenWeatherMap.

### 🧠 AI Oil Spill Detection (New!)
*   **Deep Learning Model**: Uses **DeepLabV3+** (ResNet50 encoder) to segment oil spills from satellite imagery.
*   **Real-Time Inference**: Analyzes satellite images on-the-fly to detect potential anomalies.
*   **Visual Overlay**: Generates a grayscale analysis map with **Red Highlights** for detected spills.
*   **Risk Assessment**: Calculates confidence score and percentage of oil coverage.

### ⚙️ Backend & Performance
*   **Smart Caching (MongoDB)**: Caches vessel data for **24 hours** to minimize API costs and rate limits.
*   **Microservice Architecture**: Decouples the heavy ML inference (Python) from the main application logic (Node.js).
*   **Mock Data Engine**: Includes a resilient fallback system. If external APIs (AIS/Weather) are down or rate-limited, the system automatically serves realistic "Mock Data" to ensure the UI never breaks during demos.

---

## 📖 User Manual: How to Use

Once the app is running (see Quick Start), here is how to play with it:

### 1. The Search Bar
*   **Search by Name**: Type a ship name like `COMPASS` or `EVER GIVEN`.
*   **Search by ID**: Type a 9-digit MMSI number (e.g., `244110352`).
*   *Tip*: If you don't know any ships, just click "Search" with the default example to see a demo.

### 2. The Dashboard Cards
*   **🚢 Vessel Details**: Shows the static info (Flag, Dimensions, Type).
*   **📍 Live Position**: Shows coordinates. Updates every few seconds if the ship is moving.
*   **🌤️ Weather**: Real-time wind and temperature at that exact spot in the ocean.
*   **🛰️ Satellite View**: The coolest part! It pulls the latest available satellite shot.

### 3. Interpreting the AI Analysis
The bottom card shows the **Oil Spill Analysis**.
*   **✅ No Spill Detected**:
    *   **Status**: Green Badge.
    *   **Meaning**: The AI looked at the water and saw only water.
*   **⚠️ OIL SPILL DETECTED**:
    *   **Status**: Red Flashing Badge.
    *   **Visual**: You will see a **Red Heatmap** overlaid on the satellite image.
    *   **Action**: This indicates a high probability of pollution.

---


## 🏗️ Architecture

The system uses a Microservices approach. Think of it as a team working together:

| Component | Role | Analogy | Tech Stack |
| :--- | :--- | :--- | :--- |
| **Frontend** | **The Face** | The **Waiter** who shows you the menu. | React 19, Vite, Tailwind CSS |
| **Backend** | **The Manager** | The **Kitchen Manager** who organizes orders. | Node.js, Express, MongoDB |
| **ML Service** | **The Brain** | The **Specialist Chef** who cooks the AI dish. | Python, Flask, PyTorch |

### 📂 Folder Structure

```
Vessel-Tracking/
├── frontend/             # 🎨 React + Vite Frontend
│   ├── src/components/   # UI Components (GlowingEffect, Boxes)
│   └── src/App.jsx       # Main Dashboard UI
├── final-version/        # 🚀 Node.js Backend (API Gateway)
│   ├── server.js         # Express Server & caching logic
│   └── db.js             # MongoDB Schema & Connection
├── hf_space/             # 🧠 Deployment Bundle (All-in-One)
│   ├── app.py            # Combined Python Backend (ML + Logic)
│   ├── Dockerfile        # Container config for Hugging Face
│   ├── static/           # Built Frontend Assets
│   └── templates/        # Frontend HTML
├── Model/                # 🧪 Local ML Environment
│   ├── api.py            # Local Flask Interface for Model
│   └── deeplabv3p_best.pth # Trained Model Weights
├── package.json          # Root configuration
└── vercel.json           # Vercel Configuration
```

---

## 🧪 Technical Deep Dive

Why did we choose this specific tech stack?

### 1. The AI Model: DeepLabV3+
We didn't just pick any model; we chose **DeepLabV3+** because oil spills have irregular shapes and sizes.
*   **Why?**: It uses *Atrous Spatial Pyramid Pooling (ASPP)*.
*   **Translation**: It looks at the image with "different sized glasses" (zoom levels) simultaneously. This allows it to spot tiny oil leaks AND massive spills in the same image.

### 2. Frontend: React 19 + Vite
*   **Why?**: Speed. Traditional React apps can be slow to load.
*   **Vite**: Uses modern browser features to serve files instantly, making the dashboard feel "native" and snappy.
*   **Aceternity UI**: We used this library to give the "Glowing Glass" effect, which looks futuristic and matches the maritime theme.

### 3. Database: MongoDB with TTL
*   **Problem**: Storing every ship location forever would fill up the database in days.
*   **Solution**: **TTL (Time-To-Live) Indexes**.
*   **How it works**: We tell MongoDB, *"Delete any record that is older than 24 hours"*. This keeps our database small, free, and fast, acting like a self-cleaning cache.

---


## 🚀 Deployment Options

You can deploy this project in two ways:

### Option 1: Hugging Face Spaces (All-in-One) 🌟 *Recommended*
Host the **Entire Application** (Frontend + Backend + ML) in a single Docker container.

1.  **Create a Space**: Go to Hugging Face and create a new Space with the **Docker** SDK.
2.  **Upload Files**: Upload the contents of the `hf_space/` directory.
    *   *Important*: Ensure `deeplabv3p_best.pth` is included.
3.  **Environment Variables**: Set the following secrets in your Space settings:
    *   `MONGO_URI`, `MAPBOX_ACCESS_TOKEN`, `WEATHER_API_KEY`, `RAPIDAPI_KEY`
4.  **Run**: The Space will build and serve your app on port 7860.

### Option 2: Vercel + Hugging Face (Split)
Host Frontend/Backend on Vercel and ML Service on Hugging Face.

1.  **ML Service**: Deploy `hf_space/` to Hugging Face (Port 7860).
2.  **Frontend/Backend**: Deploy the root repo to **Vercel**.
    *   Set `ML_SERVICE_URL` in Vercel to your Hugging Face Space URL.

---

## 🛠️ Local Setup (Quick Start)

We will set this up using **3 separate terminals**, because each part of the "Team" needs its own space to run.

### Prerequisites
*   Node.js (v18+) & npm
*   Python (3.9+)
*   MongoDB Atlas URI
*   API Keys (Mapbox, OpenWeatherMap, RapidAPI)

### 1. Install Dependencies & Setup

**Terminal 1: The Brain (ML Service)**
```bash
python -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -r hf_space/requirements.txt
# Run the ML API
python Model/api.py
```
*Runs on Port 5001*

**Terminal 2: The Manager (Backend)**
```bash
cd final-version
npm install
# Create .env file here with your API Keys
node server.js
```
*Runs on Port 3000*

**Terminal 3: The Face (Frontend)**
```bash
cd frontend
npm install
npm run dev
```
*Runs on Port 5173. Click the link to view the app!*

---

## 📡 API Endpoints

### `GET /api/vessel-position`
Returns vessel data + ML analysis.

**Params**: `?name=COMPASS` or `?name=244110352` (MMSI)

**Response**:
```json
{
  "name": "COMPASS",
  "mmsi": "244110352",
  "latitude": 53.259,
  "longitude": 6.497,
  "satelliteImage": "<base64>",
  "oilSpillData": {
    "is_spill": true,
    "confidence": 0.89,
    "analysisImage": "<base64_overlay>"
  }
}
```

---

## ❓ Troubleshooting

### 1. "Loading..." Forever / Black Screen
*   **Cause**: The Frontend cannot talk to the Backend.
*   **Fix**: Check **Terminal 2**. Is the server running? Did it crash?

### 2. `405 Method Not Allowed` on Hugging Face
*   **Cause**: The static file handler is catching the API request.
*   **Fix**: Ensure `app.route('/predict')` is defined **before** `app.route('/<path:path>')` in `app.py`. (Fixed in V3).

### 3. Missing API Keys / Mock Data
*   **Symptoms**: Weather says "N/A" or "Mock Data".
*   **Fix**: The system automatically switches to **Mock Data** if keys are missing to prevent crashing. Double-check your `.env` file to see real data.

---



## 🗺️ Future Roadmap

We are constantly improving! Here is what's coming next:

- [ ] **🔔 SMS/Email Alerts**: Automatically notify authorities when a spill > 50% confidence is detected.
- [ ] **⏪ Historical Playback**: A "Time Slider" to watch a ship's path over the last 30 days.
- [ ] **🛰️ Multi-Satellite Support**: Integration with **Sentinel-1 (Radar)**. Radar can see oil spills even through clouds and at night!
- [ ] **📱 Mobile App**: A React Native version for Coast Guard officers on patrol.

---

## 👤 Author

**Ganesh Arihanth**
*   [GitHub Profile](https://github.com/GaneshArihanth)
*   [Hugging Face Space](https://huggingface.co/spaces/GaneshArihanth/Vessel-Oil-Spill-Detection-API)

---
