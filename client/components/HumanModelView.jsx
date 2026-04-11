"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import HumanModelScene from "./three/HumanModelScene";

export default function HumanModelView({ className = "" }) {
  return (
    // Both the wrapper div AND the canvas have pointer-events:none.
    // This stops R3F's canvas from intercepting wheel/scroll events,
    // which was causing the model to zoom when the user scrolled the page.
    <div
      className={`overflow-hidden w-full h-full ${className}`}
      style={{ pointerEvents: "none" }}
    >
      <Canvas
        camera={{ position: [0, 0, 15], fov: 75 }}
        gl={{ antialias: true, alpha: true }}
        style={{ pointerEvents: "none" }}
      >
        <Suspense fallback={null}>
          <HumanModelScene />
        </Suspense>
      </Canvas>
    </div>
  );
}
