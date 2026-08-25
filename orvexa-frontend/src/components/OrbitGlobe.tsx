import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Viewer, CzmlDataSource, Entity, PolylineGraphics } from 'resium';
import * as Cesium from 'cesium';
import axios from 'axios';
import {
  Crosshair,
  Shield,
  X,
  EyeOff,
  AlertTriangle,
  Search,
  Minimize2,
  Download,
  Settings,
  Eye,
  Sliders,
  MapPin,
  Gauge,
  Box,
  Globe,
  Upload,
  Zap,
  CheckCircle,
  RefreshCw,
  ShieldCheck
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import { LeverSwitch } from '@/components/ui/lever-switch';
import { MatrixNumber } from './ui/matrix';
import { CollisionSimulationPanel } from './CollisionSimulationPanel';
import type { CollisionSimulationConfig } from '../types';

interface OrbitGlobeProps {
  limit?: number;
  setLimit?: (l: number) => void;
  showDebris: boolean;
  setShowDebris?: (b: boolean) => void;
  showPayloads: boolean;
  setShowPayloads?: (b: boolean) => void;
  showSensors: boolean;
  setShowSensors?: (b: boolean) => void;
  showHeatmap: boolean;
  setShowHeatmap?: (b: boolean) => void;
  isSimActive?: boolean;
  multiplier: number;
  setMultiplier?: (m: number) => void;
  /** Collision simulation config — pass null/undefined to stop the simulation */
  simulationConfig?: CollisionSimulationConfig | null;
  onUpdateSimConfig?: (cfg: CollisionSimulationConfig) => void;
  onLaunchSim?: () => void;
  onStopSim?: () => void;
  /** Increment this to force-reset the camera to the default orbital view */
  resetCameraTrigger?: number;
  // TLE self-serve props
  isTleOpen?: boolean;
  setIsTleOpen?: (open: boolean) => void;
  tleInput?: string;
  setTleInput?: (val: string) => void;
  isImporting?: boolean;
  importResult?: { success: boolean; message: string } | null;
  onImportTle?: () => void;
}

const CESIUM_CONTEXT_OPTIONS = { webgl: { alpha: false } };
const CESIUM_STYLE = { width: '100%', height: '100%', background: '#000000' };

export const OrbitGlobe: React.FC<OrbitGlobeProps> = ({
  limit = 40,
  setLimit,
  showDebris,
  setShowDebris,
  showPayloads,
  setShowPayloads,
  showSensors,
  setShowSensors,
  showHeatmap,
  setShowHeatmap,
  isSimActive = false,
  multiplier,
  setMultiplier,
  simulationConfig,
  onUpdateSimConfig,
  onLaunchSim,
  onStopSim,
  resetCameraTrigger,
  isTleOpen = false,
  setIsTleOpen,
  tleInput = '',
  setTleInput,
  isImporting = false,
  importResult = null,
  onImportTle,
}) => {
  const viewerRef = useRef<any>(null);
  const [viewerReady, setViewerReady] = useState(false);
  const [czmlData, setCzmlData] = useState<any[]>([]);
  const [selectedSat, setSelectedSat] = useState<any>(null);
  const [selectedSatIds, setSelectedSatIds] = useState<Set<string>>(new Set());

  // ── Collision Simulation refs (ported from YUG Globe.tsx) ──────────────────
  const simEntitiesRef = useRef<any[]>([]);
  const simPointCollectionRef = useRef<any>(null);
  const phase1EntitiesRef = useRef<any>(null);
  const phase2EntitiesRef = useRef<any>(null);
  const phase3EntitiesRef = useRef<any>(null);
  const lastPhaseKeyRef = useRef<string | null>(null);
  const activeSimScenarioRef = useRef<number | null>(null);
  const appliedCameraModeRef = useRef<string | null>(null);
  const ambientDimStateRef = useRef<'dimmed' | 'restored' | null>(null);
  const cinematicTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const debrisFragmentsRef = useRef<{ scenarioId: number; list: any[] }>({ scenarioId: -1, list: [] });
  // ─────────────────────────────────────────────────────────────────────────

  const [telemetry, setTelemetry] = useState<{
    name: string;
    noradId: string;
    altitude: number; // km
    velocity: number; // km/s
    type: string;
    operator: string;
    latitude: number;
    longitude: number;
    dragStatus?: string;
    decayRate?: number;
    dragScale?: number;
  } | null>(null);
  const [isTracking, setIsTracking] = useState<boolean>(false);
  const [solarWeather, setSolarWeather] = useState<{ f10_7: number; ap: number } | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [operatorFilter, setOperatorFilter] = useState<string>("ALL");
  const [maneuverDeltaV, setManeuverDeltaV] = useState<number>(0);
  const [satDetails, setSatDetails] = useState<any | null>(null);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);

  // Unified Deck Controls
  const [satInspectorTab, setSatInspectorTab] = useState<'telemetry' | 'specs' | 'risks'>('telemetry');
  const [isInspectorMinimized, setIsInspectorMinimized] = useState<boolean>(false);
  const [activeRightDeck, setActiveRightDeck] = useState<'none' | 'search' | 'controls'>('none');
  const [isTrajectoriesOpen, setIsTrajectoriesOpen] = useState<boolean>(false);

  const [earthStyle, setEarthStyle] = useState<'satellite' | 'dark' | 'natural'>('satellite');
  const [show3DModels, setShow3DModels] = useState<boolean>(true);
  const [trackCamMode, setTrackCamMode] = useState<'chase' | 'close' | 'sector'>('chase');

  const hoveredSatIdRef = useRef<string | null>(null);
  const selectedSatRef = useRef<any>(null);
  const selectedSatIdsRef = useRef<Set<string>>(new Set());
  const show3DModelsRef = useRef<boolean>(true);
  const isTrackingRef = useRef<boolean>(false);
  const trackCamModeRef = useRef<'chase' | 'close' | 'sector'>('chase');

  // Resium no longer exposes an onReady prop. A callback ref lets the scene
  // configuration run exactly once after the underlying Cesium Viewer exists.
  const setViewerRef = useCallback((instance: any | null) => {
    viewerRef.current = instance;
    setViewerReady(Boolean(instance?.cesiumElement));
  }, []);

  // Sync refs with React state to support non-closure access inside Cesium CallbackProperty instances
  useEffect(() => { selectedSatRef.current = selectedSat; }, [selectedSat]);
  useEffect(() => { selectedSatIdsRef.current = selectedSatIds; }, [selectedSatIds]);
  useEffect(() => { show3DModelsRef.current = show3DModels; }, [show3DModels]);
  useEffect(() => { isTrackingRef.current = isTracking; }, [isTracking]);
  useEffect(() => { trackCamModeRef.current = trackCamMode; }, [trackCamMode]);

  // Fetch detailed satellite info when selectedSat changes
  useEffect(() => {
    if (!selectedSat) {
      setSatDetails(null);
      return;
    }
    const fetchDetails = async () => {
      setLoadingDetails(true);
      try {
        const noradId = selectedSat.id.replace("sat_", "");
        const response = await axios.get(`${API_BASE_URL}/api/satellites/${noradId}/details`);
        setSatDetails(response.data);
      } catch (err) {
        console.error("Error fetching satellite details:", err);
        setSatDetails(null);
      } finally {
        setLoadingDetails(false);
      }
    };
    fetchDetails();
  }, [selectedSat]);

  // Fetch live NOAA solar weather indices for orbit decay calculations
  useEffect(() => {
    const fetchWeather = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/solar`);
        const data = response.data;
        // Support both nested current schema and flat schema
        const f10_7 = data.f10_7 || data.current?.f10_7 || 135.0;
        const ap = data.ap || data.current?.ap || 12.0;
        setSolarWeather({ f10_7, ap });
      } catch (e) {
        console.error("Error fetching solar weather in globe:", e);
        setSolarWeather({ f10_7: 135.0, ap: 12.0 });
      }
    };
    fetchWeather();
  }, []);

  // 1. Fetch CZML trajectories from FastAPI backend — refreshes every 5 minutes for live positions
  const [lastCzmlUpdate, setLastCzmlUpdate] = React.useState<Date | null>(null);
  const [czmlRefreshing, setCzmlRefreshing] = React.useState(false);

  useEffect(() => {
    const fetchCzml = async () => {
      setCzmlRefreshing(true);
      try {
        const url = `${API_BASE_URL}/api/satellites/czml?limit=${limit}`;
        const response = await axios.get(url);
        setCzmlData(response.data);
        setLastCzmlUpdate(new Date());
      } catch (e) {
        console.error("Failed to load CZML", e);
      } finally {
        setCzmlRefreshing(false);
      }
    };
    fetchCzml();
    // Refresh every 5 minutes — satellites move ~2,120 km in that time (LEO)
    const interval = setInterval(fetchCzml, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [limit]);

  // Camera reset trigger
  useEffect(() => {
    if (resetCameraTrigger && viewerRef.current?.cesiumElement) {
      const viewer = viewerRef.current.cesiumElement;
      if (!viewer.isDestroyed?.()) {
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(0, 20, 25000000),
          duration: 1.5,
        });
      }
    }
  }, [resetCameraTrigger]);

  // Earth globe setup — real NASA day + night imagery with physical daylight effect
  useEffect(() => {
    if (!viewerRef.current || !viewerRef.current.cesiumElement) return;
    const viewer = viewerRef.current.cesiumElement;
    if (viewer.isDestroyed?.() || !viewer.scene || viewer.scene.isDestroyed?.() || !viewer.imageryLayers) return;
    const scene = viewer.scene;
    const globe = scene.globe;
    const layers = viewer.imageryLayers;

    layers.removeAll();

    // ── 1. BASE DAY IMAGERY ───────────────────────────────────────
    let provider: any;
    if (earthStyle === 'satellite') {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        maximumLevel: 19,
        credit: 'Esri World Imagery'
      });
    } else if (earthStyle === 'dark') {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_Black_Marble/default/2021-01-01/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg',
        maximumLevel: 8,
        credit: 'NASA VIIRS Black Marble'
      });
    } else {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        maximumLevel: 19
      });
    }
    const dayLayer = layers.addImageryProvider(provider);
    (dayLayer as any).dayAlpha = 1.0;
    (dayLayer as any).nightAlpha = 0.0;

    // ── 2. NIGHT LIGHTS SECOND LAYER (Ion Asset 3812 / NASA Black Marble) ──
    const loadNightLightsLayer = async () => {
      try {
        let nightProvider: any;
        try {
          if ((Cesium as any).IonImageryProvider?.fromAssetId) {
            nightProvider = await (Cesium as any).IonImageryProvider.fromAssetId(3812);
          } else {
            throw new Error("IonImageryProvider not available");
          }
        } catch {
          // Fallback to NASA VIIRS Black Marble if Ion token is not configured
          nightProvider = new Cesium.UrlTemplateImageryProvider({
            url: 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_Black_Marble/default/2021-01-01/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg',
            maximumLevel: 8,
            credit: 'NASA VIIRS Black Marble'
          });
        }

        if (viewer.isDestroyed?.() || !viewer.imageryLayers) return;
        const nightLayer = layers.addImageryProvider(nightProvider);
        
        // High-Luminance Night City Lights & Lamps Enhancement
        (nightLayer as any).dayAlpha = 0.0;
        (nightLayer as any).nightAlpha = 1.0;
        (nightLayer as any).brightness = 3.5; // High-intensity city glow
        (nightLayer as any).contrast = 1.8;   // High dynamic contrast between oceans and cities
        (nightLayer as any).gamma = 0.65;     // Elevate mid-tone road grids and suburban networks
      } catch (err) {
        console.warn("Could not attach night lights layer:", err);
      }
    };
    loadNightLightsLayer();

    // ── HIGH-PERFORMANCE FLUID 60FPS RENDERING ──────────────────
    viewer.useBrowserRecommendedResolution = true;
    viewer.resolutionScale = 1.0;

    // ── RENDERING CLARITY & REALISTIC SUN/ATMOSPHERE LIGHTING ────
    if (scene.postProcessStages?.fxaa) scene.postProcessStages.fxaa.enabled = false;
    globe.maximumScreenSpaceError = 2.0;
    globe.tileCacheSize = 100;

    // Master switches for dynamic solar terminator & atmosphere
    globe.enableLighting = true;
    globe.dynamicAtmosphereLighting = true;
    globe.dynamicAtmosphereLightingFromSun = true;
    (globe as any).atmosphereLightIntensity = 6.0;
    globe.showGroundAtmosphere = true;
    (globe as any).lightingFadeInDistance = 20000000.0;
    (globe as any).lightingFadeOutDistance = 10000000.0;
    (globe as any).nightColor = new Cesium.Color(0.01, 0.01, 0.02, 1.0);

    if (scene.skyAtmosphere) {
      scene.skyAtmosphere.show = true;
      scene.skyAtmosphere.brightnessShift = 0.0;
      scene.skyAtmosphere.saturationShift = 0.0;
    }

    // ── 3D CELESTIAL SKYBOX & ASTRONOMICAL ENVIRONMENT ───────────
    if (scene.skyBox) scene.skyBox.show = true;
    if (scene.sun) scene.sun.show = true;
    if (scene.moon) scene.moon.show = true;
    if (scene.shadowMap) scene.shadowMap.enabled = false;

    scene.highDynamicRange = false;
    scene.backgroundColor = Cesium.Color.BLACK;
    globe.baseColor = Cesium.Color.BLACK;

    // Suppress Cesium ion token / credit banner container
    if (viewer.bottomContainer) {
      viewer.bottomContainer.style.display = 'none';
    }
    if (viewer.creditDisplay && viewer.creditDisplay.container) {
      viewer.creditDisplay.container.style.display = 'none';
    }

    viewer.clock.currentTime = Cesium.JulianDate.now();
    viewer.clock.shouldAnimate = true;

    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(0.0, 20.0, 20000000.0),
      duration: 1.5
    });
  }, [earthStyle, viewerReady]);

  // 1. Throttled mouse move handler for hover state logic (eliminates GPU framebuffer read stalls)
  useEffect(() => {
    if (!viewerRef.current || !viewerRef.current.cesiumElement) return;
    const viewer = viewerRef.current.cesiumElement;
    if (viewer.isDestroyed?.() || !viewer.scene || !viewer.scene.canvas) return;

    let handler: Cesium.ScreenSpaceEventHandler | null = null;
    let lastPickTime = 0;

    try {
      handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
      handler.setInputAction((movement: any) => {
        const now = performance.now();
        if (now - lastPickTime < 60) return; // Throttle to ~16Hz
        lastPickTime = now;

        try {
          if (viewer.isDestroyed?.() || !viewer.scene) return;
          const pickedObject = viewer.scene.pick(movement.endPosition);
          if (
            Cesium.defined(pickedObject) &&
            pickedObject.id &&
            pickedObject.id instanceof Cesium.Entity &&
            typeof pickedObject.id.id === 'string' &&
            pickedObject.id.id.startsWith("sat_")
          ) {
            hoveredSatIdRef.current = pickedObject.id.id;
          } else {
            hoveredSatIdRef.current = null;
          }
        } catch {
          hoveredSatIdRef.current = null;
        }
      }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    } catch (err) {
      console.warn("Could not attach ScreenSpaceEventHandler:", err);
    }

    return () => {
      if (handler && !handler.isDestroyed?.()) {
        try {
          handler.destroy();
        } catch {}
      }
    };
  }, [czmlData, viewerReady]);

  // 2. Sync clock multiplier speed with parent controls
  useEffect(() => {
    if (viewerRef.current && viewerRef.current.cesiumElement) {
      const viewer = viewerRef.current.cesiumElement;
      viewer.clock.multiplier = multiplier;
    }
  }, [multiplier]);

  // 3. Render ground tracking sensor stations
  useEffect(() => {
    if (!viewerRef.current || !viewerRef.current.cesiumElement) return;
    const viewer = viewerRef.current.cesiumElement;

    // Clear existing sensor entities
    viewer.entities.values
      .filter((e: any) => e.id && e.id.startsWith("sensor_"))
      .forEach((e: any) => viewer.entities.remove(e));

    if (showSensors) {
      // Ground stations mapping
      const groundStations = [
        { name: "Svalbard Satellite Station (Norway)", lat: 78.2297, lon: 15.4077 },
        { name: "ISRO Telemetry Station (Bengaluru)", lat: 13.0343, lon: 77.5116 },
        { name: "Goldstone Deep Space (California)", lat: 35.4267, lon: -116.8900 },
        { name: "Hartebeesthoek (South Africa)", lat: -25.8872, lon: 27.7078 }
      ];

      groundStations.forEach((station, idx) => {
        viewer.entities.add({
          id: `sensor_${idx}`,
          name: station.name,
          position: Cesium.Cartesian3.fromDegrees(station.lon, station.lat, 0),
          point: {
            pixelSize: 10,
            color: Cesium.Color.fromCssColorString('#3b82f6'), // blue
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
          },
          // Sensor radar cone visualization
          ellipse: {
            semiMinorAxis: 800000.0, // 800 km coverage
            semiMajorAxis: 800000.0,
            material: Cesium.Color.fromCssColorString('#3b82f6').withAlpha(0.12),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString('#3b82f6').withAlpha(0.4),
            height: 0
          }
        });
      });
    }
  }, [showSensors, czmlData]);

  // Render 3D orbital hazard shells / heatmap layer
  useEffect(() => {
    if (!viewerRef.current || !viewerRef.current.cesiumElement) return;
    const viewer = viewerRef.current.cesiumElement;

    // Remove existing hazard entities
    viewer.entities.values
      .filter((e: any) => e.id && e.id.startsWith("hazard_"))
      .forEach((e: any) => viewer.entities.remove(e));

    if (showHeatmap) {
      const earthRadius = 6378137.0;

      // 1. High-Density Polar Debris Shell (Hollow sphere 700km to 900km)
      viewer.entities.add({
        id: "hazard_debris_shell",
        name: "LEO Polar Debris Shell (700-900 km altitude)",
        position: Cesium.Cartesian3.ZERO,
        ellipsoid: {
          radii: new Cesium.Cartesian3(earthRadius + 900000.0, earthRadius + 900000.0, earthRadius + 900000.0),
          innerRadii: new Cesium.Cartesian3(earthRadius + 700000.0, earthRadius + 700000.0, earthRadius + 700000.0),
          material: Cesium.Color.fromCssColorString('#ef4444').withAlpha(0.06),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString('#ef4444').withAlpha(0.2),
          slicePartitions: 24,
          stackPartitions: 24
        }
      });

      // 2. High-Density Mega-Constellation Payload Shell (Hollow sphere 350km to 550km)
      viewer.entities.add({
        id: "hazard_constellation_shell",
        name: "LEO Constellation Payload Shell (350-550 km altitude)",
        position: Cesium.Cartesian3.ZERO,
        ellipsoid: {
          radii: new Cesium.Cartesian3(earthRadius + 550000.0, earthRadius + 550000.0, earthRadius + 550000.0),
          innerRadii: new Cesium.Cartesian3(earthRadius + 350000.0, earthRadius + 350000.0, earthRadius + 350000.0),
          material: Cesium.Color.fromCssColorString('#f59e0b').withAlpha(0.04),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString('#f59e0b').withAlpha(0.15),
          slicePartitions: 24,
          stackPartitions: 24
        }
      });
    }
  }, [showHeatmap, czmlData]);

  // 4. Update real-time physics telemetry and dynamic camera locking for selected satellite
  useEffect(() => {
    if (!selectedSat || !viewerRef.current || !viewerRef.current.cesiumElement) {
      setTelemetry(null);
      return;
    }

    const viewer = viewerRef.current.cesiumElement;

    const updateTelemetry = () => {
      const time = viewer.clock.currentTime;

      // Get position in Cartesian3 meters
      const position = selectedSat.position ? selectedSat.position.getValue(time) : undefined;
      if (!position) return;

      // Distance from Earth center in meters
      const distance = Cesium.Cartesian3.magnitude(position);
      // Average Earth radius = 6378137.0 m
      const altitude = Math.max(0, (distance - 6378137.0) / 1000.0);

      // Convert Cartesian3 to Cartographic (Geodetic) coordinates
      const cartographic = Cesium.Cartographic.fromCartesian(position);
      const latitude = cartographic ? Cesium.Math.toDegrees(cartographic.latitude) : 0;
      const longitude = cartographic ? Cesium.Math.toDegrees(cartographic.longitude) : 0;

      // Velocity calculation via position delta over 0.1 second
      const nextTime = Cesium.JulianDate.addSeconds(time, 0.1, new Cesium.JulianDate());
      const nextPosition = selectedSat.position.getValue(nextTime);

      let velocity = 7.5; // default fallback LEO velocity in km/s
      let vVec = new Cesium.Cartesian3(0.0, 7500.0, 0.0); // default velocity vector
      if (nextPosition) {
        vVec = Cesium.Cartesian3.subtract(nextPosition, position, new Cesium.Cartesian3());
        Cesium.Cartesian3.multiplyByScalar(vVec, 10.0, vVec); // velocity in m/s
        velocity = Cesium.Cartesian3.magnitude(vVec) / 1000.0;
      }

      // Calculate atmospheric drag and orbit decay using exponential scale height and live solar weather indices
      let dragStatus = "Nominal";
      let decayRate = 0.0;
      let dragScale = 1.0;

      if ((solarWeather || isSimActive) && altitude < 1200.0) {
        let baseDensity = 0.0;
        if (altitude < 300) {
          baseDensity = 1.5e-11 * Math.exp(-(altitude - 200) / 40.0);
        } else if (altitude < 500) {
          baseDensity = 1.0e-12 * Math.exp(-(altitude - 300) / 60.0);
        } else if (altitude < 800) {
          baseDensity = 1.0e-14 * Math.exp(-(altitude - 500) / 90.0);
        } else {
          baseDensity = 1.0e-15 * Math.exp(-(altitude - 800) / 120.0);
        }

        // Standard quiet conditions are f10_7 = 70.0, ap = 7.0. Override if presentation storm is simulated.
        const f10 = isSimActive ? 220.0 : (solarWeather?.f10_7 || 135.0);
        const apVal = isSimActive ? 54.2 : (solarWeather?.ap || 12.0);

        dragScale = 1.0 + Math.max(0, (f10 - 70.0) / 80.0) + Math.max(0, (apVal - 7.0) / 15.0);
        decayRate = baseDensity * dragScale * 1.5e14;

        if (decayRate > 40.0) {
          dragStatus = "Critical";
        } else if (decayRate > 10.0) {
          dragStatus = "Elevated";
        } else if (decayRate > 1.0) {
          dragStatus = "Moderate";
        } else if (decayRate > 0.01) {
          dragStatus = "Nominal";
        } else {
          dragStatus = "Negligible";
        }
      } else if (altitude >= 1200.0) {
        dragStatus = "Negligible";
        decayRate = 0.0;
        dragScale = 1.0;
      }

      // DYNAMIC CO-ORBITING CAMERA LOCK:
      // Positions the camera at a cinematic inspection offset in the satellite's local orbital frame (VVLH).
      // This keeps the camera flying in parallel at the exact same speed as the satellite (60fps fluid).
      if (isTracking) {
        // Radial unit vector (Up)
        const rUnit = Cesium.Cartesian3.normalize(position, new Cesium.Cartesian3());
        // Normal unit vector (cross product of position and velocity)
        const h = Cesium.Cartesian3.cross(position, vVec, new Cesium.Cartesian3());
        const hUnit = Cesium.Cartesian3.normalize(h, new Cesium.Cartesian3());
        // In-track unit vector (Velocity direction along orbit)
        const tUnit = Cesium.Cartesian3.cross(hUnit, rUnit, new Cesium.Cartesian3());

        // Camera offsets calibrated for detailed 3D inspection and chase view
        let offsetBehind = -450.0;
        let offsetSide = 180.0;
        let offsetAbove = 90.0;

        const currentMode = trackCamModeRef.current;
        if (currentMode === 'close') {
          offsetBehind = -120.0;
          offsetSide = 45.0;
          offsetAbove = 25.0;
        } else if (currentMode === 'sector') {
          offsetBehind = -12000.0;
          offsetSide = 6000.0;
          offsetAbove = 3000.0;
        }

        const camPos = new Cesium.Cartesian3();
        Cesium.Cartesian3.add(position, Cesium.Cartesian3.multiplyByScalar(tUnit, offsetBehind, new Cesium.Cartesian3()), camPos);
        Cesium.Cartesian3.add(camPos, Cesium.Cartesian3.multiplyByScalar(hUnit, offsetSide, new Cesium.Cartesian3()), camPos);
        Cesium.Cartesian3.add(camPos, Cesium.Cartesian3.multiplyByScalar(rUnit, offsetAbove, new Cesium.Cartesian3()), camPos);

        viewer.camera.setView({
          destination: camPos,
          orientation: {
            direction: Cesium.Cartesian3.normalize(Cesium.Cartesian3.subtract(position, camPos, new Cesium.Cartesian3()), new Cesium.Cartesian3()),
            up: rUnit
          }
        });
      }

      // Throttle React state telemetry updates to 250ms (4Hz) to eliminate React re-render thrashing & lag
      const now = performance.now();
      if (now - lastTelemetryUpdateRef.current < 250) return;
      lastTelemetryUpdateRef.current = now;

      // Parse metadata from description
      const desc = selectedSat.description?.getValue(time) || "";
      const noradMatch = desc.match(/NORAD ID:\s*(\d+)/);
      const typeMatch = desc.match(/Type:\s*([^\s|]+)/);
      const operatorMatch = desc.match(/Operator:\s*([^|]+)/);

      setTelemetry({
        name: selectedSat.name || "Unknown Object",
        noradId: noradMatch ? noradMatch[1] : "N/A",
        altitude: altitude,
        velocity: velocity,
        type: typeMatch ? typeMatch[1] : "Payload",
        operator: operatorMatch ? operatorMatch[1].trim() : "Unknown",
        latitude: latitude,
        longitude: longitude,
        dragStatus: dragStatus,
        decayRate: decayRate,
        dragScale: dragScale
      });
    };

    const lastTelemetryUpdateRef = { current: 0 };
    updateTelemetry();

    // Listen to tick events to calculate metrics and update camera position in real-time
    const removeListener = viewer.clock.onTick.addEventListener(updateTelemetry);
    return () => removeListener();
  }, [selectedSat, isTracking, solarWeather, isSimActive]);


  // 5. Handle selection updates
  const handleSelectedEntityChange = (entity: any) => {
    setManeuverDeltaV(0);
    if (entity && entity.id && entity.id.startsWith("sat_")) {
      setSelectedSat(entity);
      setIsInspectorMinimized(false);
      setIsTleOpen?.(false);
    } else {
      setSelectedSat(null);
      setIsTracking(false);
    }
  };

  // Lock camera target onto clicked satellite
  const handleTrackEntity = () => {
    if (selectedSat) {
      setIsTracking(true);
    }
  };

  // Free camera from tracking selected satellite
  const handleUntrackEntity = () => {
    setIsTracking(false);
    setManeuverDeltaV(0);
    if (viewerRef.current && viewerRef.current.cesiumElement) {
      const viewer = viewerRef.current.cesiumElement;
      // Fly camera back to a nice overview of the Earth
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(0.0, 20.0, 20000000.0), // center latitude/longitude/altitude (20,000 km up)
        duration: 1.5
      });
    }
  };

  // Call backend to generate and export CCSDS OPM text file for simulated burn
  const handleExportOPM = async () => {
    if (!telemetry || maneuverDeltaV === 0) return;
    try {
      const response = await axios.post(`${API_BASE_URL}/api/satellites/${telemetry.noradId}/export-opm`, {
        maneuver_dv: maneuverDeltaV
      }, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CCSDS_OPM_${telemetry.name.replace(/\s+/g, '_')}_${telemetry.noradId}.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export CCSDS OPM:", err);
      alert("Error generating CCSDS OPM file.");
    }
  };

  const handleSelectSearchResult = (satEntityId: string) => {
    if (viewerRef.current && viewerRef.current.cesiumElement) {
      const viewer = viewerRef.current.cesiumElement;

      let entity = null;
      const dsLength = viewer.dataSources.length;
      for (let i = 0; i < dsLength; i++) {
        const ds = viewer.dataSources.get(i);
        const match = ds.entities.values.find((e: any) => e.id === satEntityId);
        if (match) {
          entity = match;
          break;
        }
      }

      if (entity) {
        setSelectedSat(entity);
        setIsInspectorMinimized(false);
        setIsTleOpen?.(false);
        viewer.selectedEntity = entity;

        const time = viewer.clock.currentTime;
        const position = entity.position?.getValue(time);
        if (position) {
          viewer.camera.flyTo({
            destination: Cesium.Cartesian3.add(
              position,
              new Cesium.Cartesian3(600000.0, 600000.0, 400000.0),
              new Cesium.Cartesian3()
            ),
            duration: 1.5
          });
        }
      }
    }
    setSearchQuery("");
  };

  // Keyboard shortcut: Escape key resets view, tracking, and selections
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsTracking(false);
        setManeuverDeltaV(0);
        if (viewerRef.current && viewerRef.current.cesiumElement) {
          const viewer = viewerRef.current.cesiumElement;
          viewer.selectedEntity = undefined;
          viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(0.0, 20.0, 20000000.0),
            duration: 1.5
          });
        }
        setSelectedSat(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const mappedCzml = useMemo(() => {
    return czmlData.filter((packet: any) => {
      if (packet.id === "document") return true;
      const descLower = (packet.description || "").toLowerCase();

      // 1. Layer Visibility Check
      const isDebris = descLower.includes("debris");
      if (isDebris && !showDebris) return false;
      const isRocket = descLower.includes("rocket") || descLower.includes("stage");
      const isPayload = !isDebris && !isRocket;
      if (isPayload && !showPayloads) return false;

      // 2. Search Query Filter (Matches Name or NORAD ID)
      const nameLower = (packet.name || "").toLowerCase();
      const noradId = packet.id.replace("sat_", "");
      if (searchQuery.trim() !== "") {
        const q = searchQuery.toLowerCase().trim();
        const matchesName = nameLower.includes(q);
        const matchesId = noradId.includes(q);
        if (!matchesName && !matchesId) return false;
      }

      // 3. Operator Filter Check
      if (operatorFilter !== "ALL") {
        const opMatch = packet.description?.match(/Operator:\s*([^|]+)/);
        const operator = opMatch ? opMatch[1].trim().toUpperCase() : "";
        const targetOp = operatorFilter.toUpperCase();

        if (targetOp === "SPACEX" && !operator.includes("SPACEX") && !operator.includes("STARLINK")) return false;
        if (targetOp === "ISRO" && !operator.includes("ISRO") && !operator.includes("INDIA")) return false;
        if (targetOp === "NASA" && !operator.includes("NASA") && !operator.includes("USA")) return false;
        if (targetOp === "ESA" && !operator.includes("ESA") && !operator.includes("EUROPE")) return false;
        if (targetOp === "ROSCOSMOS" && !operator.includes("ROSCOSMOS") && !operator.includes("RUSSIA")) return false;
      }

      return true;
    });
  }, [czmlData, showDebris, showPayloads, searchQuery, operatorFilter]);

  // Generate future perturbed trajectory positions for maneuver simulation
  const futurePositions: Cesium.Cartesian3[] = useMemo(() => {
    const positions: Cesium.Cartesian3[] = [];
    if (viewerRef.current && viewerRef.current.cesiumElement && selectedSat && maneuverDeltaV !== 0) {
      const viewer = viewerRef.current.cesiumElement;
      const currentTime = viewer.clock.currentTime;
      for (let i = 0; i <= 30; i++) {
        const offsetSeconds = i * 180;
        const evalTime = Cesium.JulianDate.addSeconds(currentTime, offsetSeconds, new Cesium.JulianDate());
        const pos = selectedSat.position.getValue(evalTime);
        if (pos) {
          const rUnit = Cesium.Cartesian3.normalize(pos, new Cesium.Cartesian3());
          const scale = maneuverDeltaV * (offsetSeconds / 10.0);
          const shiftVec = Cesium.Cartesian3.multiplyByScalar(rUnit, scale, new Cesium.Cartesian3());
          const perturbedPos = Cesium.Cartesian3.add(pos, shiftVec, new Cesium.Cartesian3());
          positions.push(perturbedPos);
        }
      }
    }
    return positions;
  }, [selectedSat, maneuverDeltaV]);


  // Callback handler to inject dynamic hover & selection properties on entity load
  const handleCzmlLoad = (dataSource: any) => {
    dataSource.entities.values.forEach((entity: any) => {
      if (!entity.id || !entity.id.startsWith("sat_")) return;
      const entityId = entity.id;
      const noradId = entityId.replace("sat_", "");

      // Retrieve type value from custom properties dictionary
      const properties = entity.properties;
      const typeValue = properties && properties.type ? properties.type.getValue(Cesium.JulianDate.now()) : "";
      const isDebris = typeValue === "DEBRIS" || (entity.name && (entity.name.toLowerCase().includes("deb") || entity.name.toLowerCase().includes("debris")));
      const isRocket = typeValue === "ROCKET BODY" || (entity.name && (entity.name.toLowerCase().includes("r/b") || entity.name.toLowerCase().includes("rocket")));
      
      const checkSelected = () => {
        return !!(selectedSatIdsRef.current.has(noradId) ||
          (selectedSatRef.current && selectedSatRef.current.id === entityId));
      };

      const checkHovered = () => {
        return hoveredSatIdRef.current === entityId;
      };

      // 1. Label show Callback (shows if hovered or selected, hides during tracking to avoid blocking 3D model)
      if (entity.label) {
        entity.label.show = new Cesium.CallbackProperty(() => {
          if (isTrackingRef.current && checkSelected()) return false;
          return !!(checkHovered() || checkSelected());
        }, false);
        entity.label.pixelOffset = new Cesium.ConstantProperty(new Cesium.Cartesian2(0, -32));
      }

      // 2. Point show Callback:
      // Hide 2D dot for the currently selected/tracked satellite so the 3D model is pristine and never mixed with dots
      // All other satellites keep their 2D dots visible for easy navigation across the globe
      if (entity.point) {
        entity.point.show = new Cesium.CallbackProperty(() => {
          if (checkSelected()) return false;
          return true;
        }, false);
        entity.point.pixelSize = new Cesium.CallbackProperty(() => {
          if (checkHovered()) return 10;
          return 7;
        }, false);
      }

      // 3. Billboard show Callback
      if (entity.billboard) {
        entity.billboard.show = new Cesium.ConstantProperty(false);
      }

      // 4. Model show & properties Callback (Renders 3D GLB model when satellite is selected/tracked or global 3D is on)
      if (entity.model) {
        entity.model.show = new Cesium.CallbackProperty(() => {
          return checkSelected() || show3DModelsRef.current;
        }, false);

        // Color tinting based on object type with MIX mode for realistic GLB textures
        entity.model.color = new Cesium.CallbackProperty(() => {
          if (isDebris) return Cesium.Color.fromCssColorString('#ef4444');
          if (isRocket) return Cesium.Color.fromCssColorString('#f59e0b');
          return Cesium.Color.WHITE;
        }, false);
        entity.model.colorBlendMode = new Cesium.ConstantProperty(Cesium.ColorBlendMode.MIX);
        entity.model.colorBlendAmount = new Cesium.ConstantProperty(0.15);

        // Scaling parameters for crisp 3D inspection and chase camera
        entity.model.minimumPixelSize = new Cesium.ConstantProperty(48);
        entity.model.maximumScale = new Cesium.ConstantProperty(2000);
      }

      // 5. Path show Callback (show orbit path when selected or hovered)
      if (entity.path) {
        entity.path.show = new Cesium.CallbackProperty(() => {
          return !!(checkHovered() || checkSelected() || selectedSatIdsRef.current.has(noradId));
        }, false);
      }
    });

    // ── FIX: After CZML load, snap viewer clock to real wall-clock time ──────
    // The CZML document packet sets clock.currentTime to the trajectory epoch
    // (which may be days in the past). This causes Cesium to calculate the
    // wrong sun position, making India appear in night during the day.
    // We override it here to always reflect actual real-world time.
    if (viewerRef.current?.cesiumElement) {
      const v = viewerRef.current.cesiumElement;
      if (!v.isDestroyed?.()) {
        v.clock.currentTime = Cesium.JulianDate.now();
        v.clock.shouldAnimate = true;
      }
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // GPU-ACCELERATED COLLISION SIMULATION RENDERING (ported from YUG Globe.tsx)
  // ═══════════════════════════════════════════════════════════════════════════
  useEffect(() => {
    if (!viewerRef.current || !viewerRef.current.cesiumElement) return;
    const viewer = viewerRef.current.cesiumElement;

    // Create PointPrimitiveCollection once for debris GPU particles
    if (!simPointCollectionRef.current) {
      simPointCollectionRef.current = viewer.scene.primitives.add(
        new Cesium.PointPrimitiveCollection()
      );
    }

    cinematicTimersRef.current.forEach((t) => clearTimeout(t));
    cinematicTimersRef.current = [];

    if (!simulationConfig || !simulationConfig.active) {
      // Teardown
      simEntitiesRef.current.forEach((e) => viewer.entities.remove(e));
      simEntitiesRef.current = [];
      if (simPointCollectionRef.current) simPointCollectionRef.current.removeAll();
      phase1EntitiesRef.current = null;
      phase2EntitiesRef.current = null;
      phase3EntitiesRef.current = null;
      lastPhaseKeyRef.current = null;
      activeSimScenarioRef.current = null;
      appliedCameraModeRef.current = null;
      ambientDimStateRef.current = null;
      return;
    }

    const SCENE_ANCHORS = {
      1: { lat: 62.0, lon: 97.0, altM: 650_000 },
      2: { lat: 48.0, lon: 105.0, altM: 865_000 },
      3: { lat: 65.0, lon: 18.0, altM: 980_000 },
    } as const;
    const scenarioId = (simulationConfig.scenario_id ?? 1) as 1 | 2 | 3;
    const anchor = SCENE_ANCHORS[scenarioId];
    const centerLat = anchor.lat;
    const centerLon = anchor.lon;
    const altM = anchor.altM;
    const progress = simulationConfig.progress;
    const collisionCenter = Cesium.Cartesian3.fromDegrees(centerLon, centerLat, altM);

    const phase: 'p1' | 'p2' | 'p3' = progress < 0.5 ? 'p1' : progress < 0.58 ? 'p2' : 'p3';
    const phaseKey = `${scenarioId}:${phase}`;
    const isPhaseTransition = lastPhaseKeyRef.current !== phaseKey;
    if (isPhaseTransition) {
      lastPhaseKeyRef.current = phaseKey;
      simEntitiesRef.current.forEach((e) => viewer.entities.remove(e));
      simEntitiesRef.current = [];
      simPointCollectionRef.current.removeAll();
      phase1EntitiesRef.current = null;
      phase2EntitiesRef.current = null;
      phase3EntitiesRef.current = null;
    }

    // Camera framing
    const explicitMode = simulationConfig.camera_mode;
    if (explicitMode) {
      if (appliedCameraModeRef.current !== `${scenarioId}:${explicitMode}`) {
        appliedCameraModeRef.current = `${scenarioId}:${explicitMode}`;
        activeSimScenarioRef.current = scenarioId;
        if (explicitMode === 'orbit') {
          viewer.camera.flyToBoundingSphere(
            new Cesium.BoundingSphere(collisionCenter, 1_000_000),
            { offset: new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-68.0), 10_000_000), duration: 1.5 }
          );
        } else if (explicitMode === 'approach') {
          viewer.camera.flyToBoundingSphere(
            new Cesium.BoundingSphere(collisionCenter, 120_000),
            { offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(45.0), Cesium.Math.toRadians(-25.0), 480_000), duration: 1.5 }
          );
        } else if (explicitMode === 'impact') {
          viewer.camera.flyToBoundingSphere(
            new Cesium.BoundingSphere(collisionCenter, 30_000),
            { offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(45.0), Cesium.Math.toRadians(-18.0), 140_000), duration: 1.2 }
          );
        } else if (explicitMode === 'aftermath') {
          viewer.camera.flyToBoundingSphere(
            new Cesium.BoundingSphere(collisionCenter, 350_000),
            { offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(25.0), Cesium.Math.toRadians(-35.0), 2_600_000), duration: 1.5 }
          );
        }
      }
    } else if (activeSimScenarioRef.current !== scenarioId) {
      activeSimScenarioRef.current = scenarioId;
      appliedCameraModeRef.current = `${scenarioId}:approach`;
      viewer.camera.flyToBoundingSphere(
        new Cesium.BoundingSphere(collisionCenter, 120_000),
        { offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(45.0), Cesium.Math.toRadians(-25.0), 480_000), duration: 1.5 }
      );
    }

    // PHASE 1: ORBITAL CONVERGENCE (progress 0 → 0.5)
    if (phase === 'p1') {
      const normProg = progress / 0.5;
      const separation = Math.pow(1 - normProg, 0.35) * 0.8;

      const pos1 = Cesium.Cartesian3.fromDegrees(
        centerLon - separation * 0.8, centerLat + separation * 0.5, altM + separation * 5000
      );
      const pos2 = Cesium.Cartesian3.fromDegrees(
        centerLon + separation * 0.8, centerLat - separation * 0.5, altM - separation * 5000
      );

      const arc1Pts: any[] = [];
      const arc2Pts: any[] = [];
      for (let i = 0; i <= 15; i++) {
        const frac = i / 15;
        const pastSep = separation + frac * 0.6;
        arc1Pts.push(Cesium.Cartesian3.fromDegrees(centerLon - pastSep * 0.8, centerLat + pastSep * 0.5, altM + pastSep * 5000));
        arc2Pts.push(Cesium.Cartesian3.fromDegrees(centerLon + pastSep * 0.8, centerLat - pastSep * 0.5, altM - pastSep * 5000));
      }

      if (!phase1EntitiesRef.current) {
        const orbit1Trail = viewer.entities.add({
          polyline: { positions: arc1Pts, width: 2.0, material: Cesium.Color.fromCssColorString('#10B981').withAlpha(0.85), arcType: Cesium.ArcType.NONE },
        });
        const orbit2Trail = viewer.entities.add({
          polyline: { positions: arc2Pts, width: 2.0, material: Cesium.Color.fromCssColorString('#E0A93B').withAlpha(0.85), arcType: Cesium.ArcType.NONE },
        });

        const sat1 = viewer.entities.add({
          id: 'sim_sat1',
          position: pos1,
          model: { uri: '/models/satellite.glb', scale: 18000.0, minimumPixelSize: 180, maximumScale: 120000 },
          label: {
            text: simulationConfig.sat1_name,
            font: "bold 11px monospace",
            fillColor: Cesium.Color.fromCssColorString('#E8ECF1'),
            outlineColor: Cesium.Color.BLACK, outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(-40, -32),
            horizontalOrigin: Cesium.HorizontalOrigin.RIGHT,
          },
        });
        const sat2 = viewer.entities.add({
          id: 'sim_sat2',
          position: pos2,
          model: { uri: '/models/satellite.glb', scale: 18000.0, minimumPixelSize: 180, maximumScale: 120000 },
          label: {
            text: simulationConfig.sat2_name,
            font: "bold 11px monospace",
            fillColor: Cesium.Color.fromCssColorString('#E8ECF1'),
            outlineColor: Cesium.Color.BLACK, outlineWidth: 3,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(40, -32),
            horizontalOrigin: Cesium.HorizontalOrigin.LEFT,
          },
        });

        simEntitiesRef.current.push(orbit1Trail, orbit2Trail, sat1, sat2);
        phase1EntitiesRef.current = { sat1, sat2, orbit1Trail, orbit2Trail };
      } else {
        // Update positions every frame
        if (phase1EntitiesRef.current.sat1) phase1EntitiesRef.current.sat1.position = pos1 as any;
        if (phase1EntitiesRef.current.sat2) phase1EntitiesRef.current.sat2.position = pos2 as any;
        if (phase1EntitiesRef.current.orbit1Trail?.polyline) phase1EntitiesRef.current.orbit1Trail.polyline.positions = arc1Pts as any;
        if (phase1EntitiesRef.current.orbit2Trail?.polyline) phase1EntitiesRef.current.orbit2Trail.polyline.positions = arc2Pts as any;
      }
    }

    // PHASE 2: IMPACT FLASH (progress 0.5 → 0.58)
    if (phase === 'p2') {
      const flashIntensity = 1.0 - (progress - 0.5) / 0.08;
      if (!phase2EntitiesRef.current) {
        const flash = viewer.entities.add({
          position: collisionCenter,
          point: {
            pixelSize: 24 + flashIntensity * 30,
            color: Cesium.Color.fromCssColorString('#ffffff').withAlpha(Math.min(1, flashIntensity * 1.2)),
            outlineColor: Cesium.Color.fromCssColorString('#ff6600').withAlpha(flashIntensity * 0.8),
            outlineWidth: 6,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });
        simEntitiesRef.current.push(flash);
        phase2EntitiesRef.current = { flash };
      } else if (phase2EntitiesRef.current.flash?.point) {
        phase2EntitiesRef.current.flash.point.pixelSize = (24 + flashIntensity * 30) as any;
        phase2EntitiesRef.current.flash.point.color = Cesium.Color.fromCssColorString('#ffffff').withAlpha(Math.min(1, flashIntensity * 1.2)) as any;
      }
    }

    // PHASE 3: DEBRIS EXPANSION (progress 0.58 → 1.0)
    if (phase === 'p3') {
      const debrisProg = Math.min(1.0, Math.max(0, (progress - 0.58) / 0.42));
      const FRAGMENT_TOTALS = { 1: 2300, 2: 3500, 3: 240 } as const;
      const totalFragments = FRAGMENT_TOTALS[scenarioId];
      const debrisRadiusKm = debrisProg * 180;

      if (!phase3EntitiesRef.current) {
        const impactMarker = viewer.entities.add({
          position: collisionCenter,
          point: {
            pixelSize: 8,
            color: Cesium.Color.fromCssColorString('#ff4444').withAlpha(0.9),
            outlineColor: Cesium.Color.WHITE, outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });
        const cloudShell = viewer.entities.add({
          position: collisionCenter,
          ellipsoid: {
            radii: new Cesium.CallbackProperty(() => {
              const curProg = Math.min(1.0, Math.max(0, (simulationConfig.progress - 0.58) / 0.42));
              const r = Math.max(5000, curProg * 280_000);
              return new Cesium.Cartesian3(r, r, r);
            }, false),
            material: Cesium.Color.fromCssColorString('#ff3322').withAlpha(0.04),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString('#ff5533').withAlpha(0.2),
            outlineWidth: 1,
          },
        });
        simEntitiesRef.current.push(impactMarker, cloudShell);
        phase3EntitiesRef.current = { impactMarker, cloudShell };
      }

      // Generate Fibonacci sphere debris distribution once per scenario change
      if (debrisFragmentsRef.current.scenarioId !== scenarioId) {
        const sampleSize = Math.min(900, totalFragments);
        debrisFragmentsRef.current = {
          scenarioId,
          list: Array.from({ length: sampleSize }, (_, i) => {
            const theta = i * 2.399963229728653;
            const y = 1 - (i / (sampleSize - 1)) * 2;
            const radiusAtY = Math.sqrt(Math.max(0, 1 - y * y));
            const x = Math.cos(theta) * radiusAtY;
            const z = Math.sin(theta) * radiusAtY;
            const speedMult = 0.5 + Math.random() * 1.5;
            return { vx: x * speedMult, vy: z * speedMult, vz: y * speedMult, size: 2.0 + Math.random() * 3.0, hue: Math.random() };
          }),
        };
      }

      if (simPointCollectionRef.current) {
        simPointCollectionRef.current.removeAll();
        const maxExpansionKm = debrisRadiusKm * 2.8;
        for (const frag of debrisFragmentsRef.current.list) {
          const lonOff = (frag.vx * maxExpansionKm) / (111 * Math.cos((centerLat * Math.PI) / 180));
          const latOff = (frag.vy * maxExpansionKm) / 111;
          const altOff = frag.vz * maxExpansionKm * 1000;
          const fragLon = centerLon + lonOff;
          const fragLat = Math.max(-85, Math.min(85, centerLat + latOff));
          const fragAlt = Math.max(80_000, altM + altOff);
          const hueVal = 0.01 + frag.hue * 0.08;
          simPointCollectionRef.current.add({
            position: Cesium.Cartesian3.fromDegrees(fragLon, fragLat, fragAlt),
            pixelSize: frag.size + debrisProg * 1.2,
            color: Cesium.Color.fromHsl(hueVal, 0.85, 0.55).withAlpha(Math.max(0.4, 0.95 - debrisProg * 0.25)),
            outlineColor: Cesium.Color.fromCssColorString('#ff2200').withAlpha(0.25),
            outlineWidth: 1,
          });
        }
      }
    }
  }, [simulationConfig, viewerReady]);

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden border border-white/[0.05] shadow-2xl bg-black select-none">

      {/* 3D Earth Viewer Canvas */}
      <Viewer
        ref={setViewerRef}
        full
        shouldAnimate={true}
        timeline={false}
        animation={false}
        navigationHelpButton={false}
        geocoder={false}
        homeButton={false}
        sceneModePicker={false}
        baseLayerPicker={false}
        infoBox={false}
        shadows={false}
        selectionIndicator={false}
        contextOptions={CESIUM_CONTEXT_OPTIONS}
        onSelectedEntityChange={handleSelectedEntityChange}
        style={CESIUM_STYLE}
      >
        {viewerReady && mappedCzml.length > 0 && (
          <CzmlDataSource data={mappedCzml} onLoad={handleCzmlLoad} />
        )}
        {maneuverDeltaV !== 0 && futurePositions.length > 0 && (
          <Entity id="maneuver_simulation_path">
            <PolylineGraphics
              positions={futurePositions}
              width={2.5}
              material={new Cesium.PolylineDashMaterialProperty({
                color: Cesium.Color.fromCssColorString('#fbbf24'), // Amber
                dashLength: 12.0
              })}
            />
          </Entity>
        )}
      </Viewer>

      {/* ══════════════════════════════════════════════════════════════════════ */}
      {/* ── UNIFIED LEFT MISSION DECK (top-20 left-6 z-30) ────────────────── */}
      {/* ══════════════════════════════════════════════════════════════════════ */}
      <div className="absolute top-20 left-6 z-30 flex flex-col gap-2.5 max-h-[calc(100vh-170px)] w-80 sm:w-88 select-none pointer-events-none">
        
        {/* Top Action Capsule Toolbar */}
        <div className="flex items-center gap-1.5 p-1 bg-[#0a0a0a]/90 backdrop-blur-xl border border-white/[0.08] rounded-xl shadow-2xl pointer-events-auto shrink-0 font-mono">
          {/* Live Status Badge */}
          <div
            title={lastCzmlUpdate ? `Last updated: ${lastCzmlUpdate.toLocaleTimeString()}` : 'Live SGP4 Ephemeris'}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.03] border border-white/[0.06] text-[10px]"
          >
            {czmlRefreshing ? (
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
            ) : (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
            )}
            <span className="font-bold text-white/80 text-[10px]">
              {czmlRefreshing ? 'SYNC' : 'LIVE'}
            </span>
            <span className="text-white/40 text-[9px] border-l border-white/10 pl-1.5">
              {czmlData.filter((p: any) => p.id !== 'document').length} Sats
            </span>
          </div>

          {/* TLE Import Toggle Button */}
          {setIsTleOpen && (
            <button
              onClick={() => setIsTleOpen(!isTleOpen)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all cursor-pointer border ${
                isTleOpen
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm'
                  : 'bg-transparent text-white/60 hover:text-white hover:bg-white/[0.05] border-transparent'
              }`}
              title="Custom TLE Ingestion"
            >
              <Upload className="h-3 w-3" />
              <span>+ TLE</span>
            </button>
          )}

          {/* Collision Replay Button */}
          {onLaunchSim && !simulationConfig && (
            <button
              onClick={onLaunchSim}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold text-sky-300 hover:bg-sky-950/30 border border-sky-500/30 hover:border-sky-500/50 transition-all cursor-pointer"
              title="Launch Collision Replay"
            >
              <Zap className="h-3 w-3 text-sky-400" />
              <span>Replay</span>
            </button>
          )}

          {/* Pinned Trajectories Chip */}
          {selectedSatIds.size > 0 && (
            <button
              onClick={() => setIsTrajectoriesOpen(!isTrajectoriesOpen)}
              className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold transition-all cursor-pointer border ${
                isTrajectoriesOpen
                  ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                  : 'bg-white/[0.04] text-white/60 hover:text-white border-white/[0.06]'
              }`}
              title="Toggle Pinned Orbits"
            >
              <span>Pinned ({selectedSatIds.size})</span>
            </button>
          )}
        </div>

        {/* Scrollable Body of Left Deck */}
        <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar flex flex-col gap-2.5 pointer-events-auto pr-0.5">
          
          {/* 1. TLE Self-Serve Ingestion Form */}
          {isTleOpen && (
            <div className="bg-[#0a0a0a]/95 border border-white/[0.1] rounded-2xl p-4 flex flex-col gap-3 shadow-2xl backdrop-blur-2xl font-mono text-xs animate-slide-in">
              <div className="flex justify-between items-center pb-2 border-b border-white/[0.06]">
                <span className="text-[10px] font-bold text-white uppercase tracking-widest flex items-center gap-1.5">
                  <Upload className="h-3.5 w-3.5 text-emerald-400" />
                  TLE Ingestion
                </span>
                <button onClick={() => setIsTleOpen?.(false)} className="text-white/40 hover:text-white cursor-pointer p-0.5"><X size={14} /></button>
              </div>
              <p className="text-[10px] text-white/50 leading-relaxed font-sans">Paste a 2 or 3-line TLE to propagate orbit & screen close encounters in real-time.</p>
              <textarea rows={3} value={tleInput || ''} onChange={(e) => setTleInput?.(e.target.value)}
                placeholder={"e.g.\nMY_CUBESAT\n1 99999U ...\n2 99999 ..."}
                className="w-full bg-black/60 border border-white/10 p-2 text-[10px] rounded-lg text-white placeholder-white/30 font-mono resize-none focus:outline-none focus:border-white/30" />
              <button onClick={onImportTle} disabled={isImporting || !tleInput?.trim()}
                className="w-full py-2 bg-white hover:bg-white/90 disabled:bg-white/10 disabled:text-white/30 text-black rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-md">
                {isImporting ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Propagating SGP4...</> : "Deploy & Screen Orbit"}
              </button>
              {importResult && (
                <div className={`p-2.5 rounded-lg border flex gap-2 items-start text-[9px] ${importResult.success ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-300' : 'border-rose-500/30 bg-rose-950/20 text-rose-300'}`}>
                  {importResult.success ? <CheckCircle className="h-3.5 w-3.5 shrink-0 text-emerald-400" /> : <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-rose-400" />}
                  <span className="leading-relaxed font-sans">{importResult.message}</span>
                </div>
              )}
            </div>
          )}

          {/* 2. Pinned Trajectories List */}
          {isTrajectoriesOpen && selectedSatIds.size > 0 && (
            <div className="bg-[#0a0a0a]/95 backdrop-blur-xl rounded-xl p-3.5 border border-white/[0.08] shadow-2xl animate-slide-in flex flex-col gap-2 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
                <span className="text-[10px] font-bold text-white/70 uppercase tracking-wide">
                  Pinned Orbits ({selectedSatIds.size})
                </span>
                <button
                  onClick={() => setSelectedSatIds(new Set())}
                  className="text-[9px] bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.1] text-white/50 hover:text-white px-2 py-0.5 rounded transition-colors cursor-pointer"
                >
                  Clear All
                </button>
              </div>
              <div className="flex flex-col gap-1.5 max-h-32 overflow-y-auto pr-1">
                {Array.from(selectedSatIds).map(id => {
                  const satPacket = czmlData.find(p => p.id === `sat_${id}`);
                  const satName = satPacket ? satPacket.name : `NORAD ${id}`;
                  return (
                    <div key={id} className="flex items-center justify-between bg-white/[0.02] border border-white/[0.04] px-2.5 py-1.5 rounded-lg text-[10px]">
                      <span className="text-white/80 truncate max-w-[170px]">{satName}</span>
                      <button
                        onClick={() => {
                          setSelectedSatIds(prev => {
                            const newSet = new Set(prev);
                            newSet.delete(id);
                            return newSet;
                          });
                        }}
                        className="text-white/40 hover:text-rose-400 font-bold ml-2 cursor-pointer text-sm"
                      >
                        ×
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 3. Unified Satellite Inspector (Tabs: Telemetry, Specs, Risks) */}
          {selectedSat && telemetry && (
            <div className="bg-[#0a0a0a]/95 backdrop-blur-2xl border border-white/[0.1] rounded-2xl shadow-2xl animate-slide-in overflow-hidden font-mono flex flex-col">
              {/* Inspector Header */}
              <div className="p-3.5 pb-2.5 border-b border-white/[0.06] flex items-center justify-between gap-2 bg-white/[0.02]">
                <div className="flex items-center gap-2 min-w-0">
                  <Shield className="h-4 w-4 text-emerald-400 shrink-0" />
                  <div className="flex flex-col min-w-0">
                    <h4 className="text-xs font-bold text-white truncate max-w-[170px]">
                      {telemetry.name}
                    </h4>
                    <div className="flex items-center gap-1.5 text-[9px] text-white/40">
                      <span>NORAD {telemetry.noradId}</span>
                      <span>•</span>
                      <span className="text-emerald-400 font-semibold">{telemetry.operator}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => setIsInspectorMinimized(!isInspectorMinimized)}
                    className="text-white/40 hover:text-white p-1 rounded hover:bg-white/[0.05] cursor-pointer"
                    title={isInspectorMinimized ? "Expand Inspector" : "Minimize Inspector"}
                  >
                    <Minimize2 className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      if (viewerRef.current?.cesiumElement) {
                        viewerRef.current.cesiumElement.selectedEntity = undefined;
                      }
                      setSelectedSat(null);
                      setSatDetails(null);
                      setIsTracking(false);
                    }}
                    className="text-white/40 hover:text-white p-1 rounded hover:bg-white/[0.05] cursor-pointer"
                    title="Close Inspector"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {!isInspectorMinimized && (
                <div className="flex flex-col p-3.5 pt-2 gap-3">
                  {/* Sub Tabs */}
                  <div className="grid grid-cols-3 gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/[0.05] text-[10px]">
                    <button
                      onClick={() => setSatInspectorTab('telemetry')}
                      className={`py-1 rounded-lg font-bold transition-all cursor-pointer ${
                        satInspectorTab === 'telemetry' ? 'bg-white/15 text-white' : 'text-white/40 hover:text-white/80'
                      }`}
                    >
                      Telemetry
                    </button>
                    <button
                      onClick={() => setSatInspectorTab('specs')}
                      className={`py-1 rounded-lg font-bold transition-all cursor-pointer ${
                        satInspectorTab === 'specs' ? 'bg-white/15 text-white' : 'text-white/40 hover:text-white/80'
                      }`}
                    >
                      Orbital Specs
                    </button>
                    <button
                      onClick={() => setSatInspectorTab('risks')}
                      className={`py-1 rounded-lg font-bold transition-all cursor-pointer flex items-center justify-center gap-1 ${
                        satInspectorTab === 'risks' ? 'bg-white/15 text-white' : 'text-white/40 hover:text-white/80'
                      }`}
                    >
                      Risks
                      {satDetails?.active_conjunction_risks?.length > 0 && (
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-ping" />
                      )}
                    </button>
                  </div>

                  {/* TAB 1: TELEMETRY */}
                  {satInspectorTab === 'telemetry' && (
                    <div className="flex flex-col gap-2 text-xs">
                      {/* Metric row: Altitude & Velocity */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-white/[0.02] border border-white/[0.05] p-2.5 rounded-xl flex flex-col justify-between">
                          <span className="text-[9px] text-white/40 uppercase">Altitude</span>
                          <div className="flex items-center gap-1 mt-1">
                            <MatrixNumber value={telemetry.altitude.toFixed(1)} size={1.5} gap={0.5} digitGap={1.5} palette={{ on: '#38bdf8', off: 'rgba(255,255,255,0.06)' }} />
                            <span className="text-[9px] text-white/40 font-bold">KM</span>
                          </div>
                        </div>
                        <div className="bg-white/[0.02] border border-white/[0.05] p-2.5 rounded-xl flex flex-col justify-between">
                          <span className="text-[9px] text-white/40 uppercase">Velocity</span>
                          <div className="flex items-center gap-1 mt-1">
                            <MatrixNumber value={telemetry.velocity.toFixed(2)} size={1.5} gap={0.5} digitGap={1.5} palette={{ on: '#34d399', off: 'rgba(255,255,255,0.06)' }} />
                            <span className="text-[9px] text-white/40 font-bold">KM/S</span>
                          </div>
                        </div>
                      </div>

                      {/* Lat/Long Row */}
                      <div className="grid grid-cols-2 gap-2 text-[10px]">
                        <div className="flex justify-between bg-white/[0.02] border border-white/[0.05] p-2 rounded-lg">
                          <span className="text-white/40">LAT</span>
                          <span className="text-white font-semibold">{telemetry.latitude.toFixed(2)}°</span>
                        </div>
                        <div className="flex justify-between bg-white/[0.02] border border-white/[0.05] p-2 rounded-lg">
                          <span className="text-white/40">LON</span>
                          <span className="text-white font-semibold">{telemetry.longitude.toFixed(2)}°</span>
                        </div>
                      </div>

                      {/* Space Weather Drag Impact */}
                      <div className="p-2.5 bg-white/[0.02] border border-white/[0.05] rounded-xl flex flex-col gap-1 text-[10px]">
                        <div className="flex justify-between items-center">
                          <span className="text-white/40 uppercase text-[9px]">Space Weather Drag</span>
                          <span className={`px-1.5 py-0.5 rounded text-[8.5px] font-bold uppercase ${
                            telemetry.dragStatus === 'Critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                            telemetry.dragStatus === 'Elevated' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                            'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          }`}>
                            {telemetry.dragStatus || 'Nominal'}
                          </span>
                        </div>
                        <div className="flex justify-between text-[9px] text-white/50 mt-0.5">
                          <span>Decay: {telemetry.decayRate && telemetry.decayRate > 0.001 ? `${telemetry.decayRate.toFixed(2)} m/day` : 'Negligible'}</span>
                          <span>Scaler: {telemetry.dragScale ? `${telemetry.dragScale.toFixed(2)}x` : '1.0x'}</span>
                        </div>
                      </div>

                      {/* Radial Burn Slider */}
                      {isTracking && (
                        <div className="p-2.5 bg-amber-500/[0.05] border border-amber-500/20 rounded-xl flex flex-col gap-1.5">
                          <div className="flex justify-between items-center text-[9px] font-bold uppercase text-amber-400">
                            <span>Simulate Burn (Radial)</span>
                            <span>{maneuverDeltaV > 0 ? `+${maneuverDeltaV}` : maneuverDeltaV} m/s</span>
                          </div>
                          <input
                            type="range" min="-50" max="50" step="2"
                            value={maneuverDeltaV} onChange={(e) => setManeuverDeltaV(Number(e.target.value))}
                            className="w-full accent-amber-500 bg-black/60 rounded h-1 cursor-pointer"
                          />
                        </div>
                      )}

                      {/* Tracking Camera Distance Mode Selector */}
                      {isTracking && (
                        <div className="flex flex-col gap-1 p-2 bg-sky-500/[0.06] border border-sky-500/20 rounded-xl">
                          <div className="flex justify-between items-center text-[9px] font-bold text-sky-400 uppercase">
                            <span>Camera Distance</span>
                            <span className="text-[8px] text-white/50">
                              {trackCamMode === 'close' ? '120m Inspection' : trackCamMode === 'chase' ? '450m Chase Cam' : '12km Sector'}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-1">
                            <button
                              onClick={() => setTrackCamMode('close')}
                              className={`py-1 text-[8.5px] font-bold rounded-lg border transition-all cursor-pointer ${
                                trackCamMode === 'close'
                                  ? 'bg-sky-500 text-black border-sky-400 font-extrabold shadow-sm'
                                  : 'bg-black/40 text-white/60 hover:text-white border-white/[0.08]'
                              }`}
                            >
                              Close 120m
                            </button>
                            <button
                              onClick={() => setTrackCamMode('chase')}
                              className={`py-1 text-[8.5px] font-bold rounded-lg border transition-all cursor-pointer ${
                                trackCamMode === 'chase'
                                  ? 'bg-sky-500 text-black border-sky-400 font-extrabold shadow-sm'
                                  : 'bg-black/40 text-white/60 hover:text-white border-white/[0.08]'
                              }`}
                            >
                              Chase 450m
                            </button>
                            <button
                              onClick={() => setTrackCamMode('sector')}
                              className={`py-1 text-[8.5px] font-bold rounded-lg border transition-all cursor-pointer ${
                                trackCamMode === 'sector'
                                  ? 'bg-sky-500 text-black border-sky-400 font-extrabold shadow-sm'
                                  : 'bg-black/40 text-white/60 hover:text-white border-white/[0.08]'
                              }`}
                            >
                              Wide 12km
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex flex-col gap-1.5 mt-1">
                        <div className="grid grid-cols-2 gap-1.5">
                          <button
                            onClick={isTracking ? handleUntrackEntity : handleTrackEntity}
                            className={`flex items-center justify-center gap-1.5 py-1.5 font-bold rounded-lg text-[10px] cursor-pointer shadow transition-all ${
                              isTracking
                                ? 'bg-sky-500 text-black hover:bg-sky-400'
                                : 'bg-white text-black hover:bg-white/90'
                            }`}
                          >
                            <Crosshair size={12} />
                            {isTracking ? 'Tracking Active' : 'Track Orbit'}
                          </button>
                          <button
                            onClick={handleUntrackEntity}
                            className="flex items-center justify-center gap-1.5 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] text-white/70 hover:text-white rounded-lg text-[10px] border border-white/[0.08] cursor-pointer"
                          >
                            <EyeOff size={12} />
                            Reset View
                          </button>
                        </div>

                        <button
                          onClick={() => {
                            const noradId = telemetry.noradId;
                            setSelectedSatIds(prev => {
                              const newSet = new Set(prev);
                              if (newSet.has(noradId)) newSet.delete(noradId);
                              else newSet.add(noradId);
                              return newSet;
                            });
                          }}
                          className={`w-full py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1.5 cursor-pointer border transition-all ${
                            selectedSatIds.has(telemetry.noradId)
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                              : 'bg-white/[0.03] hover:bg-white/[0.06] text-white/60 hover:text-white border-white/[0.06]'
                          }`}
                        >
                          <Shield size={12} />
                          {selectedSatIds.has(telemetry.noradId) ? 'Unpin Trajectory Line' : 'Pin Trajectory Line'}
                        </button>

                        {maneuverDeltaV !== 0 && (
                          <button
                            onClick={handleExportOPM}
                            className="w-full py-1.5 bg-amber-500 text-black font-bold rounded-lg text-[10px] flex items-center justify-center gap-1.5 hover:bg-amber-400 cursor-pointer shadow"
                          >
                            <Download size={12} />
                            Export CCSDS OPM
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB 2: SPECS */}
                  {satInspectorTab === 'specs' && (
                    <div className="flex flex-col gap-2 text-[10px]">
                      {loadingDetails ? (
                        <div className="py-6 flex justify-center text-white/40"><RefreshCw className="h-4 w-4 animate-spin" /></div>
                      ) : satDetails ? (
                        <>
                          <div className="flex justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                            <span className="text-white/40">DESIGNATOR</span>
                            <span className="text-white font-bold">{satDetails.launch_designator || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                            <span className="text-white/40">LAUNCH YEAR</span>
                            <span className="text-white font-bold">{satDetails.launch_year || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                            <span className="text-white/40">INCLINATION</span>
                            <span className="text-white font-bold">{satDetails.orbital_elements?.inclination_deg?.toFixed(4) ?? '0.0000'}°</span>
                          </div>
                          <div className="flex justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                            <span className="text-white/40">ECCENTRICITY</span>
                            <span className="text-white font-bold">{satDetails.orbital_elements?.eccentricity?.toFixed(7) ?? '0.0000000'}</span>
                          </div>
                          <div className="flex justify-between p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                            <span className="text-white/40">ORBITAL PERIOD</span>
                            <span className="text-white font-bold">{satDetails.orbital_elements?.orbital_period_min ?? '--'} mins</span>
                          </div>
                        </>
                      ) : (
                        <div className="py-4 text-center text-white/30 text-[10px]">Orbital elements loaded from SGP4 propagation.</div>
                      )}
                    </div>
                  )}

                  {/* TAB 3: RISKS */}
                  {satInspectorTab === 'risks' && (
                    <div className="flex flex-col gap-2">
                      {satDetails?.active_conjunction_risks?.length ? (
                        satDetails.active_conjunction_risks.map((threat: any) => {
                          const isHigh = threat.collision_probability >= 1e-4;
                          return (
                            <div key={threat.event_id} className={`p-2.5 rounded-xl border flex flex-col gap-1 font-mono text-[9px] ${
                              isHigh ? 'bg-rose-950/30 border-rose-500/30 text-rose-300' : 'bg-amber-950/30 border-amber-500/30 text-amber-300'
                            }`}>
                              <div className="flex justify-between items-center font-bold uppercase">
                                <span className="flex items-center gap-1"><AlertTriangle size={11} /> Conjunction</span>
                                <span>{threat.collision_probability.toExponential(1)} Pc</span>
                              </div>
                              <div className="flex justify-between text-white/60">
                                <span>Target:</span>
                                <span className="text-white font-bold">{threat.other_name}</span>
                              </div>
                              <div className="flex justify-between text-white/60">
                                <span>Miss Distance:</span>
                                <span className="text-white font-bold">{threat.miss_distance_km.toFixed(3)} km</span>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="p-3 bg-emerald-950/20 border border-emerald-500/20 rounded-xl flex items-center gap-2 text-emerald-400 text-[10px]">
                          <ShieldCheck size={14} />
                          <span>No critical collision hazards detected for this object.</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════ */}
      {/* ── UNIFIED RIGHT TOOL DECK (top-20 right-6 z-30) ─────────────────── */}
      {/* ══════════════════════════════════════════════════════════════════════ */}
      <div className="absolute top-20 right-6 z-30 flex flex-col items-end gap-2.5 max-h-[calc(100vh-170px)] select-none pointer-events-none">
        
        {/* Top Action Capsule Toolbar */}
        <div className="flex items-center gap-1.5 p-1 bg-[#0a0a0a]/90 backdrop-blur-xl border border-white/[0.08] rounded-xl shadow-2xl pointer-events-auto shrink-0 font-mono">
          {/* Search & Filters Button */}
          <button
            onClick={() => setActiveRightDeck(activeRightDeck === 'search' ? 'none' : 'search')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all cursor-pointer border ${
              activeRightDeck === 'search'
                ? 'bg-white text-black border-white shadow-sm'
                : 'bg-transparent text-white/60 hover:text-white hover:bg-white/[0.05] border-transparent'
            }`}
          >
            <Search className="h-3.5 w-3.5" />
            <span>Search & Filters</span>
          </button>

          {/* Map Controls Button */}
          <button
            onClick={() => setActiveRightDeck(activeRightDeck === 'controls' ? 'none' : 'controls')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all cursor-pointer border ${
              activeRightDeck === 'controls'
                ? 'bg-white text-black border-white shadow-sm'
                : 'bg-transparent text-white/60 hover:text-white hover:bg-white/[0.05] border-transparent'
            }`}
          >
            <Settings className="h-3.5 w-3.5" />
            <span>Controls</span>
          </button>

          {/* Collision Simulation Replay Indicator if active */}
          {simulationConfig && (
            <div className="flex items-center gap-1.5 pl-2 ml-1 border-l border-white/[0.1]">
              <span className="h-2 w-2 rounded-full bg-sky-400 animate-pulse" />
              <span className="text-[10px] text-sky-300 font-bold">Replay Active</span>
            </div>
          )}
        </div>

        {/* Scrollable Right Deck Container */}
        <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar flex flex-col items-end gap-2.5 pointer-events-auto pr-0.5">
          
          {/* Collision Simulation Panel (when active) */}
          {simulationConfig && onUpdateSimConfig && onStopSim && (
            <div className="animate-slide-in">
              <CollisionSimulationPanel
                config={simulationConfig}
                onUpdateConfig={onUpdateSimConfig}
                onStop={onStopSim}
              />
            </div>
          )}

          {/* Search & Filters Panel (when active and not in simulation) */}
          {activeRightDeck === 'search' && !simulationConfig && (
            <div className="w-80 bg-[#0a0a0a]/95 backdrop-blur-2xl border border-white/[0.1] rounded-2xl p-4 flex flex-col gap-3.5 shadow-2xl animate-slide-in font-mono text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                <div className="flex items-center gap-2 text-xs font-bold text-white uppercase">
                  <Search className="h-3.5 w-3.5 text-emerald-400" />
                  Search & Filters
                </div>
                <button onClick={() => setActiveRightDeck('none')} className="text-white/40 hover:text-white p-0.5 cursor-pointer">
                  <X size={14} />
                </button>
              </div>

              {/* Earth Imagery Selector */}
              <div className="flex flex-col gap-1.5 border-b border-white/[0.06] pb-3">
                <span className="text-[9.5px] font-bold text-white/50 uppercase tracking-wider flex items-center gap-1">
                  <Globe size={11} className="text-emerald-400" /> Earth Imagery Quality
                </span>
                <div className="grid grid-cols-3 gap-1">
                  <button onClick={() => setEarthStyle('satellite')} className={`py-1.5 rounded-lg text-[9px] font-bold border transition-all cursor-pointer ${earthStyle === 'satellite' ? 'bg-white/15 text-white border-white/30' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}>NASA Blue</button>
                  <button onClick={() => setEarthStyle('dark')} className={`py-1.5 rounded-lg text-[9px] font-bold border transition-all cursor-pointer ${earthStyle === 'dark' ? 'bg-white/15 text-white border-white/30' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}>Cyber Dark</button>
                  <button onClick={() => setEarthStyle('natural')} className={`py-1.5 rounded-lg text-[9px] font-bold border transition-all cursor-pointer ${earthStyle === 'natural' ? 'bg-white/15 text-white border-white/30' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}>ArcGIS HD</button>
                </div>
              </div>

              {/* Visibility Layers */}
              <div className="flex flex-col gap-1.5 border-b border-white/[0.06] pb-3">
                <span className="text-[9.5px] font-bold text-white/50 uppercase tracking-wider flex items-center gap-1">
                  <Sliders size={11} /> Visibility Layers
                </span>
                <div className="grid grid-cols-4 gap-1">
                  <button onClick={() => setShow3DModels(!show3DModels)} className={`py-1.5 rounded-lg text-[9px] font-bold border transition-all cursor-pointer flex items-center justify-center gap-1 ${show3DModels ? 'bg-white/15 text-white border-white/30' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}><Box size={10} /> 3D GLB</button>
                  <button onClick={() => setShowPayloads?.(!showPayloads)} className={`py-1.5 rounded-lg text-[9px] font-bold border transition-all cursor-pointer flex items-center justify-center gap-1 ${showPayloads ? 'bg-white/15 text-white border-white/30' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}><Eye size={10} /> Sats</button>
                  <button onClick={() => setShowDebris?.(!showDebris)} className={`py-1.5 rounded-lg text-[9px] font-bold border transition-all cursor-pointer flex items-center justify-center gap-1 ${showDebris ? 'bg-white/15 text-white border-white/30' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}><Eye size={10} /> Debris</button>
                  <button onClick={() => setShowSensors?.(!showSensors)} className={`py-1.5 rounded-lg text-[9px] font-bold border transition-all cursor-pointer flex items-center justify-center gap-1 ${showSensors ? 'bg-white/15 text-white border-white/30' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}><MapPin size={10} className="text-emerald-400" /> Sensors</button>
                </div>
              </div>

              {/* Operator Filter */}
              <div className="flex flex-col gap-1.5 border-b border-white/[0.06] pb-3">
                <span className="text-[9.5px] font-bold text-white/50 uppercase tracking-wider flex items-center gap-1">
                  <MapPin size={11} /> Filter Operator
                </span>
                <div className="grid grid-cols-3 gap-1">
                  {["ALL", "SpaceX", "NASA", "ESA", "ISRO", "Roscosmos"].map((op) => (
                    <button key={op} onClick={() => setOperatorFilter(op)} className={`py-1 rounded-lg text-[8.5px] font-bold border transition-all cursor-pointer ${operatorFilter === op ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-transparent text-white/40 border-white/[0.05] hover:text-white'}`}>
                      {op.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic Query Search */}
              <div className="flex flex-col gap-1">
                <span className="text-[9.5px] font-bold text-white/50 uppercase tracking-wider">Query Satellite</span>
                <input
                  type="text"
                  placeholder="Search name or NORAD..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-black/60 border border-white/10 p-2 rounded-lg text-white placeholder-white/30 text-xs focus:outline-none focus:border-white/30"
                />
              </div>

              {/* Instant Search Results */}
              {searchQuery.trim() !== "" && (
                <div className="flex flex-col gap-1 max-h-28 overflow-y-auto pr-1 border-t border-white/[0.06] pt-2">
                  {czmlData
                    .filter((p: any) => {
                      if (p.id === "document") return false;
                      const name = (p.name || "").toLowerCase();
                      const q = searchQuery.toLowerCase().trim();
                      return name.includes(q) || p.id.replace("sat_", "").includes(q);
                    })
                    .slice(0, 5)
                    .map((p: any) => {
                      const noradId = p.id.replace("sat_", "");
                      return (
                        <button
                          key={p.id}
                          onClick={() => handleSelectSearchResult(p.id)}
                          className="w-full text-left bg-white/[0.02] hover:bg-white/[0.06] p-1.5 rounded-lg text-[10px] text-white/80 hover:text-white flex justify-between items-center transition-colors cursor-pointer"
                        >
                          <span className="truncate max-w-[170px] font-semibold">{p.name}</span>
                          <span className="text-[8.5px] text-white/40 font-mono">NORAD {noradId}</span>
                        </button>
                      );
                    })}
                </div>
              )}
            </div>
          )}

          {/* Map Controls Panel (when active and not in simulation) */}
          {activeRightDeck === 'controls' && !simulationConfig && (
            <div className="w-80 bg-[#0a0a0a]/95 backdrop-blur-2xl border border-white/[0.1] rounded-2xl p-4 flex flex-col gap-4 shadow-2xl animate-slide-in font-mono text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                <div className="flex items-center gap-2 text-xs font-bold text-white uppercase">
                  <Settings className="h-3.5 w-3.5 text-emerald-400" />
                  Map Controls
                </div>
                <button onClick={() => setActiveRightDeck('none')} className="text-white/40 hover:text-white p-0.5 cursor-pointer">
                  <X size={14} />
                </button>
              </div>

              {/* LEO Debris Heatmap Toggle */}
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
                <LeverSwitch
                  checked={showHeatmap}
                  onCheckedChange={(checked) => setShowHeatmap?.(checked)}
                  label="LEO Debris Heatmap"
                  sublabel="Density cluster overlay"
                />
              </div>

              {/* Catalog Render Limit */}
              <div className="flex flex-col gap-1.5 border-b border-white/[0.06] pb-3">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="text-white/50 uppercase">Render Limit</span>
                  <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-amber-400 font-bold">{limit} Sats</span>
                </div>
                <input
                  type="range" min="10" max="5000" step="50" value={limit}
                  onChange={(e) => setLimit?.(parseInt(e.target.value))}
                  className="w-full h-1 bg-white/10 rounded cursor-pointer accent-emerald-400"
                />
              </div>

              {/* Propagation Speed */}
              <div className="flex flex-col gap-1.5 border-b border-white/[0.06] pb-3">
                <span className="text-[9.5px] font-bold text-white/50 uppercase tracking-wider flex items-center gap-1">
                  <Gauge size={11} /> Propagation Speed
                </span>
                <div className="grid grid-cols-5 gap-1 bg-white/[0.02] p-1 rounded-xl border border-white/[0.05]">
                  {[
                    { label: "1x", val: 1 },
                    { label: "10x", val: 10 },
                    { label: "60x", val: 60 },
                    { label: "600x", val: 600 },
                    { label: "3600x", val: 3600 }
                  ].map((m) => (
                    <button
                      key={m.label} onClick={() => setMultiplier?.(m.val)}
                      className={`py-1 text-[9px] font-bold rounded-lg transition-all cursor-pointer ${
                        multiplier === m.val ? 'bg-white text-black shadow-sm' : 'text-white/40 hover:text-white'
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Color Legend */}
              <div className="p-2.5 bg-white/[0.02] border border-white/[0.05] rounded-xl flex flex-col gap-1.5 text-[10px]">
                <div className="text-[9px] font-bold text-white/40 uppercase tracking-wider">Map Color Codes</div>
                <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-400" /><span className="text-white/70">Operational Satellite</span></div>
                <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-red-500" /><span className="text-white/70">Debris Fragment</span></div>
                <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-amber-500" /><span className="text-white/70">Spent Rocket Body</span></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

