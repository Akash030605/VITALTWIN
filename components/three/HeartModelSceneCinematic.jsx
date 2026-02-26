"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, Center } from "@react-three/drei";

const MODEL_URL = "/models/heart/heart.gltf";
if (typeof window !== "undefined") useGLTF.preload(MODEL_URL);

const PULSE_PERIOD = 60 / 72;
const PULSE_AMPLITUDE = 0.04;

function HeartMesh() {
  const group = useRef(null);
  const { scene } = useGLTF(MODEL_URL);

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.elapsedTime;
    const phase = (t % PULSE_PERIOD) / PULSE_PERIOD;
    const pulse = Math.sin(phase * Math.PI * 2);
    const scale = 2 * (1 + PULSE_AMPLITUDE * (0.5 + 0.5 * pulse));
    group.current.scale.setScalar(scale);
  });

  return (
    <Center>
      <group ref={group}>
        <primitive object={scene} />
      </group>
    </Center>
  );
}

export default function HeartModelSceneCinematic() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1.2} />
      <pointLight position={[0, 2, 2]} intensity={0.7} color="#2dd4bf" />
      <HeartMesh />
    </>
  );
}
