import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface ReentryMapProps {
  geojsonCorridor: any;
  satelliteName: string;
}

export const ReentryMap: React.FC<ReentryMapProps> = ({ 
  geojsonCorridor,
  satelliteName
}) => {
  const [mapCenter, setMapCenter] = useState<[number, number]>([0, 0]);
  const [mapKey, setMapKey] = useState<number>(0);

  // 1. Calculate map center dynamically from GeoJSON coordinates
  useEffect(() => {
    if (!geojsonCorridor || !geojsonCorridor.features || geojsonCorridor.features.length === 0) return;
    
    try {
      const feature = geojsonCorridor.features[0];
      const geom = feature.geometry;
      let centerCoords: [number, number] = [0, 0];
      
      if (geom.type === 'Polygon') {
        const polyCoords = geom.coordinates[0];
        // Calculate average coordinate
        let latSum = 0;
        let lonSum = 0;
        polyCoords.forEach((coord: number[]) => {
          lonSum += coord[0];
          latSum += coord[1];
        });
        centerCoords = [latSum / polyCoords.length, lonSum / polyCoords.length];
      } else if (geom.type === 'MultiPolygon') {
        const polyCoords = geom.coordinates[0][0];
        let latSum = 0;
        let lonSum = 0;
        polyCoords.forEach((coord: number[]) => {
          lonSum += coord[0];
          latSum += coord[1];
        });
        centerCoords = [latSum / polyCoords.length, lonSum / polyCoords.length];
      }
      
      if (centerCoords[0] !== 0 || centerCoords[1] !== 0) {
        setMapCenter(centerCoords);
        // Force Leaflet map rerender with new center key
        setMapKey(prev => prev + 1);
      }
    } catch (e) {
      console.error("Error calculating dynamic map center:", e);
    }
  }, [geojsonCorridor]);

  // Uncertainty corridor polygon styling
  const corridorStyle = {
    color: '#ef4444', // glowing red
    weight: 2,
    opacity: 0.7,
    fillColor: '#ef4444',
    fillOpacity: 0.25,
  };

  // Bind mouseover events to display details
  const onEachFeature = (feature: any, layer: any) => {
    layer.on({
      mouseover: (e: any) => {
        const target = e.target;
        target.setStyle({
          fillOpacity: 0.45,
          weight: 3.5,
          color: '#f87171' // lighter red
        });
      },
      mouseout: (e: any) => {
        const target = e.target;
        target.setStyle(corridorStyle);
      }
    });

    // Bind clean popup showing casualty risk metadata
    const props = feature.properties || {};
    layer.bindPopup(`
      <div style="font-family: monospace; font-size: 11px; color: #1e293b;">
        <h4 style="margin: 0 0 5px 0; color: #ef4444; font-weight: bold;">PROBABILISTIC REENTRY ZONE</h4>
        <b>Object:</b> ${satelliteName}<br/>
        <b>Uncertainty Window:</b> ±${props.uncertainty_hours || 'N/A'} hrs<br/>
        <b>Survival Rate:</b> ${props.survival_pct || 'N/A'}%<br/>
        <b>Casualty Risk (Ec):</b> ${props.casualty_probability || 'N/A'}
      </div>
    `);
  };

  return (
    <div className="w-full h-full min-h-[350px] relative rounded-xl overflow-hidden border border-slate-800">
      <MapContainer
        key={mapKey}
        center={mapCenter}
        zoom={2}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        {geojsonCorridor && (
          <GeoJSON
            data={geojsonCorridor}
            style={corridorStyle}
            onEachFeature={onEachFeature}
          />
        )}

        {/* Center Satellite dot representing current projected coordinates */}
        {mapCenter[0] !== 0 && mapCenter[1] !== 0 && (
          <CircleMarker
            center={mapCenter}
            radius={6}
            pathOptions={{
              fillColor: '#3b82f6',
              fillOpacity: 0.9,
              color: '#ffffff',
              weight: 1.5
            }}
          >
            <Popup>
              <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#1e293b' }}>
                <b>Projected Breakup Center</b><br/>
                Lat: {mapCenter[0].toFixed(4)}<br/>
                Lon: {mapCenter[1].toFixed(4)}
              </div>
            </Popup>
          </CircleMarker>
        )}
      </MapContainer>
      
      {/* Map watermark / info label overlay */}
      <div className="absolute top-3 left-12 z-[1000] bg-slate-950/80 border border-slate-800 rounded-lg py-1 px-3 font-mono text-[9px] text-slate-400">
        WATERMASK GRID: WGS-84 DEBRIS CORRIDOR
      </div>
    </div>
  );
};
