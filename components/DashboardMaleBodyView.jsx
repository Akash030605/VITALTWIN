"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";

const DashboardMaleBodyScene = dynamic(() => import("./three/DashboardMaleBodyScene").then((m) => m.default), { ssr: false });

export default function DashboardMaleBodyView({ className = "", showScanRing = true }) {
  return (
    <div className={`overflow-hidden w-full h-full min-h-[280px] rounded-xl bg-black/30 relative ${showScanRing ? "scan-ring-wrap" : ""} ${className}`}>
      <Canvas camera={{ position: [0, 1, 8], fov: 50 }} gl={{ antialias: true, alpha: true }}>
        <Suspense fallback={null}>
          <DashboardMaleBodyScene />
        </Suspense>
      </Canvas>
      {showScanRing && <div className="model-glow-overlay" aria-hidden />}
    </div>
  );
}

