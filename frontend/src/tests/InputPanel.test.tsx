/** Tests for InputPanel component. */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InputPanel } from '../components/InputPanel';

describe('InputPanel', () => {
  const onSubmit = vi.fn();

  it('renders the heading', () => {
    render(<InputPanel onSubmit={onSubmit} loading={false} />);
    expect(screen.getByText('Describe the Situation')).toBeInTheDocument();
  });

  it('renders text area with label', () => {
    render(<InputPanel onSubmit={onSubmit} loading={false} />);
    expect(screen.getByLabelText(/what's happening/i)).toBeInTheDocument();
  });

  it('renders file upload area', () => {
    render(<InputPanel onSubmit={onSubmit} loading={false} />);
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('renders voice recording button', () => {
    render(<InputPanel onSubmit={onSubmit} loading={false} />);
    expect(screen.getByRole('button', { name: /voice recording/i })).toBeInTheDocument();
  });

  it('submit button is disabled when no input', () => {
    render(<InputPanel onSubmit={onSubmit} loading={false} />);
    expect(screen.getByRole('button', { name: /analyze situation/i })).toBeDisabled();
  });

  it('submit button enables after typing text', async () => {
    const user = userEvent.setup();
    render(<InputPanel onSubmit={onSubmit} loading={false} />);
    await user.type(screen.getByLabelText(/what's happening/i), 'headache');
    expect(screen.getByRole('button', { name: /analyze situation/i })).not.toBeDisabled();
  });

  it('shows loading state on submit button', () => {
    render(<InputPanel onSubmit={onSubmit} loading={true} />);
    expect(screen.getByRole('button', { name: /analyzing/i })).toBeDisabled();
  });

  it('disables textarea when loading', () => {
    render(<InputPanel onSubmit={onSubmit} loading={true} />);
    expect(screen.getByLabelText(/what's happening/i)).toBeDisabled();
  });

  it('has section with aria-labelledby', () => {
    const { container } = render(<InputPanel onSubmit={onSubmit} loading={false} />);
    expect(container.querySelector('[aria-labelledby]')).toBeInTheDocument();
  });
});
