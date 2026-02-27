import { create } from "zustand";

const STORAGE_KEY = "vitaltwin_report";

function loadResult() {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveResult(result) {
  if (typeof window === "undefined") return;
  try {
    if (result == null) localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
  } catch {}
}

const ORGAN_IDS = ["heart", "liver", "lungs", "brain", "kidneys"];
const ORGAN_NAMES = {
  heart: "Heart",
  liver: "Liver",
  lungs: "Lungs",
  brain: "Brain",
  kidneys: "Kidneys",
};

export const DEFAULT_ORGANS = ORGAN_IDS.map((id) => ({
  id,
  name: ORGAN_NAMES[id],
  status: "healthy",
  summary: "Baseline — submit your data above for a personalized assessment and predictions.",
  prediction5y: null,
  prediction10y: null,
}));

const INITIAL_INPUT = {
  smoking: "",
  alcohol: "",
  sleep: "",
  stress: "",
  medical_conditions: [],
};

const INITIAL_PROFILE = {
  name: "",
  age: "",
  gender: "",
  height: "",
  weight: "",
  diet: "",
  activity: "",
};

function riskLevelToStatus(riskLevel) {
  if (!riskLevel) return "healthy";
  if (riskLevel === "RED") return "critical";
  if (riskLevel === "YELLOW") return "at-risk";
  return "healthy";
}

export const useStore = create((set, get) => ({
  profile: { ...INITIAL_PROFILE },
  setProfile: (key, value) =>
    set((state) => ({ profile: { ...state.profile, [key]: value } })),
  resetProfile: () => set({ profile: { ...INITIAL_PROFILE } }),

  input: { ...INITIAL_INPUT },
  setInput: (key, value) =>
    set((state) => ({ input: { ...state.input, [key]: value } })),
  resetInput: () => set({ input: { ...INITIAL_INPUT } }),

  result: loadResult(),
  setResult: (result) => {
    saveResult(result);
    set({ result });
  },

  isSubmitting: false,
  setSubmitting: (v) => set({ isSubmitting: v }),

  clearResult: () => {
    saveResult(null);
    set({ result: null });
  },

  /** Clear report + reset all form inputs. */
  clearAll: () => {
    saveResult(null);
    set({
      result: null,
      profile: { ...INITIAL_PROFILE },
      input: { ...INITIAL_INPUT },
    });
  },

  getOrganStatus: (organId) => {
    const state = get();
    const organs = state.result?.organs;
    if (!organs) return "healthy";
    const organ = organs[organId] ?? organs[organId === "kidneys" ? "kidney" : organId];
    return riskLevelToStatus(organ?.risk_level) ?? "healthy";
  },
}));

export { ORGAN_IDS };
