"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import {
  BufferAttribute,
  Color,
  InstancedMesh,
  Mesh,
  Object3D,
  PlaneGeometry,
} from "three";
import { useTheme } from "@/lib/theme";
import {
  MAX_VEGETATION,
  TERRAIN_SIZE,
  VEGETATION_LAYOUT,
  terrainHeight,
  type WetlandSceneParams,
} from "./wetlandModel";

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(query.matches);
    const handler = (event: MediaQueryListEvent) => setReduced(event.matches);
    query.addEventListener("change", handler);
    return () => query.removeEventListener("change", handler);
  }, []);
  return reduced;
}

function Terrain() {
  const geometry = useMemo(() => {
    const size = TERRAIN_SIZE;
    const segments = 64;
    const geo = new PlaneGeometry(size, size, segments, segments);
    geo.rotateX(-Math.PI / 2);
    const position = geo.attributes.position as BufferAttribute;
    const colors = new Float32Array(position.count * 3);
    const low = new Color("#44503f");
    const high = new Color("#7c8a5b");
    const wet = new Color("#2f4a3b");
    for (let i = 0; i < position.count; i++) {
      const x = position.getX(i);
      const z = position.getZ(i);
      const y = terrainHeight(x, z);
      position.setY(i, y);
      const t = Math.min(1, Math.max(0, (y + 0.7) / 1.4));
      const color = low.clone().lerp(high, t).lerp(wet, 0.3 * (1 - t));
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    geo.setAttribute("color", new BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    return geo;
  }, []);

  useEffect(() => () => geometry.dispose(), [geometry]);

  return (
    <mesh geometry={geometry} receiveShadow>
      <meshStandardMaterial vertexColors roughness={0.95} metalness={0} />
    </mesh>
  );
}

function Water({
  level,
  active,
  reducedMotion,
}: {
  level: number;
  active: boolean;
  reducedMotion: boolean;
}) {
  const ref = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    const mesh = ref.current;
    if (!mesh) return;
    if (active && !reducedMotion) {
      const time = clock.getElapsedTime();
      mesh.position.y = level + Math.sin(time * 0.8) * 0.01;
      (mesh.material as { opacity: number }).opacity =
        0.5 + Math.sin(time * 1.3) * 0.05;
    } else {
      mesh.position.y = level;
    }
  });

  return (
    <mesh ref={ref} position={[0, level, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[TERRAIN_SIZE, TERRAIN_SIZE]} />
      <meshStandardMaterial
        color="#2b6cb0"
        transparent
        opacity={0.5}
        roughness={0.15}
        metalness={0.1}
      />
    </mesh>
  );
}

function Vegetation({
  density,
  health,
}: {
  density: number;
  health: number;
}) {
  const ref = useRef<InstancedMesh>(null);
  const count = Math.round(
    Math.min(1, Math.max(0, density)) * MAX_VEGETATION,
  );

  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const dummy = new Object3D();
    const brown = new Color("#8a6d3b");
    const green = new Color("#2f7d32");
    const color = new Color();
    for (let i = 0; i < MAX_VEGETATION; i++) {
      const instance = VEGETATION_LAYOUT[i];
      const visible = i < count;
      dummy.position.set(instance.x, instance.y + 0.06, instance.z);
      dummy.rotation.set(0, instance.rotation, 0);
      dummy.scale.setScalar(visible ? instance.scale : 0);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
      if (visible) {
        color.lerpColors(brown, green, health);
        mesh.setColorAt(i, color);
      }
    }
    mesh.count = count;
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  }, [count, health]);

  return (
    <instancedMesh ref={ref} args={[undefined, undefined, MAX_VEGETATION]} castShadow>
      <coneGeometry args={[0.045, 0.28, 4]} />
      <meshStandardMaterial roughness={0.9} metalness={0} />
    </instancedMesh>
  );
}

function CarbonBeacon({ level }: { level: number }) {
  const height = 0.4 + level * 1.6;
  const color = useMemo(
    () => new Color("#12b76a").lerp(new Color("#f79009"), 1 - level),
    [level],
  );
  return (
    <group position={[3.4, 0, 3.4]}>
      <mesh position={[0, height / 2, 0]} castShadow>
        <cylinderGeometry args={[0.05, 0.05, height, 12]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
      </mesh>
      <mesh position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.12, 0.16, 24]} />
        <meshBasicMaterial color={color} transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

function Scene({
  params,
  active,
  reducedMotion,
  dark,
}: {
  params: WetlandSceneParams;
  active: boolean;
  reducedMotion: boolean;
  dark: boolean;
}) {
  const background = dark ? "#060b14" : "#cfe8f3";
  return (
    <>
      <color attach="background" args={[background]} />
      <fog attach="fog" args={[background, 13, 27]} />
      <hemisphereLight intensity={0.65} groundColor="#3b4a3f" />
      <ambientLight intensity={0.25} />
      <directionalLight position={[6, 10, 4]} intensity={1.2} castShadow />
      <Terrain />
      <Water
        level={params.waterLevel}
        active={active}
        reducedMotion={reducedMotion}
      />
      <Vegetation
        density={params.vegetationDensity}
        health={params.vegetationHealth}
      />
      <CarbonBeacon level={params.carbonLevel} />
      <OrbitControls
        enablePan={false}
        minDistance={6}
        maxDistance={18}
        maxPolarAngle={Math.PI / 2.2}
        autoRotate={active && !reducedMotion}
        autoRotateSpeed={0.4}
      />
    </>
  );
}

export default function WetlandScene({
  params,
  active,
}: {
  params: WetlandSceneParams;
  active: boolean;
}) {
  const { theme } = useTheme();
  const reducedMotion = usePrefersReducedMotion();

  return (
    <Canvas
      dpr={[1, 2]}
      shadows
      frameloop={active ? "always" : "demand"}
      camera={{ position: [7.5, 6, 7.5], fov: 45 }}
      gl={{ antialias: true }}
      className="h-full w-full"
    >
      <Scene
        params={params}
        active={active}
        reducedMotion={reducedMotion}
        dark={theme === "dark"}
      />
    </Canvas>
  );
}
