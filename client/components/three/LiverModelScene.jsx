"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, OrbitControls, Center } from "@react-three/drei";

const MODEL_URL = "/models/liver/liver.gltf";
if (typeof window !== "undefined") useGLTF.preload(MODEL_URL);

function LiverMesh() {
  const group = useRef(null);
  const { scene } = useGLTF(MODEL_URL);
  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.2;
  });
  return (
    <Center>
      <group ref={group} scale={12}>
        <primitive object={scene} />
      </group>
    </Center>
  );
}

export default function LiverModelScene() {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 5, 5]} intensity={1.2} />
      <pointLight position={[0, 2, 2]} intensity={0.5} color="#2dd4bf" />
      <LiverMesh />
      <OrbitControls enableZoom={false} />
    </>
  );
}
