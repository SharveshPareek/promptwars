/** Hook for SSE-based analysis with progressive status. */

import { useState, useCallback } from 'react';
import type { AnalysisResponse } from '../types';
import { analyzeStream } from '../services/api';

interface UseAnalyzeReturn {
  result: AnalysisResponse | null;
  loading: boolean;
  stage: string;
  stageMessage: string;
  error: string | null;
  analyze: (text: string, files: File[]) => Promise<void>;
  reset: () => void;
}

export function useAnalyze(): UseAnalyzeReturn {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState('');
  const [stageMessage, setStageMessage] = useState('');
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (text: string, files: File[]) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setStage('analyzing');
    setStageMessage('Connecting to Gemini AI...');

    try {
      await analyzeStream(text, files, {
        onStatus: (s, msg) => {
          setStage(s);
          setStageMessage(msg);
        },
        onIntake: () => {},
        onResult: (data) => {
          setResult(data);
          setLoading(false);
          setStage('done');
        },
        onError: (msg) => {
          setError(msg);
          setLoading(false);
        },
      });
      setLoading(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed.');
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setLoading(false);
    setStage('');
    setStageMessage('');
  }, []);

  return { result, loading, stage, stageMessage, error, analyze, reset };
}
