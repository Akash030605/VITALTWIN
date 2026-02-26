# Models folder – study

## Current contents

| File            | Type  | Notes |
|-----------------|-------|--------|
| heart.gltf      | organ | 12k vertices, 1 mesh |
| liver.gltf      | organ | 65k vertices, multiple materials |
| lungs.gltf      | organ | uses KHR_materials_specular |
| kidney.gltf     | organ | 3 textures |
| brain.gltf      | organ | uses KHR_materials_pbrSpecularGlossiness |
| malebody.gltf   | body  | 36 MB scene.bin, no images |
| femalebody.gltf | body  | 10 MB scene.bin, no images |
| README.md       | doc   | this file |

Only the `.gltf` JSON files are present. No binary or image assets are in the repo.

---

## What each .gltf expects (relative to its own folder)

All paths below are relative to the folder containing the .gltf.

### heart.gltf
- **Buffers:** `heart.bin` (1,039,576 bytes)
- **Images:**  
  `textures/Heart_Tex_baseColor.png`  
  `textures/Heart_Tex_metallicRoughness.png`  
  `textures/Heart_Tex_normal.png`

### liver.gltf
- **Buffers:** `liver.bin` (3,254,928 bytes)
- **Images:**  
  `textures/Material.011_baseColor.png`, `Material.011_normal.png`  
  `textures/Material.012_*.png`, `Material.013_*.png`  
  `textures/Material_*.png`, `Material.015_*.png`  
  (multiple baseColor, metallicRoughness, normal)

### lungs.gltf
- **Buffers:** `lungs.bin` (2,908,744 bytes)
- **Images:**  
  `textures/thairoid01lungh_part01_baseColor.jpeg` (+ metallicRoughness, normal, specularf0)  
  `textures/thairoid01lungh_part02_*` (same set)

### kidney.gltf
- **Buffers:** `kidney.bin` (2,218,016 bytes)
- **Images:**  
  `textures/Kidney_Tex_baseColor.png`  
  `textures/Kidney_Tex_metallicRoughness.png`  
  `textures/Kidney_Tex_normal.png`

### brain.gltf
- **Buffers:** `brain.bin` (245,760 bytes)
- **Images:**  
  `textures/material_0_diffuse.png`  
  `textures/material_0_specularGlossiness.png`  
  `textures/material_0_normal.png`

### malebody.gltf
- **Buffers:** `malebody.bin` (36,041,448 bytes)
- **Images:** none (untextured or vertex colors only)

### femalebody.gltf
- **Buffers:** `femalebody.bin` (10,445,256 bytes)
- **Images:** none

---

## Why the app can’t load them yet

1. **No `.bin`** – Each .gltf points to an organ-named .bin in the same folder (e.g. `heart.bin`, `liver.bin`). If that file is missing, the loader gets 404.
2. **No `textures/`** – Organ models reference images under `textures/`. That folder does not exist.
3. **Single folder conflict** – If all seven .gltf files stay in one folder, they would all expect one `scene.bin`, but each model has a different `byteLength`. So each model must live in **its own folder** with its **own** `scene.bin` (and its own `textures/` if it has images).

---

## Required layout for loading

Put each model in its own subfolder and keep paths relative to that folder:

```
public/models/
  heart/
    heart.gltf
    scene.bin
    textures/
      Heart_Tex_baseColor.png
      Heart_Tex_metallicRoughness.png
      Heart_Tex_normal.png
  liver/
    liver.gltf
    scene.bin
    textures/
      (all Material.*.png listed above)
  lungs/
    lungs.gltf
    lungs.bin
    textures/
      (thairoid01lungh_part01_*, part02_*)
  kidney/
    kidney.gltf
    kidney.bin
    textures/
      Kidney_Tex_*.png
  brain/
    brain.gltf
    brain.bin
    textures/
      material_0_*.png
  malebody/
    malebody.gltf
    malebody.bin
  femalebody/
    femalebody.gltf
    femalebody.bin
```

The app loads organs from subfolders (e.g. `/models/heart/heart.gltf`). When you add these folders and files, the real models will load.

---

## Using your `texture-for-*` folders

Your texture folders (e.g. **texture-for-liver**, **texture-for-heart**) need to be used as the **`textures`** folder **next to** each model’s `.gltf`. The loader expects paths like `textures/Heart_Tex_baseColor.png` relative to the `.gltf` file.

**Do this for each organ:**

1. Create a subfolder: `public/models/heart/`, `public/models/liver/`, etc.
2. Put the `.gltf` and `scene.bin` for that organ in that folder (e.g. `public/models/liver/liver.gltf`, `public/models/liver/scene.bin`).
3. Put the **contents** of your texture folder inside a folder named **`textures`** next to the `.gltf`:
   - **texture-for-heart** → `public/models/heart/textures/` (files: `Heart_Tex_baseColor.png`, etc.)
   - **texture-for-liver** → `public/models/liver/textures/` (files: `Material.011_baseColor.png`, `Material_normal.png`, etc.)
   - **texture-for-lungs** → `public/models/lungs/textures/` (files: `thairoid01lungh_part01_baseColor.jpeg`, etc.)
   - **texture-for-kidney** → `public/models/kidney/textures/` (files: `Kidney_Tex_baseColor.png`, etc.)
   - **texture-for-brain** → `public/models/brain/textures/` (files: `material_0_diffuse.png`, etc.)

The **folder name** must be exactly **`textures`** (lowercase). The **file names** inside must match what the `.gltf` references (see the tables above). If your texture-for-liver files have different names, rename them to match (e.g. `Material.011_baseColor.png`).

**Resulting layout example:**

```
public/models/
  heart/
    heart.gltf
    heart.bin
    textures/          ← contents of texture-for-heart (rename folder to "textures")
      Heart_Tex_baseColor.png
      Heart_Tex_metallicRoughness.png
      Heart_Tex_normal.png
  liver/
    liver.gltf
    liver.bin
    textures/          ← contents of texture-for-liver
      Material.011_baseColor.png
      ...
```

Body models (malebody, femalebody) have no images in the .gltf; they only need `malebody.bin` / `femalebody.bin` next to the `.gltf`.
