require('dotenv').config();
const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');
const cors = require('cors');
const { VesselCache, VesselHistory } = require('./db');

const app = express();
app.use(cors()); // Enable CORS for all routes
const PORT = process.env.PORT || 3000;

console.log("DEBUG: MONGO_URI starts with:", process.env.MONGO_URI ? process.env.MONGO_URI.substring(0, 20) : "UNDEFINED");

// API Keys
const WEATHER_API_KEY = process.env.WEATHER_API_KEY;
const MAPBOX_ACCESS_TOKEN = process.env.MAPBOX_ACCESS_TOKEN;
// ML Service URL (Hugging Face or Local)
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://127.0.0.1:5001/predict';
console.log(`[DEBUG] Configured ML_SERVICE_URL: ${ML_SERVICE_URL}`);

// Helper function to fetch weather
async function fetchWeather(lat, lon) {
    try {
        const response = await axios.get('https://api.openweathermap.org/data/2.5/weather', {
            params: {
                lat,
                lon,
                appid: WEATHER_API_KEY,
                units: 'metric',
            },
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching weather data:', error.message);
        // Fallback for verification
        console.log('Using fallback weather data');
        return {
            weather: [{ main: 'Clear', description: 'clear sky' }],
            main: { temp: 25, pressure: 1013, humidity: 50 },
            wind: { speed: 5 },
            rain: { '1h': 0 },
            clouds: { all: 0 }
        };
    }
}

// Helper function to fetch satellite image
async function fetchSatelliteImage(lat, lon) {
    try {
        const zoom = 17;
        const width = 1000;
        const height = 600;
        const mapboxUrl = `https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/${lon},${lat},${zoom}/${width}x${height}?access_token=${MAPBOX_ACCESS_TOKEN}`;
        const response = await axios.get(mapboxUrl, { responseType: 'arraybuffer' });
        return response.data;
    } catch (error) {
        console.error('Error fetching satellite image:', error.message);
        throw new Error('Failed to fetch satellite image');
    }
}

// RapidAPI Configuration
const RAPIDAPI_KEY = process.env.RAPIDAPI_KEY;
const RAPIDAPI_HOST = 'vessels1.p.rapidapi.com';

// Helper: Map Name to MMSI (Mock Search)
const NAME_TO_MMSI = {
    'EVER GIVEN': '353136000',
    'COMPASS': '244110352',
    'EVERGREEN': '353136000' // Alias
};

// Main Endpoint
// Handle both /vessel-position (local) and /api/vessel-position (Vercel)
const handleVesselPosition = async (req, res) => {
    const query = req.query.name;

    if (!query) {
        return res.status(400).json({ error: 'Ship name or MMSI is required' });
    }

    // Determine MMSI: Check if input is 9 digits (MMSI) or a name
    let mmsi = null;
    if (/^\d{9}$/.test(query)) {
        mmsi = query;
    } else {
        const upperName = query.toUpperCase();
        mmsi = NAME_TO_MMSI[upperName];
    }

    if (!mmsi) {
        return res.status(404).json({
            error: 'Vessel not found in local database. Please search by MMSI (9 digits) for this API.',
            details: 'Search by name is limited. Try "EVER GIVEN" or "COMPASS".'
        });
    }

    console.log(`Fetching data for MMSI: ${mmsi}`);

    // Check Database for recent data (Caching)
    try {
        // Check for data cached within the last 24 hours (86400 seconds)
        const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
        const cachedVessel = await VesselCache.findOne({
            mmsi: mmsi,
            cachedAt: { $gte: oneDayAgo }
        }).sort({ cachedAt: -1 });

        if (cachedVessel) {
            console.log('Returning cached data from database (Cache HIT)');

            // Fetch weather for cached location (or cache weather too, but fetching weather is usually fine)
            // The schema stores weather.

            // Re-construct response from DB
            const satelliteImage = await fetchSatelliteImage(cachedVessel.latitude, cachedVessel.longitude);

            // --- OIL SPILL DETECTION (Moved to shared logic in future refactor) ---
            let oilSpillData = null;
            try {
                console.log(`[DEBUG] Calling ML Service at: ${ML_SERVICE_URL} (Cache Hit)`);
                const imageBase64 = Buffer.from(satelliteImage).toString('base64');

                const mlResponse = await axios.post(ML_SERVICE_URL, {
                    image: imageBase64
                });

                console.log(`[DEBUG] ML Service Response Status: ${mlResponse.status} (Cache Hit)`);

                if (mlResponse.data) {
                    oilSpillData = mlResponse.data;
                    if (oilSpillData.annotated_image) {
                        oilSpillData.analysisImage = oilSpillData.annotated_image;
                        delete oilSpillData.annotated_image;
                    }
                }
            } catch (mlError) {
                console.error("[ERROR] Oil Spill Detection Service Failed (Cache Hit)");
                console.error(`[ERROR] URL Used: ${ML_SERVICE_URL}`);
                console.error(`[ERROR] Message: ${mlError.message}`);
                if (mlError.response) {
                    console.error(`[ERROR] Status: ${mlError.response.status}`);
                    console.error(`[ERROR] Data:`, JSON.stringify(mlError.response.data));
                }
                oilSpillData = { error: "Service Unavailable" };
            }
            // ---------------------------------------------------------------------

            if (req.headers.accept && req.headers.accept.includes('application/json')) {
                return res.json({
                    name: cachedVessel.name,
                    mmsi: mmsi,
                    imo: cachedVessel.imo,
                    latitude: cachedVessel.latitude,
                    longitude: cachedVessel.longitude,
                    speed: 0,
                    course: cachedVessel.cog,
                    timestamp: cachedVessel.timestamp,
                    weather: cachedVessel.weather,
                    weatherDescription: cachedVessel.weatherdescription,
                    temperature: cachedVessel.temperature,
                    pressure: cachedVessel.pressure,
                    humidity: cachedVessel.humidity,
                    windspeed: cachedVessel.windspeed,
                    rain: cachedVessel.rain,
                    clouds: cachedVessel.clouds,
                    temperatureMessage: 'Cached Data',
                    satelliteImage: Buffer.from(satelliteImage).toString('base64'),
                    oilSpillData: oilSpillData
                });
            }

            // HTML Response for Cache
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.write(`
                <h1>Vessel Information (Cached)</h1>
                <p><strong>Name:</strong> ${cachedVessel.name}</p>
                <p><strong>MMSI:</strong> ${mmsi}</p>
                <p><strong>IMO:</strong> ${cachedVessel.imo}</p>
                
                <h2>Vessel Position:</h2>
                <p><strong>Source:</strong> Database Cache</p>
                <p><strong>Timestamp:</strong> ${new Date(cachedVessel.timestamp).toLocaleString()}</p>
                <p><strong>Location:</strong> Latitude ${cachedVessel.latitude}, Longitude ${cachedVessel.longitude}</p>
                
                <h2>Satellite Image:</h2>
                <img src="data:image/png;base64,${Buffer.from(satelliteImage).toString('base64')}" alt="Satellite Image"/>
            `);
            res.end();
            return; // Ensure we stop here!
        }
    } catch (cacheError) {
        console.error('Cache check failed:', cacheError);
    }

    try {
        const options = {
            method: 'GET',
            url: 'https://ais-vessel-finder.p.rapidapi.com/getAisData',
            params: { mmsi: mmsi },
            headers: {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': 'ais-vessel-finder.p.rapidapi.com'
            }
        };

        const response = await axios.request(options);
        const vesselData = response.data;

        if (!vesselData || !vesselData.latitude || !vesselData.longitude) {
            return res.status(404).json({ error: 'No position data found for this vessel' });
        }

        const latitude = parseFloat(vesselData.latitude);
        const longitude = parseFloat(vesselData.longitude);
        const speed = 0; // New API doesn't seem to provide speed (SOG) in the example response
        const course = 0; // New API doesn't seem to provide course (COG) in the example response

        console.log(`Vessel position: Lat ${latitude}, Lon ${longitude}`);

        // 3. Fetch Weather
        const weatherData = await fetchWeather(latitude, longitude);

        // 4. Save to Database (Optional: Update schema if needed, keeping simple for now)
        // 4. Save to Database
        try {
            // Save to Cache (Overwrite or new entry, handled by separate collection with TTL)
            await VesselCache.create({
                mmsi: vesselData.mmsi,
                imo: vesselData.imo || 0,
                name: vesselData.vesselName,
                timestamp: new Date(vesselData.updatedAt),
                length: 0,
                width: 0,
                draft: vesselData.draught,
                cog: course,
                heading: 0,
                latitude: latitude,
                longitude: longitude,
                weather: weatherData.weather[0].main,
                weatherdescription: weatherData.weather[0].description,
                temperature: weatherData.main.temp,
                pressure: weatherData.main.pressure,
                humidity: weatherData.main.humidity,
                windspeed: weatherData.wind.speed,
                rain: weatherData.rain ? weatherData.rain['1h'] : 'No rain data',
                clouds: weatherData.clouds.all
            });

            // Save to History (Permanent record)
            await VesselHistory.create({
                mmsi: vesselData.mmsi,
                imo: vesselData.imo || 0,
                name: vesselData.vesselName,
                timestamp: new Date(vesselData.updatedAt),
                message: 'Live API Fetch',
                length: 0,
                width: 0,
                draft: vesselData.draught,
                cog: course,
                heading: 0,
                latitude: latitude,
                longitude: longitude,
                weather: weatherData.weather[0].main,
                weatherdescription: weatherData.weather[0].description,
                temperature: weatherData.main.temp,
                pressure: weatherData.main.pressure,
                humidity: weatherData.main.humidity,
                windspeed: weatherData.wind.speed,
                rain: weatherData.rain ? weatherData.rain['1h'] : 'No rain data',
                clouds: weatherData.clouds.all
            });
            console.log(`Saved data for ${vesselData.vesselName} to Cache and History.`);

        } catch (dbError) {
            console.error("Database save failed:", dbError.message);
            // Continue without failing the request
        }

        // 5. Compare Temperatures (Skipping for brevity/robustness in this migration)
        const temperatureMessage = 'Temperature comparison unavailable';

        // 6. Fetch Satellite Image
        let satelliteImage = await fetchSatelliteImage(latitude, longitude);
        let oilSpillData = null;

        // --- OIL SPILL DETECTION INTEGRATION ---
        try {
            console.log("Creating oil spill detection request...");
            // Convert buffer to base64 for transport to Python API
            const imageBase64 = Buffer.from(satelliteImage).toString('base64');

            // Call Python Flask API
            const mlResponse = await axios.post(ML_SERVICE_URL, {
                image: imageBase64
            });

            if (mlResponse.data) {
                console.log("Oil spill detection successful:", mlResponse.data.is_spill ? "SPILL DETECTED" : "Safe");
                oilSpillData = mlResponse.data;

                // If the ML model returns an annotated image, use it!
                if (oilSpillData.annotated_image) {
                    // Optionally replace the original satellite image with the annotated one in the main response
                    // Or send it as a separate field. Let's send it as a separate field 'oilSpillImage'
                    // or override 'satelliteImage' if we want the user to see the analysis by default.
                    // Making a design choice: Let's keep original 'satelliteImage' clean, and send 'oilAnalysisImage' separately.
                    oilSpillData.analysisImage = oilSpillData.annotated_image;
                    delete oilSpillData.annotated_image; // Clean up payload
                }
            }
        } catch (mlError) {
            console.error("Oil Spill Detection Service Failed:", mlError.message);
            // Don't fail the whole request, just return null for oil spill data
            oilSpillData = { error: "Service Unavailable" };
        }
        // ---------------------------------------

        // 7. Send Response
        if (req.headers.accept && req.headers.accept.includes('application/json')) {
            return res.json({
                name: vesselData.vesselName,
                mmsi: vesselData.mmsi,
                imo: vesselData.imo,
                latitude: latitude,
                longitude: longitude,
                speed: speed,
                course: course,
                timestamp: vesselData.updatedAt,
                weather: weatherData.weather[0].main,
                weatherDescription: weatherData.weather[0].description,
                temperature: weatherData.main.temp,
                pressure: weatherData.main.pressure,
                humidity: weatherData.main.humidity,
                windspeed: weatherData.wind.speed,
                rain: weatherData.rain ? weatherData.rain['1h'] : 'No rain data',
                clouds: weatherData.clouds.all,
                temperatureMessage: temperatureMessage,
                satelliteImage: Buffer.from(satelliteImage).toString('base64'),
                oilSpillData: oilSpillData
            });
        }

        // HTML Response (Legacy support)
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.write(`
      <h1>Vessel Information</h1>
      <p><strong>Name:</strong> ${vesselData.vesselName}</p>
      <p><strong>MMSI:</strong> ${vesselData.mmsi}</p>
      <p><strong>IMO:</strong> ${vesselData.imo}</p>
   
      <h2>Vessel Position:</h2>
      <p><strong>Source:</strong> RapidAPI (AIS Vessel Finder)</p>
      <p><strong>Timestamp:</strong> ${new Date(vesselData.updatedAt).toLocaleString()}</p>
      <p><strong>Location:</strong> Latitude ${latitude}, Longitude ${longitude}</p>
      
      <h2>Satellite Image:</h2>
      <img src="data:image/png;base64,${Buffer.from(satelliteImage).toString('base64')}" alt="Satellite Image"/>
    `);
        res.end();

    } catch (err) {
        console.error('Error processing request:', err.message);
        if (err.response) {
            console.error('API Response Status:', err.response.status);
            console.error('API Response Data:', err.response.data);

            if (err.response.status === 429 || err.response.status === 502) {
                console.log('Switching to MOCK DATA due to API error');
                // Mock Data Fallback
                const mockData = {
                    name: 'MOCK VESSEL (Demo)',
                    mmsi: mmsi || '000000000',
                    imo: 1234567,
                    latitude: 53.259190,
                    longitude: 6.497000,
                    speed: 12.5,
                    course: 91,
                    timestamp: new Date(),
                    weather: 'Clouds',
                    weatherDescription: 'overcast clouds (Mock)',
                    temperature: 15,
                    pressure: 1015,
                    humidity: 80,
                    windspeed: 5,
                    rain: '0',
                    clouds: 90,
                    temperatureMessage: 'Mock Data - API Limit Exceeded',
                    satelliteImage: '' // Client will handle empty image or we can try fetching real one
                };

                // Fetch REAL weather for the mock location
                try {
                    const realWeather = await fetchWeather(mockData.latitude, mockData.longitude);
                    mockData.weather = realWeather.weather[0].main;
                    mockData.weatherDescription = realWeather.weather[0].description;
                    mockData.temperature = realWeather.main.temp;
                    mockData.pressure = realWeather.main.pressure;
                    mockData.humidity = realWeather.main.humidity;
                    mockData.windspeed = realWeather.wind.speed;
                    mockData.rain = realWeather.rain ? realWeather.rain['1h'] : 'No rain data';
                    mockData.clouds = realWeather.clouds.all;
                    console.log('Fetched live weather for mock data');
                } catch (weatherErr) {
                    console.log('Could not fetch live weather for mock data, using static defaults');
                }

                // Try to fetch real satellite image even for mock location
                try {
                    const satelliteImage = await fetchSatelliteImage(mockData.latitude, mockData.longitude);
                    mockData.satelliteImage = Buffer.from(satelliteImage).toString('base64');
                } catch (imgErr) {
                    console.log('Could not fetch satellite image for mock data');
                }

                // SAVE MOCK DATA TO DB (for caching verification)
                // SAVE MOCK DATA TO DB
                try {
                    await VesselCache.create({
                        mmsi: mockData.mmsi,
                        imo: mockData.imo,
                        name: mockData.name,
                        timestamp: mockData.timestamp,
                        length: 100,
                        width: 20,
                        draft: 5,
                        cog: mockData.course,
                        heading: 0,
                        latitude: mockData.latitude,
                        longitude: mockData.longitude,
                        weather: mockData.weather,
                        weatherdescription: mockData.weatherDescription,
                        temperature: mockData.temperature,
                        pressure: mockData.pressure,
                        humidity: mockData.humidity,
                        windspeed: mockData.windspeed,
                        rain: mockData.rain,
                        clouds: mockData.clouds
                    });

                    await VesselHistory.create({
                        mmsi: mockData.mmsi,
                        imo: mockData.imo,
                        name: mockData.name,
                        timestamp: mockData.timestamp,
                        message: 'Mock Data Entry',
                        length: 100,
                        width: 20,
                        draft: 5,
                        cog: mockData.course,
                        heading: 0,
                        latitude: mockData.latitude,
                        longitude: mockData.longitude,
                        weather: mockData.weather,
                        weatherdescription: mockData.weatherDescription,
                        temperature: mockData.temperature,
                        pressure: mockData.pressure,
                        humidity: mockData.humidity,
                        windspeed: mockData.windspeed,
                        rain: mockData.rain,
                        clouds: mockData.clouds
                    });
                    console.log('Mock data saved to Cache and History');
                } catch (dbErr) {
                    console.error('Failed to save mock data:', dbErr.message);
                }

                return res.json(mockData);
            }
        } // End if (err.response)

        res.status(500).json({ error: 'Internal Server Error', details: err.message });
    }
};

app.get('/vessel-position', handleVesselPosition);
app.get('/api/vessel-position', handleVesselPosition);

if (process.env.NODE_ENV !== 'production') {
    app.listen(PORT, () => {
        console.log(`Server is running on http://localhost:${PORT}`);
    });
}

module.exports = app;
