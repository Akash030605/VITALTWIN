"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import HumanModelScene from "./three/HumanModelScene";

export default function HumanModelView({ className = "" }) {
  return (
    <div className={`overflow-hidden w-full h-full ${className}`}>
      <Canvas
        camera={{ position: [0, 0, 15], fov: 75 }}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <HumanModelScene />
        </Suspense>
      </Canvas>
    </div>
  );
}
