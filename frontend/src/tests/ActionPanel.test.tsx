/** Tests for ActionPanel component. */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActionPanel } from '../components/ActionPanel';
import type { AnalysisResponse } from '../types';

const mockResult: AnalysisResponse = {
  session_id: 'test-123',
  intake: {
    situation_type: 'medical',
    severity: 'high',
    entities: ['aspirin', 'ibuprofen'],
    symptoms_or_damage: ['dizziness', 'nausea'],
    location_cues: ['home'],
    time_sensitivity: 'Urgent',
    raw_summary: 'Patient took multiple medications.',
  },
  action_plan: {
    situation_summary: 'Potential drug interaction between aspirin and ibuprofen',
    triage_level: 'YELLOW',
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
    emergency_number: '911',
    verification_sources: ['FDA', 'Mayo Clinic'],
    confidence_overall: 0.88,
  },
};

describe('ActionPanel', () => {
  it('shows empty state when no result', () => {
    render(<ActionPanel result={null} loading={false} error={null} />);
    expect(screen.getByText(/results will appear here/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ActionPanel result={null} loading={true} error={null} />);
    expect(screen.getByText(/analyzing situation/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(
      <ActionPanel result={null} loading={false} error="Something went wrong" />
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it('renders triage level badge', () => {
    render(<ActionPanel result={mockResult} loading={false} error={null} />);
    expect(screen.getByText(/YELLOW/)).toBeInTheDocument();
    expect(screen.getByText(/DELAYED/)).toBeInTheDocument();
  });

  it('renders verified actions', () => {
    render(<ActionPanel result={mockResult} loading={false} error={null} />);
    expect(
      screen.getByText(/stop taking both medications/i)
    ).toBeInTheDocument();
  });

  it('renders confidence percentage', () => {
    render(<ActionPanel result={mockResult} loading={false} error={null} />);
    expect(screen.getByText('88%')).toBeInTheDocument();
  });

  it('renders what not to do section', () => {
    render(<ActionPanel result={mockResult} loading={false} error={null} />);
    expect(
      screen.getByText(/do not give additional medication/i)
    ).toBeInTheDocument();
  });

  it('renders verification sources', () => {
    render(<ActionPanel result={mockResult} loading={false} error={null} />);
    expect(screen.getByText('FDA')).toBeInTheDocument();
    expect(screen.getByText('Mayo Clinic')).toBeInTheDocument();
  });

  it('has accessible loading state with aria-busy', () => {
    const { container } = render(
      <ActionPanel result={null} loading={true} error={null} />
    );
    const section = container.querySelector('[aria-busy="true"]');
    expect(section).toBeInTheDocument();
  });

  it('has accessible confidence progress bars', () => {
    render(<ActionPanel result={mockResult} loading={false} error={null} />);
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBeGreaterThan(0);
    expect(progressBars[0]).toHaveAttribute('aria-valuenow', '92');
  });
});
