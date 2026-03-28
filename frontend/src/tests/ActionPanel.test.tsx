/** Tests for ActionPanel component. */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActionPanel } from '../components/ActionPanel';
import type { AnalysisResponse } from '../types';

const defaultProps = {
  result: null as AnalysisResponse | null,
  loading: false,
  stage: '',
  stageMessage: '',
  error: null as string | null,
};

const mockResult: AnalysisResponse = {
  session_id: 'test-123',
  action_plan: {
    situation_summary: 'Potential drug interaction between aspirin and ibuprofen',
    triage_level: 'YELLOW' as const,
    verified_actions: [
      {
        priority: 1,
        action: 'Stop taking both medications',
        reasoning: 'NSAIDs should not be combined',
        confidence: 0.92,
        source: 'FDA Drug Interaction Guidelines',
        do_not: 'Do not take additional NSAIDs',
      },
    ],
    what_not_to_do: ['Do not give additional medication'],
    call_emergency: false,
    emergency_number: '108',
    verification_sources: ['FDA', 'Mayo Clinic'],
    confidence_overall: 0.88,
  },
};

const emergencyResult: AnalysisResponse = {
  session_id: 'test-456',
  action_plan: {
    ...mockResult.action_plan,
    triage_level: 'RED',
    call_emergency: true,
    emergency_number: '911',
  },
};

describe('ActionPanel', () => {
  it('shows empty state when no result', () => {
    render(<ActionPanel {...defaultProps} />);
    expect(screen.getByText(/results will appear here/i)).toBeInTheDocument();
  });

  it('shows loading state with stage message', () => {
    render(
      <ActionPanel {...defaultProps} loading={true} stage="analyzing" stageMessage="Analyzing with Gemini AI..." />
    );
    expect(screen.getByText(/analyzing with gemini ai/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<ActionPanel {...defaultProps} error="Something went wrong" />);
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it('renders triage level badge', () => {
    render(<ActionPanel {...defaultProps} result={mockResult} />);
    expect(screen.getByText(/YELLOW/)).toBeInTheDocument();
    expect(screen.getByText(/DELAYED/)).toBeInTheDocument();
  });

  it('renders RED triage with emergency call', () => {
    render(<ActionPanel {...defaultProps} result={emergencyResult} />);
    expect(screen.getByText(/RED/)).toBeInTheDocument();
    expect(screen.getByText(/Call 911 Now/)).toBeInTheDocument();
  });

  it('renders verified actions', () => {
    render(<ActionPanel {...defaultProps} result={mockResult} />);
    expect(screen.getByText(/stop taking both medications/i)).toBeInTheDocument();
  });

  it('renders confidence percentage', () => {
    render(<ActionPanel {...defaultProps} result={mockResult} />);
    expect(screen.getByText('88%')).toBeInTheDocument();
  });

  it('renders what not to do section', () => {
    render(<ActionPanel {...defaultProps} result={mockResult} />);
    expect(screen.getByText(/do not give additional medication/i)).toBeInTheDocument();
  });

  it('renders verification sources', () => {
    render(<ActionPanel {...defaultProps} result={mockResult} />);
    expect(screen.getByText('FDA')).toBeInTheDocument();
    expect(screen.getByText('Mayo Clinic')).toBeInTheDocument();
  });

  it('has accessible loading state with aria-busy', () => {
    const { container } = render(
      <ActionPanel {...defaultProps} loading={true} stage="analyzing" stageMessage="Working..." />
    );
    expect(container.querySelector('[aria-busy="true"]')).toBeInTheDocument();
  });

  it('has accessible confidence progress bars', () => {
    render(<ActionPanel {...defaultProps} result={mockResult} />);
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBeGreaterThan(0);
    expect(progressBars[0]).toHaveAttribute('aria-valuenow', '92');
  });

  it('renders do_not warning on actions', () => {
    render(<ActionPanel {...defaultProps} result={mockResult} />);
    expect(screen.getByText(/do not take additional nsaids/i)).toBeInTheDocument();
  });
});
