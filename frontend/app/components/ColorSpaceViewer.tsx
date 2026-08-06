"use client";

import { Grid, Line, OrbitControls } from "@react-three/drei";
import { Canvas, type ThreeEvent } from "@react-three/fiber";
import { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import type { ExtractResult, VisualizationPoint } from "../lib/api";

type Position = [number, number, number];

function labToPosition([lightness, a, b]: [number, number, number]): Position {
  return [a / 55, (lightness - 50) / 25, b / 55];
}

function PointCloud({
  points,
  activeCluster,
  onHover,
}: {
  points: VisualizationPoint[];
  activeCluster: number | null;
  onHover: (index: number | null) => void;
}) {
  const geometry = useMemo(() => {
    const positions = new Float32Array(points.length * 3);
    const colors = new Float32Array(points.length * 3);
    const color = new THREE.Color();

    points.forEach((point, index) => {
      const [x, y, z] = labToPosition(point.lab);
      positions.set([x, y, z], index * 3);

      const isMuted = activeCluster !== null && point.cluster !== activeCluster;
      color.setRGB(
        point.rgb[0] / 255,
        point.rgb[1] / 255,
        point.rgb[2] / 255,
        THREE.SRGBColorSpace,
      );
      const intensity = isMuted ? 0.16 : 1;
      colors.set([color.r * intensity, color.g * intensity, color.b * intensity], index * 3);
    });

    const nextGeometry = new THREE.BufferGeometry();
    nextGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    nextGeometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    nextGeometry.computeBoundingSphere();
    return nextGeometry;
  }, [activeCluster, points]);

  useEffect(() => () => geometry.dispose(), [geometry]);

  function handlePointerMove(event: ThreeEvent<PointerEvent>) {
    event.stopPropagation();
    onHover(event.index ?? null);
  }

  return (
    <points
      geometry={geometry}
      onPointerMove={handlePointerMove}
      onPointerOut={() => onHover(null)}
    >
      <pointsMaterial
        size={0.052}
        sizeAttenuation
        vertexColors
        transparent
        opacity={0.86}
        depthWrite={false}
      />
    </points>
  );
}

function Scene({
  result,
  activeCluster,
  onClusterSelect,
  onHover,
}: {
  result: ExtractResult;
  activeCluster: number | null;
  onClusterSelect: (cluster: number) => void;
  onHover: (index: number | null) => void;
}) {
  const points = result.visualization?.points ?? [];

  return (
    <>
      <color attach="background" args={["#0b0d0d"]} />
      <fog attach="fog" args={["#0b0d0d", 7.5, 12]} />
      <ambientLight intensity={1.8} />
      <directionalLight position={[3, 5, 4]} intensity={2.4} />

      <Grid
        position={[0, -2.02, 0]}
        args={[10, 10]}
        cellSize={0.4}
        cellThickness={0.45}
        cellColor="#343837"
        sectionSize={2}
        sectionThickness={0.8}
        sectionColor="#565d5a"
        fadeDistance={9}
        fadeStrength={1.5}
        infiniteGrid
      />

      <Line points={[[-2.7, 0, 0], [2.7, 0, 0]]} color="#ef675f" lineWidth={1.2} />
      <Line points={[[0, -2.1, 0], [0, 2.25, 0]]} color="#f1eee4" lineWidth={1.2} />
      <Line points={[[0, 0, -2.7], [0, 0, 2.7]]} color="#5875e8" lineWidth={1.2} />

      <PointCloud points={points} activeCluster={activeCluster} onHover={onHover} />

      {result.palette.map((swatch) => {
        const isActive = activeCluster === null || activeCluster === swatch.rank;
        return (
          <group key={swatch.rank} position={labToPosition(swatch.lab)}>
            <mesh
              scale={isActive ? 1 : 0.72}
              onClick={(event) => {
                event.stopPropagation();
                onClusterSelect(swatch.rank);
              }}
            >
              <sphereGeometry args={[0.115, 24, 24]} />
              <meshStandardMaterial
                color={swatch.hex}
                roughness={0.36}
                metalness={0.08}
                transparent
                opacity={isActive ? 1 : 0.35}
              />
            </mesh>
            <mesh scale={isActive ? 1 : 0.72}>
              <sphereGeometry args={[0.155, 18, 18]} />
              <meshBasicMaterial color="#f4f0e5" wireframe transparent opacity={isActive ? 0.5 : 0.12} />
            </mesh>
          </group>
        );
      })}

      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.08}
        minDistance={3.2}
        maxDistance={10}
        target={[0, 0, 0]}
      />
    </>
  );
}

export function ColorSpaceViewer({
  result,
  activeCluster,
  onClusterSelect,
}: {
  result: ExtractResult;
  activeCluster: number | null;
  onClusterSelect: (cluster: number) => void;
}) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const hovered =
    hoveredIndex === null ? null : (result.visualization?.points[hoveredIndex] ?? null);

  return (
    <div className="viewer-frame">
      <div className="viewer-axis viewer-axis-x"><span />a* · green → red</div>
      <div className="viewer-axis viewer-axis-y"><span />L* · black → white</div>
      <div className="viewer-axis viewer-axis-z"><span />b* · blue → yellow</div>

      <div className="viewer-canvas" aria-hidden="true">
        <Canvas
          frameloop="demand"
          dpr={[1, 1.75]}
          camera={{ position: [4.8, 3.4, 5.4], fov: 42, near: 0.1, far: 50 }}
          gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
        >
          <Scene
            result={result}
            activeCluster={activeCluster}
            onClusterSelect={onClusterSelect}
            onHover={setHoveredIndex}
          />
        </Canvas>
      </div>

      <div className="viewer-readout" aria-live="polite">
        {hovered ? (
          <>
            <span>bin {hoveredIndex! + 1}</span>
            <strong>
              L* {hovered.lab[0].toFixed(1)} · a* {hovered.lab[1].toFixed(1)} · b*{" "}
              {hovered.lab[2].toFixed(1)}
            </strong>
            <span>{(hovered.weight * 100).toFixed(3)}% weight</span>
          </>
        ) : (
          <>
            <span>navigation</span>
            <strong>Drag to orbit · scroll to zoom</strong>
            <span>select a swatch to isolate its cluster</span>
          </>
        )}
      </div>
      <p className="sr-only">
        Interactive CIELAB plot with {result.visualization?.displayed_bins ?? 0} weighted histogram
        bins and {result.palette.length} cluster centers. The palette list beside this plot provides
        the same cluster information without requiring the canvas.
      </p>
    </div>
  );
}
