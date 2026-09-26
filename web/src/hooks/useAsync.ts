/**
 * `useAsync` — one loading / error / data state machine for every panel.
 *
 * Day 5 requires every page to handle Loading / Error / Empty; without this the
 * alternative is repeating three booleans per component. Aborts are ignored so a
 * fast role switch cannot leave a stale response behind.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { asFailure } from "../services/api";
import type { ApiFailure } from "../types";

export interface AsyncState<T> {
  data: T | null;
  error: ApiFailure | null;
  loading: boolean;
  /** True while refreshing but previous data is still shown. */
  refreshing: boolean;
  reload: () => void;
  setData: (value: T) => void;
}

export function useAsync<T>(
  loader: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[],
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiFailure | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  const mounted = useRef(true);
  const haveData = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    let active = true;
    loader(controller.signal)
      .then((value) => {
        if (!active) return;
        haveData.current = true;
        setData(value);
        setError(null);
      })
      .catch((reason: unknown) => {
        if (!active || (reason as Error).name === "AbortError") return;
        setError(asFailure(reason));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((value) => value + 1), []);

  return {
    data,
    error,
    loading,
    refreshing: loading && haveData.current,
    reload,
    setData: (value: T) => {
      haveData.current = true;
      setData(value);
    },
  };
}

/** Auto-refresh helper: re-runs `reload` on an interval while the tab is visible. */
export function useAutoRefresh(reload: () => void, intervalMs: number, enabled = true): void {
  useEffect(() => {
    if (!enabled || intervalMs <= 0) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") reload();
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [reload, intervalMs, enabled]);
}
