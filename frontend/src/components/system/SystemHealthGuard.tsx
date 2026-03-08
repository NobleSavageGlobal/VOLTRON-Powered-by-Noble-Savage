"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { healthApi } from "@/lib/api";

type HealthStatus = "online" | "degraded" | "offline";

export function SystemHealthGuard() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<HealthStatus>("online");
  const [freezeRecoveredAt, setFreezeRecoveredAt] = useState<number | null>(
    null,
  );
  const wasUnhealthyRef = useRef(false);

  useEffect(() => {
    let isDisposed = false;

    const ping = async () => {
      try {
        await healthApi.ping();
        if (isDisposed) return;
        setStatus("online");
        if (wasUnhealthyRef.current) {
          wasUnhealthyRef.current = false;
          queryClient.invalidateQueries();
        }
      } catch {
        if (isDisposed) return;
        const nextStatus: HealthStatus =
          typeof navigator !== "undefined" && navigator.onLine
            ? "degraded"
            : "offline";
        setStatus(nextStatus);
        wasUnhealthyRef.current = true;
      }
    };

    const onOnline = () => {
      setStatus("degraded");
      void ping();
    };

    const onOffline = () => {
      setStatus("offline");
      wasUnhealthyRef.current = true;
    };

    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);

    void ping();
    const interval = window.setInterval(() => {
      void ping();
    }, 20000);

    return () => {
      isDisposed = true;
      window.clearInterval(interval);
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, [queryClient]);

  useEffect(() => {
    const intervalMs = 2000;
    let expected = Date.now() + intervalMs;

    const interval = window.setInterval(() => {
      const now = Date.now();
      const drift = now - expected;
      expected = now + intervalMs;

      if (document.visibilityState !== "visible") {
        return;
      }

      // A large drift indicates event loop blocking or tab freeze; refetch stale data when app resumes.
      if (drift > 7000) {
        setFreezeRecoveredAt(now);
        queryClient.invalidateQueries();
      }
    }, intervalMs);

    return () => {
      window.clearInterval(interval);
    };
  }, [queryClient]);

  useEffect(() => {
    if (!freezeRecoveredAt) return;
    const timeout = window.setTimeout(() => {
      setFreezeRecoveredAt(null);
    }, 15000);
    return () => {
      window.clearTimeout(timeout);
    };
  }, [freezeRecoveredAt]);

  if (status === "online" && !freezeRecoveredAt) {
    return null;
  }

  const message =
    status === "offline"
      ? "You are offline. The app will self-recover and sync when connection returns."
      : status === "degraded"
        ? "Connection is unstable. Retrying requests automatically."
        : "Recovered from a temporary freeze. Data is refreshing now.";

  const toneClass =
    status === "offline"
      ? "bg-red-950/85 border-red-700 text-red-100"
      : status === "degraded"
        ? "bg-amber-950/85 border-amber-700 text-amber-100"
        : "bg-emerald-950/85 border-emerald-700 text-emerald-100";

  return (
    <div
      className={`fixed top-0 inset-x-0 z-[70] border-b ${toneClass}`}
      role="status"
      aria-live="polite"
    >
      <div className="mx-auto max-w-6xl px-4 py-2 text-xs sm:text-sm">
        {message}
      </div>
    </div>
  );
}
