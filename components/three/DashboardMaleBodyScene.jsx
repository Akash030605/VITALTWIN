"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, OrbitControls, Center } from "@react-three/drei";

const MALEBODY_URL = "/models/malebody/scene.gltf";

if (typeof window !== "undefined") {
  useGLTF.preload(MALEBODY_URL);
}

function DashboardMaleBodyMesh() {
  const group = useRef(null);
  const { scene } = useGLTF(MALEBODY_URL);

  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.2;
  });

  return (
    <Center>
      <group ref={group} scale={220}>
        <primitive object={scene} />
      </group>
    </Center>
  );
}

export default function DashboardMaleBodyScene() {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[6, 6, 6]} intensity={1.6} />
      <directionalLight position={[-4, 4, -4]} intensity={0.7} />
      <directionalLight position={[0, 8, 2]} intensity={0.5} />
      <DashboardMaleBodyMesh />
      <OrbitControls enableZoom minDistance={4} maxDistance={20} />
    </>
  );
}

