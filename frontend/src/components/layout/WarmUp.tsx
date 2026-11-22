"use client";

import { useEffect } from "react";

/**
 * Nudges the API awake as soon as someone lands on a page that doesn't need it.
 *
 * The free Render instance sleeps when idle and takes 30-60s to wake. The
 * landing and auth pages render without the API, so firing a health check
 * from here means the wake-up happens while the visitor is still reading,
 * not after they click "Browse". Once per tab is plenty.
 */
export function WarmUp() {
  useEffect(() => {
    try {
      if (sessionStorage.getItem("zenkai:warm")) return;
      sessionStorage.setItem("zenkai:warm", "1");
    } catch {
      // storage blocked - pinging again is harmless
    }
    fetch("/api/health", { cache: "no-store" }).catch(() => {});
  }, []);

  return null;
}
