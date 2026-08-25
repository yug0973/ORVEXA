import * as Cesium from 'cesium';

/**
 * Procedurally generates 6 crystal-clear, high-resolution (1024x1024) Deep Space & Milky Way
 * cubemap faces with authentic stellar magnitudes, astronomical star colors (O/B blue to M red),
 * and subtle galactic dust nebulae, replacing Cesium's noisy default 8-bit skybox.
 */
export function createRealisticSpaceSkyBox(): Cesium.SkyBox {
  const FACE_SIZE = 1024;
  const faces = ['positiveX', 'negativeX', 'positiveY', 'negativeY', 'positiveZ', 'negativeZ'] as const;
  const sources: Record<string, string> = {};

  // Deterministic PRNG for consistent, beautiful starfield layout
  let seed = 42;
  function random() {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  }

  // Pre-generate ~4000 astronomical stars with 3D unit vectors
  interface Star {
    x: number;
    y: number;
    z: number;
    radius: number;
    brightness: number;
    r: number;
    g: number;
    b: number;
    halo: boolean;
  }

  const stars: Star[] = [];
  const TOTAL_STARS = 4500;

  for (let i = 0; i < TOTAL_STARS; i++) {
    // Uniform sphere point picking
    const u = random();
    const v = random();
    const theta = u * 2.0 * Math.PI;
    const phi = Math.acos(2.0 * v - 1.0);
    const sinPhi = Math.sin(phi);

    let x = sinPhi * Math.cos(theta);
    let y = sinPhi * Math.sin(theta);
    let z = Math.cos(phi);

    // Galactic coordinate approximation: Galactic equator near Y-Z inclined plane
    const galDist = Math.abs(x * 0.7 + y * 0.2 + z * 0.68);
    // Concentrate stars towards the Milky Way galactic plane
    if (random() > 0.4 && galDist > 0.35) {
      continue;
    }

    // Stellar classification & temperature colors (O/B blue-white, A/F white, G yellow, K orange, M red)
    const typeRoll = random();
    let r = 255, g = 255, b = 255;
    if (typeRoll < 0.15) {
      // O/B Blue giant
      r = 180 + Math.floor(random() * 40);
      g = 205 + Math.floor(random() * 40);
      b = 255;
    } else if (typeRoll < 0.35) {
      // A/F White star
      r = 235 + Math.floor(random() * 20);
      g = 240 + Math.floor(random() * 15);
      b = 255;
    } else if (typeRoll < 0.65) {
      // G/K Yellow-Orange star (Sun-like / Arcturus)
      r = 255;
      g = 220 + Math.floor(random() * 30);
      b = 160 + Math.floor(random() * 40);
    } else if (typeRoll < 0.85) {
      // K/M Red dwarf / giant
      r = 255;
      g = 140 + Math.floor(random() * 50);
      b = 120 + Math.floor(random() * 40);
    }

    // Apparent magnitude distribution (power law: few bright stars, many faint stars)
    const magFactor = Math.pow(random(), 3.5);
    const isMajorStar = random() < 0.03;
    const radius = isMajorStar ? 1.8 + random() * 1.4 : 0.6 + magFactor * 0.9;
    const brightness = isMajorStar ? 0.95 : 0.35 + magFactor * 0.6;

    stars.push({
      x, y, z,
      radius,
      brightness,
      r, g, b,
      halo: isMajorStar
    });
  }

  // Helper to map 3D vector to Cube Face (u, v) in [-1, 1]
  function projectToFace(star: Star, face: typeof faces[number]): { u: number; v: number } | null {
    const { x, y, z } = star;
    let u = 0, v = 0, depth = 0;

    switch (face) {
      case 'positiveX': // +X
        if (x <= 0) return null;
        u = -z / x;
        v = -y / x;
        depth = x;
        break;
      case 'negativeX': // -X
        if (x >= 0) return null;
        u = z / -x;
        v = -y / -x;
        depth = -x;
        break;
      case 'positiveY': // +Y
        if (y <= 0) return null;
        u = x / y;
        v = z / y;
        depth = y;
        break;
      case 'negativeY': // -Y
        if (y >= 0) return null;
        u = x / -y;
        v = -z / -y;
        depth = -y;
        break;
      case 'positiveZ': // +Z
        if (z <= 0) return null;
        u = x / z;
        v = -y / z;
        depth = z;
        break;
      case 'negativeZ': // -Z
        if (z >= 0) return null;
        u = -x / -z;
        v = -y / -z;
        depth = -z;
        break;
    }

    if (Math.abs(u) > 1.05 || Math.abs(v) > 1.05 || depth <= 0.01) return null;
    return { u, v };
  }

  // Render each of the 6 cube faces
  for (const face of faces) {
    const canvas = document.createElement('canvas');
    canvas.width = FACE_SIZE;
    canvas.height = FACE_SIZE;
    const ctx = canvas.getContext('2d');
    if (!ctx) continue;

    // 1. Deep Space Obsidian Base (Zero noise, velvety pure black)
    ctx.fillStyle = '#020205';
    ctx.fillRect(0, 0, FACE_SIZE, FACE_SIZE);

    // 2. Cosmic Galactic Nebula Dust Clouds (Milky Way core glow)
    const bgGrad = ctx.createRadialGradient(
      FACE_SIZE * 0.5, FACE_SIZE * 0.5, 50,
      FACE_SIZE * 0.5, FACE_SIZE * 0.5, FACE_SIZE * 0.7
    );
    bgGrad.addColorStop(0, 'rgba(25, 20, 45, 0.28)');
    bgGrad.addColorStop(0.4, 'rgba(15, 18, 35, 0.16)');
    bgGrad.addColorStop(0.8, 'rgba(5, 7, 18, 0.08)');
    bgGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, FACE_SIZE, FACE_SIZE);

    // Secondary stellar gas lane
    const gasGrad = ctx.createLinearGradient(0, 0, FACE_SIZE, FACE_SIZE);
    gasGrad.addColorStop(0, 'rgba(40, 20, 60, 0.12)');
    gasGrad.addColorStop(0.5, 'rgba(20, 35, 70, 0.18)');
    gasGrad.addColorStop(1, 'rgba(10, 15, 30, 0.08)');
    ctx.fillStyle = gasGrad;
    ctx.fillRect(0, 0, FACE_SIZE, FACE_SIZE);

    // 3. Render Crisp Stars on this Face
    for (const star of stars) {
      const proj = projectToFace(star, face);
      if (!proj) continue;

      // Convert [-1, 1] to pixel [0, FACE_SIZE]
      const px = ((proj.u + 1) / 2) * FACE_SIZE;
      const py = ((proj.v + 1) / 2) * FACE_SIZE;

      // Subtle diffraction bloom for brightest stars
      if (star.halo) {
        const haloGrad = ctx.createRadialGradient(px, py, 0, px, py, star.radius * 4.5);
        haloGrad.addColorStop(0, `rgba(${star.r}, ${star.g}, ${star.b}, ${star.brightness * 0.6})`);
        haloGrad.addColorStop(0.4, `rgba(${star.r}, ${star.g}, ${star.b}, ${star.brightness * 0.15})`);
        haloGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = haloGrad;
        ctx.beginPath();
        ctx.arc(px, py, star.radius * 4.5, 0, Math.PI * 2);
        ctx.fill();
      }

      // Crisp Star Core
      ctx.fillStyle = `rgba(${star.r}, ${star.g}, ${star.b}, ${star.brightness})`;
      ctx.beginPath();
      ctx.arc(px, py, Math.max(0.5, star.radius), 0, Math.PI * 2);
      ctx.fill();
    }

    sources[face] = canvas.toDataURL('image/png');
  }

  return new Cesium.SkyBox({
    sources: {
      positiveX: sources.positiveX,
      negativeX: sources.negativeX,
      positiveY: sources.positiveY,
      negativeY: sources.negativeY,
      positiveZ: sources.positiveZ,
      negativeZ: sources.negativeZ,
    }
  });
}
