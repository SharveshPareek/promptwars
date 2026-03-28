/** Hook for SSE-based progressive analysis. */

import { useState, useCallback } from 'react';
import type { AnalysisResponse, IntakeResult } from '../types';
import { analyzeStream } from '../services/api';

interface UseAnalyzeReturn {
  result: AnalysisResponse | null;
  intake: IntakeResult | null;
  loading: boolean;
  stage: string;
  stageMessage: string;
  error: string | null;
  analyze: (text: string, files: File[]) => Promise<void>;
  reset: () => void;
}

export function useAnalyze(): UseAnalyzeReturn {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [intake, setIntake] = useState<IntakeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState('');
  const [stageMessage, setStageMessage] = useState('');
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (text: string, files: File[]) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setIntake(null);
    setStage('starting');
    setStageMessage('Connecting...');

    try {
      await analyzeStream(text, files, {
        onStatus: (s, msg) => {
          setStage(s);
          setStageMessage(msg);
        },
        onIntake: (data) => {
          setIntake(data);
          setStage('reasoning');
        },
        onResult: (data) => {
          setResult(data);
          setIntake(data.intake);
          setLoading(false);
          setStage('done');
        },
        onError: (msg) => {
          setError(msg);
          setLoading(false);
        },
      });
      // If stream ended without result or error
      setLoading(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed.');
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setIntake(null);
    setError(null);
    setLoading(false);
    setStage('');
    setStageMessage('');
  }, []);

  return { result, intake, loading, stage, stageMessage, error, analyze, reset };
}
