/** API client for CrisisLens backend with SSE streaming support. */

import type { AnalysisResponse, IntakeResult } from '../types';

const API_BASE =
  import.meta.env.VITE_API_URL ||
  'https://crisislens-api-713762440139.us-central1.run.app/api';

export interface SSECallbacks {
  onStatus: (stage: string, message: string) => void;
  onIntake: (intake: IntakeResult) => void;
  onResult: (result: AnalysisResponse) => void;
  onError: (message: string) => void;
}

/**
 * Stream analysis results via SSE.
 * Sends multimodal input and receives progressive updates.
 */
export async function analyzeStream(
  text: string,
  files: File[],
  callbacks: SSECallbacks
): Promise<void> {
  const formData = new FormData();
  if (text.trim()) formData.append('text', text.trim());
  for (const file of files) formData.append('files', file);

  const response = await fetch(`${API_BASE}/analyze/stream`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    callbacks.onError(`Server error: ${response.status}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError('Streaming not supported');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ') && currentEvent) {
        try {
          const data = JSON.parse(line.slice(6));
          switch (currentEvent) {
            case 'status':
              callbacks.onStatus(data.stage, data.message);
              break;
            case 'intake':
              callbacks.onIntake(data as IntakeResult);
              break;
            case 'result':
              callbacks.onResult(data as AnalysisResponse);
              break;
            case 'error':
              callbacks.onError(data.message);
              break;
            case 'done':
              break;
          }
        } catch {
          // Skip malformed JSON
        }
        currentEvent = '';
      }
    }
  }
}
