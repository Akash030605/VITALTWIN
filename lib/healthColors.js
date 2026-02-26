/**
 * Maps organ health status to display colors (healthcare theme).
 */
export const HEALTH_STATUS = {
  healthy: "healthy",
  atRisk: "at-risk",
  critical: "critical",
};

export const HEALTH_COLORS = {
  [HEALTH_STATUS.healthy]: "#10b981",
  [HEALTH_STATUS.atRisk]: "#f59e0b",
  [HEALTH_STATUS.critical]: "#ef4444",
};

export function getHealthColor(status) {
  return HEALTH_COLORS[status] ?? HEALTH_COLORS[HEALTH_STATUS.healthy];
}

export function getHealthColorHex(status) {
  return getHealthColor(status);
}
