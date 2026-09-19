/**
 * Tracks browser connectivity via `navigator.onLine` and the online/offline
 * events. Used to drive the offline indicator and stale-data labeling — the app
 * never presents cached data as live.
 */

import { useSyncExternalStore } from "react";

function subscribe(callback: () => void): () => void {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

function getSnapshot(): boolean {
  // Default to online where the API is unavailable (SSR/tests).
  return typeof navigator === "undefined" ? true : navigator.onLine;
}

export function useOnlineStatus(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, () => true);
}
