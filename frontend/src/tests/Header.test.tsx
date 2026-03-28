/** Tests for Header component. */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Header } from '../components/Header';

describe('Header', () => {
  it('renders the app name', () => {
    render(<Header />);
    expect(screen.getByText('CrisisLens')).toBeInTheDocument();
  });

  it('renders the tagline', () => {
    render(<Header />);
    expect(screen.getByText(/AI-Powered Medical Emergency Triage/i)).toBeInTheDocument();
  });

  it('shows Gemini badge', () => {
    render(<Header />);
    expect(screen.getByText(/Powered by Gemini/i)).toBeInTheDocument();
  });

  it('has proper heading hierarchy', () => {
    render(<Header />);
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('CrisisLens');
  });

  it('renders as banner landmark', () => {
    render(<Header />);
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });
});
