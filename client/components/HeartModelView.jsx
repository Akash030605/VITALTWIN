"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import HeartModelScene from "./three/HeartModelScene";

export default function HeartModelView({ className = "", size, fullHeight = false }) {
  const isFullHeight = fullHeight ?? !size;
  return (
    <div
      className={`overflow-hidden w-full h-full ${isFullHeight ? "min-h-[50vh] lg:min-h-[calc(100vh-4rem)]" : ""} ${className}`}
      style={!isFullHeight && size ? { width: size, height: size } : undefined}
    >
      <Canvas
        camera={{ position: [0, 0, 5.5], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <HeartModelScene />
        </Suspense>
      </Canvas>
    </div>
  );
}
