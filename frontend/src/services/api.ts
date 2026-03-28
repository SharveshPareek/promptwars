/** API client for CrisisLens backend. */

import axios from 'axios';
import type { AnalysisResponse } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 120000, // 2 minutes — Gemini pipelines can take time
});

/**
 * Send multimodal input to the analysis endpoint.
 * Accepts text + files (images, audio, PDFs).
 */
export async function analyzeInput(
  text: string,
  files: File[]
): Promise<AnalysisResponse> {
  const formData = new FormData();

  if (text.trim()) {
    formData.append('text', text.trim());
  }

  for (const file of files) {
    formData.append('files', file);
  }

  const response = await api.post<AnalysisResponse>('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
}
