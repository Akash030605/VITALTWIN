"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";

const HeartModelScene = dynamic(() => import("./three/HeartModelScene").then((m) => m.default), { ssr: false });
const BrainModelScene = dynamic(() => import("./three/BrainModelScene").then((m) => m.default), { ssr: false });
const LiverModelScene = dynamic(() => import("./three/LiverModelScene").then((m) => m.default), { ssr: false });
const KidneyModelScene = dynamic(() => import("./three/KidneyModelScene").then((m) => m.default), { ssr: false });
const LungsModelScene = dynamic(() => import("./three/LungsModelScene").then((m) => m.default), { ssr: false });

const SCENES = {
  heart: HeartModelScene,
  brain: BrainModelScene,
  liver: LiverModelScene,
  kidney: KidneyModelScene,
  lungs: LungsModelScene,
};

export default function OrganModelView({ organId, className = "", style }) {
  const Scene = organId ? SCENES[organId] : null;
  if (!Scene) return <div className={`bg-(--color-surface)/50 flex items-center justify-center ${className}`}><span className="text-(--color-muted) text-sm">No model</span></div>;

  return (
    <div className={`overflow-hidden w-full h-full min-h-[280px] ${className}`} style={style}>
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }} gl={{ antialias: true, alpha: true }}>
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
    </div>
  );
}
