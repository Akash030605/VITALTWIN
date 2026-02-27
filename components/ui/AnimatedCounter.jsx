"use client";

import { useEffect, useState } from "react";

export default function AnimatedCounter({ value, duration = 1200, suffix = "", decimals = 0 }) {
  const [display, setDisplay] = useState(0);
  const num = Number(value);
  const isNum = !Number.isNaN(num);

  useEffect(() => {
    if (!isNum) return;
    let start = 0;
    const startTime = performance.now();
    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - (1 - progress) * (1 - progress);
      const current = Math.round(start + (num - start) * eased);
      setDisplay(current);
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [num, duration, isNum]);

  if (!isNum) return <>{value}{suffix}</>;
  const formatted = decimals > 0 ? display.toFixed(decimals) : display;
  return <>{formatted}{suffix}</>;
}
