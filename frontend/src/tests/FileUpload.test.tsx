/** Tests for FileUpload component. */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUpload } from '../components/ui/FileUpload';

describe('FileUpload', () => {
  const defaultProps = {
    files: [] as File[],
    onFilesChange: vi.fn(),
  };

  it('renders upload label', () => {
    render(<FileUpload {...defaultProps} />);
    expect(
      screen.getByText('Upload files (images, audio, PDFs)')
    ).toBeInTheDocument();
  });

  it('renders drop zone with accessible button', () => {
    render(<FileUpload {...defaultProps} />);
    const dropZone = screen.getByRole('button', {
      name: /drop files here or click to upload/i,
    });
    expect(dropZone).toBeInTheDocument();
  });

  it('shows file list after adding files', () => {
    const testFile = new File(['hello'], 'report.pdf', {
      type: 'application/pdf',
    });
    render(
      <FileUpload
        {...defaultProps}
        files={[testFile]}
      />
    );
    expect(screen.getByText('report.pdf')).toBeInTheDocument();
    expect(screen.getByRole('list', { name: /selected files/i })).toBeInTheDocument();
  });

  it('removes file when remove button clicked', async () => {
    const onFilesChange = vi.fn();
    const user = userEvent.setup();
    const testFile = new File(['data'], 'photo.png', { type: 'image/png' });
    render(
      <FileUpload
        files={[testFile]}
        onFilesChange={onFilesChange}
      />
    );

    const removeBtn = screen.getByRole('button', { name: /remove photo\.png/i });
    await user.click(removeBtn);
    expect(onFilesChange).toHaveBeenCalledWith([]);
  });

  it('shows error for oversized files', async () => {
    const onFilesChange = vi.fn();
    const user = userEvent.setup();

    render(
      <FileUpload
        files={[]}
        onFilesChange={onFilesChange}
        maxSizeMB={1}
      />
    );

    // Create a file that exceeds the 1MB limit
    const oversizedContent = new Uint8Array(2 * 1024 * 1024); // 2MB
    const oversizedFile = new File([oversizedContent], 'huge.pdf', {
      type: 'application/pdf',
    });

    // Simulate selecting the file via the hidden input
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(input, oversizedFile);

    expect(screen.getByRole('alert')).toHaveTextContent(
      /huge\.pdf.*exceeds.*1MB limit/i
    );
  });

  it('has proper aria-label on drop zone', () => {
    render(<FileUpload {...defaultProps} />);
    const dropZone = screen.getByRole('button', {
      name: /drop files here or click to upload/i,
    });
    expect(dropZone).toHaveAttribute(
      'aria-label',
      'Drop files here or click to upload'
    );
  });
});
