import { useCallback, useEffect, useRef, useState } from "react";
import { analyzeRoutes } from "../api/tripApi";

/** status: "idle" | "loading" | "success" | "error" */
export function useTripAnalysis() {
  const [state, setState] = useState({
    status: "idle",
    data: null,
    error: null,
  });
  const controllerRef = useRef(null);

  const analyze = useCallback(async (payload) => {
    controllerRef.current?.abort(); // a newer submit supersedes an in-flight one
    const controller = new AbortController();
    controllerRef.current = controller;

    setState({ status: "loading", data: null, error: null });
    try {
      const data = await analyzeRoutes(payload, { signal: controller.signal });
      setState({ status: "success", data, error: null });
    } catch (error) {
      if (error.name === "AbortError") return;
      setState({ status: "error", data: null, error });
    }
  }, []);

  useEffect(() => () => controllerRef.current?.abort(), []);

  return { ...state, analyze };
}
