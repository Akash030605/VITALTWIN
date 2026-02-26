/**
 * API client for digital twin. Mock implementation; swap for Spring Boot later.
 */

export const MOCK_RESULT = {
  organs: [
    {
      id: "heart",
      name: "Heart",
      status: "healthy",
      summary: "Cardiovascular metrics are within normal range. Blood pressure and resting heart rate suggest good cardiac efficiency.",
      prediction5y: "With current habits, heart health is projected to remain stable. Continued exercise supports this outlook.",
      prediction10y: "Long-term risk remains low if diet and activity levels are maintained. Consider periodic lipid panels.",
    },
    {
      id: "liver",
      name: "Liver",
      status: "at-risk",
      summary: "Liver enzymes show mild elevation. Current alcohol intake and diet may be contributing to hepatic load.",
      prediction5y: "Reducing alcohol and processed foods can improve enzyme levels. Without changes, risk of fatty liver may increase.",
      prediction10y: "Lifestyle changes now can prevent progression to significant liver disease. Monitoring recommended.",
    },
    {
      id: "lungs",
      name: "Lungs",
      status: "healthy",
      summary: "Respiratory function is good. No signs of obstruction or significant inflammation. Oxygen uptake is efficient.",
      prediction5y: "Lung capacity is expected to stay strong with no smoking and minimal pollution exposure.",
      prediction10y: "Age-related decline may be modest if you maintain activity and avoid respiratory irritants.",
    },
    {
      id: "brain",
      name: "Brain",
      status: "critical",
      summary: "Cognitive markers and sleep patterns suggest elevated stress on brain health. Sleep quality and mental load are key factors.",
      prediction5y: "Without intervention, cognitive reserve may decline. Sleep hygiene and stress management are priorities.",
      prediction10y: "Addressing sleep and stress now can significantly improve long-term cognitive trajectory and dementia risk.",
    },
    {
      id: "kidneys",
      name: "Kidneys",
      status: "healthy",
      summary: "Kidney function is within normal range. Hydration and blood pressure are supportive of renal health.",
      prediction5y: "Kidney function is likely to remain stable with current habits and adequate hydration.",
      prediction10y: "Continued blood pressure control and avoiding nephrotoxic substances support long-term kidney health.",
    },
  ],
  timeline: [
    { year: 0, label: "Today", summary: "Baseline assessment — all vitals logged." },
    { year: 1, label: "1 year", summary: "First follow-up: track liver enzymes and sleep quality." },
    { year: 3, label: "3 years", summary: "Mid-term check: cardiovascular and cognitive markers." },
    { year: 5, label: "5 years", summary: "Projected with current habits — liver and brain need attention." },
    { year: 10, label: "10 years", summary: "Long-term outlook — lifestyle changes now improve trajectory." },
  ],
  recommendations: [
    "Reduce alcohol intake to lower liver strain.",
    "Consider cognitive exercises and sleep hygiene for brain health.",
    "Maintain current exercise and diet for heart and lungs.",
    "Schedule annual blood work to monitor liver and kidney function.",
    "Aim for 7–8 hours of sleep to support cognitive reserve.",
  ],
};

export async function submitInput(inputData) {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 800));
  return { ok: true, data: MOCK_RESULT };
}

export async function getResults() {
  await new Promise((r) => setTimeout(r, 300));
  return { ok: true, data: MOCK_RESULT };
}
