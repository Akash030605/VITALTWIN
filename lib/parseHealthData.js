/**
 * Parse Apple Health XML export or Google Fit JSON export into normalized form fields.
 * Returns: { height?, weight?, sleep?, steps?, heartRate? }
 * All values are normalized to: height in cm, weight in kg, sleep in hours.
 */

/** Apple Health XML — exported as export.xml from Health app */
export function parseAppleHealthXML(xmlString) {
  if (typeof window === "undefined") return {};
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlString, "text/xml");
    const records = Array.from(doc.querySelectorAll("Record"));

    const getLatest = (type) => {
      const matching = records
        .filter((r) => r.getAttribute("type") === type)
        .map((r) => ({
          value: parseFloat(r.getAttribute("value")),
          unit: r.getAttribute("unit"),
          date: r.getAttribute("startDate") || r.getAttribute("creationDate"),
        }))
        .filter((r) => !isNaN(r.value))
        .sort((a, b) => new Date(b.date) - new Date(a.date));
      return matching[0] ?? null;
    };

    const result = {};

    // Height
    const heightRecord = getLatest("HKQuantityTypeIdentifierHeight");
    if (heightRecord) {
      // unit is usually "cm" or "in"
      result.height = heightRecord.unit === "in"
        ? Math.round(heightRecord.value * 2.54)
        : Math.round(heightRecord.value);
    }

    // Weight
    const weightRecord = getLatest("HKQuantityTypeIdentifierBodyMass");
    if (weightRecord) {
      // unit is usually "kg" or "lb"
      result.weight = weightRecord.unit === "lb"
        ? Math.round(weightRecord.value * 0.4536 * 10) / 10
        : Math.round(weightRecord.value * 10) / 10;
    }

    // Sleep — sum inBed/asleep durations for last 30 days, then average
    const sleepRecords = records.filter(
      (r) =>
        r.getAttribute("type") === "HKCategoryTypeIdentifierSleepAnalysis" &&
        (r.getAttribute("value") === "HKCategoryValueSleepAnalysisAsleep" ||
          r.getAttribute("value") === "HKCategoryValueSleepAnalysisInBed")
    );
    if (sleepRecords.length > 0) {
      const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
      const recentSleep = sleepRecords.filter(
        (r) => new Date(r.getAttribute("startDate")).getTime() > thirtyDaysAgo
      );
      if (recentSleep.length > 0) {
        // Group by day and sum durations
        const byDay = {};
        recentSleep.forEach((r) => {
          const start = new Date(r.getAttribute("startDate"));
          const end = new Date(r.getAttribute("endDate"));
          const dayKey = start.toISOString().slice(0, 10);
          const hours = (end - start) / (1000 * 60 * 60);
          if (hours > 0 && hours < 16) {
            byDay[dayKey] = (byDay[dayKey] || 0) + hours;
          }
        });
        const days = Object.values(byDay);
        if (days.length > 0) {
          const avgSleep = days.reduce((a, b) => a + b, 0) / days.length;
          result.sleep = Math.round(avgSleep).toString();
        }
      }
    }

    // Heart rate (informational)
    const hrRecord = getLatest("HKQuantityTypeIdentifierHeartRate");
    if (hrRecord) result.heartRate = Math.round(hrRecord.value);

    // Step count
    const stepsRecord = getLatest("HKQuantityTypeIdentifierStepCount");
    if (stepsRecord) result.steps = Math.round(stepsRecord.value);

    return result;
  } catch {
    return {};
  }
}

/** Google Fit JSON — typical merged_fitness_data.json or daily_activity_metrics.json */
export function parseGoogleFitJSON(json) {
  try {
    const data = typeof json === "string" ? JSON.parse(json) : json;
    const result = {};

    // Common aggregate format: { bucket: [{ dataset: [{ point: [{ value: [{fpVal/intVal}] }] }] }] }
    const extractValue = (point) => {
      const val = point?.value?.[0];
      return val?.fpVal ?? val?.intVal ?? null;
    };

    // Height
    const heightData = data?.height || data?.Body?.height;
    if (heightData) {
      const val = typeof heightData === "number" ? heightData : extractValue(heightData?.bucket?.[0]?.dataset?.[0]?.point?.[0]);
      if (val) result.height = Math.round(val < 3 ? val * 100 : val); // handle meters vs cm
    }

    // Weight
    const weightData = data?.weight || data?.Body?.weight;
    if (weightData) {
      const val = typeof weightData === "number" ? weightData : extractValue(weightData?.bucket?.[0]?.dataset?.[0]?.point?.[0]);
      if (val) result.weight = Math.round(val * 10) / 10;
    }

    // Sleep — Google Fit sleep sessions
    const sleepSessions = data?.sleep || data?.Sleep;
    if (Array.isArray(sleepSessions) && sleepSessions.length > 0) {
      const recentSessions = sleepSessions.slice(-30);
      const avgMs = recentSessions.reduce((sum, s) => {
        const ms = (s.endTimeMillis || s.end_time_ms || 0) - (s.startTimeMillis || s.start_time_ms || 0);
        return sum + ms;
      }, 0) / recentSessions.length;
      const avgHours = avgMs / (1000 * 60 * 60);
      if (avgHours > 0) result.sleep = Math.round(avgHours).toString();
    }

    // Steps
    const stepsData = data?.steps || data?.Activity?.steps;
    if (stepsData != null) {
      const val = typeof stepsData === "number" ? stepsData : extractValue(stepsData?.bucket?.[0]?.dataset?.[0]?.point?.[0]);
      if (val) result.steps = Math.round(val);
    }

    return result;
  } catch {
    return {};
  }
}

/**
 * Normalize imported data to store field names.
 * Returns { profileFields: {height?, weight?}, inputFields: {sleep?} }
 */
export function normalizeImportedData(raw) {
  const profileFields = {};
  const inputFields = {};

  if (raw.height) profileFields.height = String(raw.height);
  if (raw.weight) profileFields.weight = String(raw.weight);
  if (raw.sleep) inputFields.sleep = raw.sleep;

  return { profileFields, inputFields, meta: { heartRate: raw.heartRate, steps: raw.steps } };
}
