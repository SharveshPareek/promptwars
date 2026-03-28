/** Tests for AudioRecorder component. */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AudioRecorder } from '../components/AudioRecorder';

describe('AudioRecorder', () => {
  const defaultProps = {
    isRecording: false,
    onStart: vi.fn(),
    onStop: vi.fn(),
  };

  it('renders record button', () => {
    render(<AudioRecorder {...defaultProps} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('button has correct aria-label when not recording', () => {
    render(<AudioRecorder {...defaultProps} />);
    expect(screen.getByRole('button')).toHaveAttribute(
      'aria-label',
      'Start voice recording'
    );
  });

  it('shows "Record Voice" text when not recording', () => {
    render(<AudioRecorder {...defaultProps} />);
    expect(screen.getByText('Record Voice')).toBeInTheDocument();
  });

  it('button has aria-pressed attribute set to false when not recording', () => {
    render(<AudioRecorder {...defaultProps} />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'false');
  });

  it('button has aria-pressed attribute set to true when recording', () => {
    render(<AudioRecorder {...defaultProps} isRecording={true} />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true');
  });

  it('shows "Stop Recording" text when recording', () => {
    render(<AudioRecorder {...defaultProps} isRecording={true} />);
    expect(screen.getByText('Stop Recording')).toBeInTheDocument();
  });

  it('button has correct aria-label when recording', () => {
    render(<AudioRecorder {...defaultProps} isRecording={true} />);
    expect(screen.getByRole('button')).toHaveAttribute(
      'aria-label',
      'Stop recording'
    );
  });

  it('shows "Recording..." indicator when recording', () => {
    render(<AudioRecorder {...defaultProps} isRecording={true} />);
    expect(screen.getByText('Recording...')).toBeInTheDocument();
  });
});
