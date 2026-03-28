/** Hook for managing analysis state and API calls. */

import { useState, useCallback } from 'react';
import type { AnalysisResponse } from '../types';
import { analyzeInput } from '../services/api';

interface UseAnalyzeReturn {
  result: AnalysisResponse | null;
  loading: boolean;
  error: string | null;
  analyze: (text: string, files: File[]) => Promise<void>;
  reset: () => void;
}

export function useAnalyze(): UseAnalyzeReturn {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (text: string, files: File[]) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await analyzeInput(text, files);
      setResult(response);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Analysis failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setLoading(false);
  }, []);

  return { result, loading, error, analyze, reset };
}
