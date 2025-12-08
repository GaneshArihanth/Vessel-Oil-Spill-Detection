const mongoose = require('mongoose');

// Connect to MongoDB
// Connect to MongoDB with retry logic
const connectDB = async () => {
    try {
        const uri = process.env.MONGO_URI;
        if (!uri) {
            console.error('❌ MONGO_URI is missing in environment variables.');
            return;
        }

        await mongoose.connect(uri);
        console.log('✅ Connected to MongoDB');
    } catch (err) {
        console.error('❌ MongoDB connection error:', err.message);
        console.log('🔄 Retrying in 5 seconds...');
        setTimeout(connectDB, 5000);
    }
};

connectDB();

const db = mongoose.connection;
db.on('error', (err) => {
    console.error('❌ MongoDB runtime error:', err.message);
});

// Define the Vessel schema
// Create the VesselCache model for 24-hour caching
const vesselCacheSchema = new mongoose.Schema({
    mmsi: String,
    imo: Number,
    name: String,
    timestamp: Date, // Vessel's actual timestamp
    cachedAt: { type: Date, default: Date.now }, // When we fetched/cached this record
    length: Number,
    width: Number,
    draft: Number,
    cog: Number,
    heading: Number,
    latitude: Number,
    longitude: Number,
    weather: String,
    weatherdescription: String,
    temperature: Number,
    pressure: Number,
    humidity: Number,
    windspeed: Number,
    rain: String,
    clouds: Number
});

// Create a TTL index on the 'cachedAt' field to expire documents after 24 hours (86400 seconds)
vesselCacheSchema.index({ cachedAt: 1 }, { expireAfterSeconds: 86400 });

const VesselCache = mongoose.model('VesselCache', vesselCacheSchema);

// Create the VesselHistory model for permanent storage (same schema, no TTL)
const vesselHistorySchema = new mongoose.Schema({
    mmsi: String,
    imo: Number,
    name: String,
    timestamp: Date, // Vessel's actual timestamp
    message: String, // Context message (e.g., 'API Fetch', 'User Query')
    createdAt: { type: Date, default: Date.now }, // When this history record was created
    length: Number,
    width: Number,
    draft: Number,
    cog: Number,
    heading: Number,
    latitude: Number,
    longitude: Number,
    weather: String,
    weatherdescription: String,
    temperature: Number,
    pressure: Number,
    humidity: Number,
    windspeed: Number,
    rain: String,
    clouds: Number
});

// No TTL index for history
const VesselHistory = mongoose.model('VesselHistory', vesselHistorySchema);

module.exports = { VesselCache, VesselHistory };
