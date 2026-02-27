"use client";

import { useRef, useMemo, useEffect } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF, OrbitControls, Center } from "@react-three/drei";
import * as THREE from "three";

const HUMAN_URL = "/models/human/scene.gltf";
const FEMALE_URL = "/models/femalebody/femalebody.gltf";

if (typeof window !== "undefined") {
  useGLTF.preload(HUMAN_URL);
  useGLTF.preload(FEMALE_URL);
}

const WARM_TINT = new THREE.Color(0.92, 0.68, 0.42);

function ensureClonedMaterials(mesh) {
  if (!mesh.material) return;
  const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  const cloned = mats.map((m) => {
    if (m.userData.agedClone) return m;
    const clone = m.clone();
    const base = clone.color ? clone.color.clone() : new THREE.Color(1, 1, 1);
    clone.userData.baseColor = base;
    if (clone.emissive) clone.userData.baseEmissive = clone.emissive.clone();
    clone.userData.agedClone = true;
    return clone;
  });
  mesh.material = cloned.length === 1 ? cloned[0] : cloned;
}

function applyAgeingTint(mesh, amount) {
  if (!mesh || !mesh.material) return;
  const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  const amt = Math.min(1, Math.max(0, amount));
  mats.forEach((mat) => {
    if (!mat.color || !mat.userData.baseColor) return;
    mat.color.lerpColors(mat.userData.baseColor, WARM_TINT, amt);
    if (mat.emissive && mat.userData.baseEmissive) {
      mat.emissive.lerpColors(mat.userData.baseEmissive, new THREE.Color(0.15, 0.08, 0.02), amt);
    }
  });
}

function useClonedSceneWithTint(scene, ageingLevel) {
  const clonedScene = useMemo(() => {
    const c = scene.clone();
    c.traverse((child) => { if (child.isMesh) ensureClonedMaterials(child); });
    return c;
  }, [scene]);
  useEffect(() => {
    if (!clonedScene) return;
    clonedScene.traverse((child) => { if (child.isMesh) applyAgeingTint(child, ageingLevel); });
  }, [clonedScene, ageingLevel]);
  return clonedScene;
}

function HumanBodyMesh({ ageingLevel = 0 }) {
  const group = useRef(null);
  const { scene } = useGLTF(HUMAN_URL);
  const clonedScene = useClonedSceneWithTint(scene, ageingLevel);
  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.2;
  });
  return (
    <Center>
      <group ref={group} scale={0.88}>
        <primitive object={clonedScene} />
      </group>
    </Center>
  );
}

function FemaleBodyMesh({ ageingLevel = 0 }) {
  const group = useRef(null);
  const { scene } = useGLTF(FEMALE_URL);
  const clonedScene = useClonedSceneWithTint(scene, ageingLevel);
  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.2;
  });
  return (
    <Center>
      <group ref={group} scale={0.88}>
        <primitive object={clonedScene} />
      </group>
    </Center>
  );
}

export default function BodyModelScene({ gender, ageingLevel = 0 }) {
  const isFemale = (gender || "").toLowerCase() === "female";
  return (
    <>
      <ambientLight intensity={0.55} />
      <directionalLight position={[6, 6, 6]} intensity={1.5} />
      <directionalLight position={[-4, 4, -4]} intensity={0.6} />
      <directionalLight position={[0, 8, 2]} intensity={0.4} />
      {isFemale ? <FemaleBodyMesh ageingLevel={ageingLevel} /> : <HumanBodyMesh ageingLevel={ageingLevel} />}
      <OrbitControls enableZoom minDistance={5} maxDistance={18} />
    </>
  );
}
