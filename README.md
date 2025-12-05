# 🚢 Vessel Anomaly Detection System

> **Empowering Maritime Intelligence with Real-Time Data & Analytics**

**Vessel Anomaly Detection System** is a comprehensive maritime tracking and analysis platform designed to provide real-time insights into vessel movements, environmental conditions, and satellite imagery. By integrating multiple data sources, it offers a holistic view of maritime activities, aiding in navigation, monitoring, and decision-making.

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)
[![React](https://img.shields.io/badge/React-18.x-blue)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.x-purple)](https://vitejs.dev/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green)](https://nodejs.org/)
[![Express](https://img.shields.io/badge/Express-4.x-black)](https://expressjs.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)](https://www.mongodb.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-4.0-38B2AC)](https://tailwindcss.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-black)](https://vercel.com/)

The application features a modern, responsive user interface with **glowing interactive cards** and a robust backend that handles data caching and rate limiting to ensure reliability.

---

## 🌟 Key Features

### 🖥️ Modern User Interface
*   **Interactive Dashboard**: A sleek, dark-themed dashboard with glowing card effects that react to user interaction.
*   **Real-Time Updates**: Instant visualization of vessel data.
*   **Responsive Design**: Optimized for various screen sizes.

### 📍 Core Functionality
*   **Real-Time Vessel Tracking**: Track vessels globally using their MMSI number or name.
*   **🛰️ Satellite Imagery**: Fetch high-resolution satellite images of vessel locations on demand.
*   **🌤️ Live Weather**: Access real-time weather conditions (temperature, wind, humidity) for any vessel's location.

### ⚙️ Backend & Performance
*   **Smart Caching**: Uses MongoDB Atlas to cache vessel data, reducing API calls and latency.
*   **TTL Indexing**: Automatically expires stale data after **1 hour**.
*   **Rate Limit Protection**: Intelligent fallback mechanisms to prevent API exhaustion.
*   **Mock Data Fallback**: Ensures the application remains functional even when external APIs are down.

---

## 📂 Folder Structure

```
AISvessels-backed/
├── .env                  # Environment variables (API Keys)
├── vercel.json           # Vercel deployment configuration
├── final-version/        # Backend (Express.js)
│   ├── server.js         # Main server entry point
│   ├── db.js             # Database connection
│   └── .env              # Backend-specific env (optional)
└── frontend/             # Frontend (React + Vite)
    ├── src/
    │   ├── components/   # UI Components (GlowingEffect, Boxes)
    │   ├── App.jsx       # Main application logic
    │   └── App.css       # Global styles
    └── vite.config.js    # Vite configuration
```

---

## 🛠️ Tech Stack

*   **Frontend**: [React](https://react.dev/), [Vite](https://vitejs.dev/), [Framer Motion](https://www.framer.com/motion/) (Animations), [Tailwind CSS](https://tailwindcss.com/) (Styling)
*   **Backend**: [Express.js](https://expressjs.com/), [Node.js](https://nodejs.org/)
*   **Database**: [MongoDB Atlas](https://www.mongodb.com/atlas)
*   **Deployment**: [Vercel](https://vercel.com/)

---

## 🚀 Getting Started

Follow these steps to run the project locally.

### Prerequisites
*   Node.js (v18+)
*   MongoDB Connection String
*   API Keys (OpenWeatherMap, Mapbox, RapidAPI)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd AISvessels-backed
    ```

2.  **Install Dependencies**
    ```bash
    # Install Backend Dependencies
    cd final-version
    npm install

    # Install Frontend Dependencies
    cd ../frontend
    npm install
    ```

3.  **Configure Environment Variables**
    Create a `.env` file in the **root directory** with the following keys:
    ```env
    PORT=3000
    WEATHER_API_KEY=your_weather_api_key
    MAPBOX_ACCESS_TOKEN=your_mapbox_token
    RAPIDAPI_KEY=your_rapidapi_key
    ```

4.  **Start the Application**
    You need to run both backend and frontend.

    **Terminal 1 (Backend):**
    ```bash
    cd final-version
    npm start
    ```

    **Terminal 2 (Frontend):**
    ```bash
    cd frontend
    npm run dev
    ```

5.  **Access the App**
    Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📡 API Documentation

The backend exposes a unified endpoint for fetching vessel data.

### `GET /api/vessel-position`

Fetches real-time data for a specific vessel.

**Query Parameters:**
*   `name`: The MMSI (9 digits) or name of the vessel.

**Example Request:**
```http
GET /api/vessel-position?name=244110352
```

**Example Response:**
```json
{
  "name": "COMPASS",
  "mmsi": "244110352",
  "latitude": 53.259,
  "longitude": 6.497,
  "speed": 12.5,
  "course": 91,
  "weather": "Clouds",
  "temperature": 15,
  "satelliteImage": "base64_encoded_image_string..."
}
```

---

## ☁️ Deployment on Vercel

This project is configured for easy deployment on Vercel.

1.  **Push to GitHub**: Ensure your code is pushed to a GitHub repository.
2.  **Import Project**: Go to Vercel Dashboard and import your repository.
3.  **Environment Variables**: In Vercel Project Settings, add the variables from your `.env` file:
    *   `WEATHER_API_KEY`
    *   `MAPBOX_ACCESS_TOKEN`
    *   `RAPIDAPI_KEY`
4.  **Deploy**: Click **Deploy**. Vercel will automatically detect the `vercel.json` configuration and build both the frontend and backend.

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

This project is licensed under the ISC License.
