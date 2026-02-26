"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, OrbitControls, Center } from "@react-three/drei";

const MODEL_URL = "/models/human/scene.gltf";
if (typeof window !== "undefined") useGLTF.preload(MODEL_URL);

function HumanMesh() {
  const group = useRef(null);
  const { scene } = useGLTF(MODEL_URL);

  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.25;
  });

  return (
    <Center>
      <group ref={group} scale={0.95}>
        <primitive object={scene} />
      </group>
    </Center>
  );
}

export default function HumanModelScene() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1.2} />
      <directionalLight position={[-3, 5, -3]} intensity={0.4} />
      <HumanMesh />
      <OrbitControls enableZoom minDistance={5} maxDistance={14} />
    </>
  );
}
