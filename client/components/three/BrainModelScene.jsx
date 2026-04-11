"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, OrbitControls, Center } from "@react-three/drei";

const MODEL_URL = "/models/brain/brain.gltf";
if (typeof window !== "undefined") useGLTF.preload(MODEL_URL);

function BrainMesh() {
  const group = useRef(null);
  const { scene } = useGLTF(MODEL_URL);
  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.12;
  });
  return (
    <Center>
      <group ref={group} scale={2.2}>
        <primitive object={scene} />
      </group>
    </Center>
  );
}

export default function BrainModelScene() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={1.1} />
      <pointLight position={[0, 2, 3]} intensity={0.7} color="#2dd4bf" />
      <BrainMesh />
      <OrbitControls enableZoom={false} />
    </>
  );
}
