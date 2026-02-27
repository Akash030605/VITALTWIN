"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";

const BodyModelScene = dynamic(() => import("./three/BodyModelScene").then((m) => m.default), { ssr: false });

/** Renders male or female body model based on profile gender. ageingLevel 0–1 drives colour tint. */
export default function BodyModelView({ gender, ageingLevel = 0, className = "", showScanRing = true }) {
  return (
    <div className={`overflow-hidden w-full h-full min-h-[280px] rounded-xl bg-black/30 relative ${showScanRing ? "scan-ring-wrap" : ""} ${className}`}>
      <Canvas camera={{ position: [0, 0, 16], fov: 50 }} gl={{ antialias: true, alpha: true }}>
        <Suspense fallback={null}>
          <BodyModelScene gender={gender} ageingLevel={ageingLevel} />
        </Suspense>
      </Canvas>
      {showScanRing && <div className="model-glow-overlay" aria-hidden />}
    </div>
  );
}
