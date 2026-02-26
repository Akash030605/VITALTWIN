import { create } from "zustand";
import { MOCK_RESULT } from "../lib/api";

const ORGAN_IDS = ["heart", "liver", "lungs", "brain", "kidneys"];

const ORGAN_NAMES = {
  heart: "Heart",
  liver: "Liver",
  lungs: "Lungs",
  brain: "Brain",
  kidneys: "Kidneys",
};

/** Default organ list shown from the start — all 100% healthy until user submits. */
export const DEFAULT_ORGANS = ORGAN_IDS.map((id) => ({
  id,
  name: ORGAN_NAMES[id],
  status: "healthy",
  summary: "Baseline — submit your data above for a personalized assessment and predictions.",
  prediction5y: null,
  prediction10y: null,
}));

/** Dummy form data so the app is pre-filled for demo. */
export const DUMMY_INPUT = {
  age: "32",
  weight: "72",
  height: "178",
  smoking: "Never",
  alcohol: "Moderate",
  exercise: "Active",
  diet: "Balanced",
};

export const useStore = create((set) => ({
  // Profile (starter page): name, height, weight, diet, etc.
  profile: {},
  setProfile: (key, value) =>
    set((state) => ({ profile: { ...state.profile, [key]: value } })),

  // User input (health questions / legacy)
  input: { ...DUMMY_INPUT },
  setInput: (key, value) =>
    set((state) => ({ input: { ...state.input, [key]: value } })),

  // Result — pre-filled with mock data for dashboard/organ health
  result: MOCK_RESULT,
  setResult: (result) => set({ result }),

  // UI state
  isSubmitting: false,
  setSubmitting: (v) => set({ isSubmitting: v }),

  clearResult: () => set({ result: null }),

  getOrganStatus: (organId) => {
    const state = useStore.getState();
    const organ = state.result?.organs?.find((o) => o.id === organId);
    return organ?.status ?? "healthy";
  },
}));

export { ORGAN_IDS };
