/**
 * Dummy report response — same shape as API. Swap for real API later.
 */
export const DUMMY_REPORT = {
  user_id: "TEST123",
  simulation_date: "2026-02-26T19:41:26.804582Z",
  vital_score: {
    current: 59,
    category: "Fair",
    color: "YELLOW",
    message: "\u26a0\ufe0f Moderate health concerns to address",
    trend: "declining",
    trend_percent: -69.5,
    gauge: {
      value: 59,
      min: 0,
      max: 100,
      segments: [
        { from: 0, to: 49, color: "#F44336", label: "Critical" },
        { from: 50, to: 79, color: "#FFC107", label: "Fair" },
        { from: 80, to: 100, color: "#4CAF50", label: "Good" },
      ],
      current_segment: { color: "#FFC107", label: "Fair" },
      needle: { value: 59, color: "#333333" },
    },
    interpretation: "Several health markers need attention. Focus on lifestyle changes.",
  },
  biological_age: {
    real_age: 45,
    biological_age: 60,
    age_gap: 15,
    gap_level: "RED",
    message: "\ud83d\udd34 CRITICAL: Your body is aging 15 years faster! Immediate action needed",
    factors: [
      "High heart risk (+5)",
      "Moderate brain risk (+2)",
      "Moderate lungs risk (+2)",
      "Daily smoking (+4)",
      "Poor sleep (+2)",
    ],
  },
  body_stress: {
    overall_stress: 0.56,
    overall_level: "MEDIUM",
    systems: {
      cardiovascular: { stress: 0.8, level: "HIGH", color: "RED" },
      metabolic: { stress: 0.18, level: "LOW", color: "GREEN" },
      sleep_debt: { stress: 0.6, level: "MEDIUM", color: "YELLOW" },
      lifestyle: { stress: 0.7, level: "HIGH", color: "RED" },
    },
    heatmap_zones: [
      { organ: "heart", strain: 0.84, color: "RED", intensity: 0.9, glow: "true" },
      { organ: "brain", strain: 0.6, color: "YELLOW", intensity: 0.6, glow: "true" },
      { organ: "liver", strain: 0.18, color: "GREEN", intensity: 0.3, glow: "false" },
      { organ: "kidney", strain: 0.24, color: "GREEN", intensity: 0.3, glow: "false" },
      { organ: "lungs", strain: 0.42, color: "YELLOW", intensity: 0.6, glow: "false" },
    ],
    visual_overlay: { type: "gradient", opacity: 0.4, blend_mode: "multiply" },
  },
  future_self: {
    timeline: [
      { year: 0, label: "Today", status: "Current", vitality_score: 59, biological_age: 60, organ_status: { heart: "RED", brain: "YELLOW", liver: "GREEN", kidney: "GREEN", lungs: "YELLOW" }, changes: [], visual_cues: [] },
      { year: 1, label: "1 Year", status: "1 Year", vitality_score: 55, biological_age: 60, organ_status: { heart: "RED", brain: "YELLOW", liver: "GREEN", kidney: "GREEN", lungs: "YELLOW" }, changes: [], visual_cues: ["heart_pulsing"] },
      { year: 3, label: "3 Year", status: "3 Years", vitality_score: 47, biological_age: 62, organ_status: { heart: "RED", brain: "YELLOW", liver: "YELLOW", kidney: "YELLOW", lungs: "YELLOW" }, changes: ["Liver showing early warning signs", "Kidney showing early warning signs"], visual_cues: ["heart_pulsing", "brain_warning_glow", "liver_warning_glow"] },
      { year: 5, label: "5 Year", status: "5 Years", vitality_score: 40, biological_age: 62, organ_status: { heart: "RED", brain: "YELLOW", liver: "YELLOW", kidney: "YELLOW", lungs: "YELLOW" }, changes: ["Liver showing early warning signs", "Kidney showing early warning signs"], visual_cues: ["heart_pulsing", "brain_warning_glow", "liver_warning_glow"] },
      { year: 10, label: "10 Year", status: "10 Years", vitality_score: 18, biological_age: 65, organ_status: { heart: "RED", brain: "RED", liver: "RED", kidney: "YELLOW", lungs: "RED" }, changes: ["Brain at critical risk", "Liver at critical risk", "Kidney showing early warning signs"], visual_cues: ["heart_pulsing", "brain_pulsing", "liver_pulsing"] },
    ],
    overall_trajectory: "declining_rapidly",
  },
  organs: {
    heart: { current_risk: 0.84, risk_level: "RED", health_score: 16, metrics: { blood_pressure_risk: 0.3, cholesterol_risk: 0.1, age_risk: 0.3, lifestyle_risk: 0.5 }, risk_progression: { year_1: 0.89, year_3: 0.99, year_5: 1.0, year_10: 1.0 }, recommendations: ["IMMEDIATE: Consult cardiologist within 1 month", "Take prescribed medications regularly", "Monitor blood pressure daily", "Attend cardiac rehabilitation if recommended"] },
    brain: { current_risk: 0.37, risk_level: "YELLOW", health_score: 63, metrics: { stress_risk: 0.5, sleep_risk: 0.3, bp_risk: 0.3, age_risk: 0.3 }, risk_progression: { year_1: 0.4, year_3: 0.47, year_5: 0.54, year_10: 0.7 }, recommendations: ["Practice mindfulness 10 min daily for stress reduction", "Ensure 7-8 hours of quality sleep", "Include omega-3 rich foods in diet", "Engage in mentally stimulating activities"] },
    liver: { current_risk: 0.17, risk_level: "GREEN", health_score: 83, metrics: { bmi_risk: 0.4, alcohol_risk: 0.3, diet_risk: 0.15, metabolic_risk: 0.1 }, risk_progression: { year_1: 0.24, year_3: 0.37, year_5: 0.51, year_10: 0.84 }, recommendations: ["Maintain healthy BMI", "Limit alcohol to occasional", "Eat balanced diet with limited processed foods", "Stay hydrated"] },
    kidney: { current_risk: 0.24, risk_level: "GREEN", health_score: 76, metrics: { bp_risk: 0.4, diabetes_risk: 0.1, diet_risk: 0.15, age_risk: 0.3 }, risk_progression: { year_1: 0.28, year_3: 0.37, year_5: 0.45, year_10: 0.66 }, recommendations: ["Drink 2-3 liters water daily", "Reduce salt and processed foods", "Monitor blood pressure regularly", "Avoid NSAIDs when possible"] },
    lungs: { current_risk: 0.42, risk_level: "YELLOW", health_score: 58, metrics: { smoking_risk: 0.7, exercise_risk: 0.3, condition_risk: 0.1, age_risk: 0.3 }, risk_progression: { year_1: 0.45, year_3: 0.52, year_5: 0.59, year_10: 0.75 }, recommendations: ["Cardio exercise 3x weekly to improve lung capacity", "Avoid exposure to pollutants and smoke", "Practice deep breathing exercises", "Get flu vaccine annually"] },
  },
  overall_health_score: 59,
  priority_recommendations: [
    { priority: "CRITICAL", category: "biological_age", action: "Immediate lifestyle intervention needed", impact: "Could reduce biological age by 5-7 years" },
    { priority: "HIGH", category: "heart", action: "IMMEDIATE: Consult cardiologist within 1 month", impact: "Critical - address within 1 month" },
    { priority: "MEDIUM", category: "brain", action: "Practice mindfulness 10 min daily for stress reduction", impact: "Moderate - address within 3 months" },
    { priority: "MEDIUM", category: "lungs", action: "Cardio exercise 3x weekly to improve lung capacity", impact: "Moderate - address within 3 months" },
  ],
  what_if_simulations: {
    current: { id: "current", name: "Current Lifestyle", description: "Your current habits", biological_age: 60, health_score: 59, risk_level: "RED", is_current: "true" },
    scenarios: [
      { id: "all_changes", name: "Complete Transformation", description: "All healthy changes combined", biological_age: 45, health_score: 70, risk_level: "RED", improvements: { biological_age_reduction: 15, health_score_increase: 11, years_gained: 15 }, changes: ["Smoking: Never", "Sleep: 8", "Stress: Low", "Alcohol: Never", "ActivityLevel: Active", "Diet: Good"], impact: "transformative", is_current: "false" },
      { id: "quit_smoking", name: "Quit Smoking", description: "Stop smoking completely", biological_age: 55, health_score: 65, risk_level: "RED", improvements: { biological_age_reduction: 5, health_score_increase: 6, years_gained: 5 }, changes: ["Smoking: Never"], impact: "high", is_current: "false" },
      { id: "reduce_stress", name: "Reduce Stress", description: "Practice stress management", biological_age: 57, health_score: 62, risk_level: "RED", improvements: { biological_age_reduction: 3, health_score_increase: 3, years_gained: 3 }, changes: ["Stress: Low"], impact: "medium", is_current: "false" },
    ],
    best_case: { id: "all_changes", name: "Complete Transformation", description: "All healthy changes combined", biological_age: 45, health_score: 70, risk_level: "RED", improvements: { biological_age_reduction: 15, health_score_increase: 11, years_gained: 15 }, changes: ["Smoking: Never", "Sleep: 8", "Stress: Low", "Alcohol: Never", "ActivityLevel: Active", "Diet: Good"], impact: "transformative", is_current: "false" },
    quick_wins: [{ name: "Quit Smoking", gain: 6 }],
  },
};
