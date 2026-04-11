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
const AGED_EMISSIVE = new THREE.Color(0.22, 0.10, 0.02);
const ZERO_COLOR = new THREE.Color(0, 0, 0);

function ensureClonedMaterials(mesh) {
  if (!mesh.material) return;
  const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  const cloned = mats.map((m) => {
    if (m.userData.agedClone) return m;
    const clone = m.clone();
    const base = clone.color ? clone.color.clone() : new THREE.Color(1, 1, 1);
    clone.userData.baseColor = base;
    clone.userData.baseEmissive = clone.emissive ? clone.emissive.clone() : ZERO_COLOR.clone();
    clone.userData.baseEmissiveIntensity = clone.emissiveIntensity ?? 0;
    clone.userData.baseRoughness = clone.roughness ?? 0.5;
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
    if (!mat.userData.baseColor) return;

    // Color: lerp to warm amber-brown tint
    if (mat.color) mat.color.lerpColors(mat.userData.baseColor, WARM_TINT, amt * 0.7);

    // Emissive: lerp from base emissive → aged sickly orange
    if (mat.emissive) {
      mat.emissive.lerpColors(mat.userData.baseEmissive, AGED_EMISSIVE, amt);
      mat.emissiveIntensity = mat.userData.baseEmissiveIntensity + amt * 0.45;
    }

    // Roughness: increases at high aging — dried/worn skin effect
    if (mat.roughness !== undefined && mat.userData.baseRoughness !== undefined) {
      mat.roughness = mat.userData.baseRoughness + amt * 0.35;
    }

    // Metalness: slightly reduce at high aging
    if (mat.metalness !== undefined) {
      mat.metalness = Math.max(0, (mat.metalness ?? 0) - amt * 0.15);
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
  const ageLightRef = useRef(null);
  const { scene } = useGLTF(HUMAN_URL);
  const clonedScene = useClonedSceneWithTint(scene, ageingLevel);

  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.2;
    if (ageLightRef.current) {
      // Reactive aging light: warm amber rises with aging, pulses subtly
      const pulse = Math.sin(Date.now() * 0.002) * 0.08 + 0.92;
      ageLightRef.current.intensity = ageingLevel * 1.8 * pulse;
      ageLightRef.current.color.setRGB(
        0.9 + ageingLevel * 0.1,
        0.45 - ageingLevel * 0.2,
        0.05
      );
    }
  });

  return (
    <Center>
      <group ref={group} scale={0.88}>
        <primitive object={clonedScene} />
        {/* Aging point light: amber glow from below, intensifies with age */}
        <pointLight ref={ageLightRef} position={[0, -1.5, 1.2]} intensity={0} distance={8} decay={2} />
      </group>
    </Center>
  );
}

function FemaleBodyMesh({ ageingLevel = 0 }) {
  const group = useRef(null);
  const ageLightRef = useRef(null);
  const { scene } = useGLTF(FEMALE_URL);
  const clonedScene = useClonedSceneWithTint(scene, ageingLevel);

  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.2;
    if (ageLightRef.current) {
      const pulse = Math.sin(Date.now() * 0.002) * 0.08 + 0.92;
      ageLightRef.current.intensity = ageingLevel * 1.8 * pulse;
      ageLightRef.current.color.setRGB(
        0.9 + ageingLevel * 0.1,
        0.45 - ageingLevel * 0.2,
        0.05
      );
    }
  });

  return (
    <Center>
      <group ref={group} scale={0.88}>
        <primitive object={clonedScene} />
        <pointLight ref={ageLightRef} position={[0, -1.5, 1.2]} intensity={0} distance={8} decay={2} />
      </group>
    </Center>
  );
}

export default function BodyModelScene({ gender, ageingLevel = 0 }) {
  const isFemale = (gender || "").toLowerCase() === "female";
  // Ambient dims slightly at high aging for dramatic effect
  const ambientIntensity = 0.55 - ageingLevel * 0.15;
  return (
    <>
      <ambientLight intensity={ambientIntensity} />
      <directionalLight position={[6, 6, 6]} intensity={1.5} />
      <directionalLight position={[-4, 4, -4]} intensity={0.6} />
      <directionalLight position={[0, 8, 2]} intensity={0.4} />
      {isFemale ? <FemaleBodyMesh ageingLevel={ageingLevel} /> : <HumanBodyMesh ageingLevel={ageingLevel} />}
      <OrbitControls enableZoom={false} />
    </>
  );
}
