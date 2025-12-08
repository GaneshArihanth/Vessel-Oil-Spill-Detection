import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import { Boxes } from './components/ui/background-boxes';
import { GlowingEffect } from './components/ui/glowing-effect';
import { cn } from './lib/utils';

function App() {
  const [query, setQuery] = useState('');
  const [vesselData, setVesselData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const searchVessel = async (e) => {
    e.preventDefault();
    if (!query) return;

    setLoading(true);
    setError(null);
    setVesselData(null);

    try {
      // Call the backend API
      const response = await axios.get(`/api/vessel-position?name=${encodeURIComponent(query)}`, {
        headers: {
          'Accept': 'application/json' // Request JSON if backend supports it
        }
      });

      // Backend currently returns HTML, we might need to parse it or update backend to return JSON.
      // For now, let's assume we updated the backend to return JSON.
      // If backend returns HTML, this will fail or need parsing.
      // Let's proceed assuming we will fix the backend next.
      setVesselData(response.data);
    } catch (err) {
      console.error("Error fetching vessel data:", err);
      setError('Failed to fetch vessel data. Please check the MMSI/Name and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative w-full overflow-hidden bg-slate-900 flex flex-col items-center justify-center min-h-screen">
      <div className="absolute inset-0 w-full h-full bg-slate-900 z-20 [mask-image:radial-gradient(transparent,white)] pointer-events-none" />
      <Boxes />
      <div className={cn("relative z-20 w-full pointer-events-none")}>
        <div className="app-container">
          <h1>Vessel Tracker</h1>

          <div className="search-container">
            <input
              type="text"
              className="search-input"
              placeholder="Enter MMSI (e.g., 244110352)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchVessel(e)}
            />
            <button className="search-button" onClick={searchVessel} disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {error && <div className="error">{error}</div>}

          {vesselData && (
            <div className="dashboard-grid">
              {/* Vessel Details Card */}
              <div className="card relative">
                <GlowingEffect
                  spread={40}
                  glow={true}
                  disabled={false}
                  proximity={64}
                  inactiveZone={0.01}
                  borderWidth={3}
                />
                <div className="relative z-10">
                  <h2>🚢 Vessel Details</h2>
                  <div className="info-row">
                    <span>Name</span>
                    <span className="info-value">{vesselData.name}</span>
                  </div>
                  <div className="info-row">
                    <span>MMSI</span>
                    <span className="info-value">{vesselData.mmsi}</span>
                  </div>
                  <div className="info-row">
                    <span>IMO</span>
                    <span className="info-value">{vesselData.imo}</span>
                  </div>
                </div>
              </div>

              {/* Live Position Card */}
              <div className="card relative">
                <GlowingEffect
                  spread={40}
                  glow={true}
                  disabled={false}
                  proximity={64}
                  inactiveZone={0.01}
                />
                <div className="relative z-10">
                  <h2>📍 Live Position</h2>
                  <div className="info-row">
                    <span>Latitude</span>
                    <span className="info-value">{vesselData.latitude}</span>
                  </div>
                  <div className="info-row">
                    <span>Longitude</span>
                    <span className="info-value">{vesselData.longitude}</span>
                  </div>
                  <div className="info-row">
                    <span>Speed</span>
                    <span className="info-value">{vesselData.speed} knots</span>
                  </div>
                  <div className="info-row">
                    <span>Course</span>
                    <span className="info-value">{vesselData.course}°</span>
                  </div>
                </div>
              </div>

              {/* Weather Card */}
              <div className="card relative">
                <GlowingEffect
                  spread={40}
                  glow={true}
                  disabled={false}
                  proximity={64}
                  inactiveZone={0.01}
                />
                <div className="relative z-10">
                  <h2>🌤️ Weather Conditions</h2>
                  <div className="info-row">
                    <span>Condition</span>
                    <span className="info-value">{vesselData.weather}</span>
                  </div>
                  <div className="info-row">
                    <span>Temperature</span>
                    <span className="info-value">{vesselData.temperature}°C</span>
                  </div>
                  <div className="info-row">
                    <span>Wind</span>
                    <span className="info-value">{vesselData.windspeed} m/s</span>
                  </div>
                  <div className="info-row">
                    <span>Humidity</span>
                    <span className="info-value">{vesselData.humidity}%</span>
                  </div>
                </div>
              </div>

              {/* Satellite Image Card */}
              {vesselData.satelliteImage && (
                <div className="card satellite-card relative">
                  <GlowingEffect
                    spread={40}
                    glow={true}
                    disabled={false}
                    proximity={64}
                    inactiveZone={0.01}
                  />
                  <div className="relative z-10">
                    <h2>🛰️ Satellite View</h2>
                    <img
                      src={`data:image/png;base64,${vesselData.satelliteImage}`}
                      alt="Satellite View"
                      className="satellite-img"
                    />
                  </div>
                </div>
              )}

              {/* Oil Spill Analysis Card */}
              {vesselData.oilSpillData && !vesselData.oilSpillData.error && (
                <div className="card oil-spill-card relative">
                  <GlowingEffect
                    spread={40}
                    glow={true}
                    disabled={false}
                    proximity={64}
                    inactiveZone={0.01}
                  />
                  <div className="relative z-10">
                    <h2>🛢️ Oil Spill Analysis</h2>

                    <div className={cn("status-badge", vesselData.oilSpillData.is_spill ? "status-danger" : "status-safe")}>
                      {vesselData.oilSpillData.is_spill ? "⚠️ OIL SPILL DETECTED" : "✅ No Spill Detected"}
                    </div>

                    <div className="info-row">
                      <span>Confidence</span>
                      <span className="info-value">{(vesselData.oilSpillData.confidence * 100).toFixed(1)}%</span>
                    </div>

                    <div className="info-row">
                      <span>Oil Coverage</span>
                      <span className="info-value">{vesselData.oilSpillData.oil_percentage.toFixed(2)}%</span>
                    </div>

                    <div className="info-row">
                      <span>Risk Level</span>
                      <span className={cn("info-value", vesselData.oilSpillData.is_spill ? "text-red-400" : "text-green-400")}>
                        {vesselData.oilSpillData.is_spill ? "HIGH RISK" : "Low Risk"}
                      </span>
                    </div>

                    <div className="info-row">
                      <span>Analysis Location</span>
                      <span className="info-value">{vesselData.latitude.toFixed(4)}, {vesselData.longitude.toFixed(4)}</span>
                    </div>

                    <div className="info-row">
                      <span>Action Required</span>
                      <span className="info-value">
                        {vesselData.oilSpillData.is_spill ? "⚠️ Monitor & Report" : "None"}
                      </span>
                    </div>

                    {vesselData.oilSpillData.analysisImage && (
                      <div className="analysis-image-container mt-4">
                        <p className="text-sm text-slate-400 mb-2">Analysis Overlay:</p>
                        <img
                          src={`data:image/png;base64,${vesselData.oilSpillData.analysisImage}`}
                          alt="Oil Spill Analysis"
                          className="satellite-img border border-slate-700 rounded-md"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {loading && (
            <div className="loading">
              Fetching real-time data...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
