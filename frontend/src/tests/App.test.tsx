/** Tests for App component. */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock the useAnalyze hook so App renders without making API calls
vi.mock('../hooks/useAnalyze', () => ({
  useAnalyze: () => ({
    result: null,
    loading: false,
    stage: '',
    stageMessage: '',
    error: null,
    analyze: vi.fn(),
    reset: vi.fn(),
  }),
}));

// Mock the useAudioRecorder hook to avoid MediaRecorder dependency
vi.mock('../hooks/useAudioRecorder', () => ({
  useAudioRecorder: () => ({
    isRecording: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
  }),
}));

import App from '../App';

describe('App', () => {
  it('renders header', () => {
    render(<App />);
    expect(screen.getByText('CrisisLens')).toBeInTheDocument();
  });

  it('renders input panel', () => {
    render(<App />);
    expect(screen.getByText('Describe the Situation')).toBeInTheDocument();
  });

  it('renders output panel', () => {
    render(<App />);
    expect(screen.getByText(/results will appear here/i)).toBeInTheDocument();
  });

  it('has skip-to-content link', () => {
    render(<App />);
    const skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  it('has main landmark', () => {
    render(<App />);
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content');
  });

  it('has footer with disclaimer', () => {
    render(<App />);
    expect(
      screen.getByText(/not a substitute for professional medical advice/i)
    ).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
  });
});
