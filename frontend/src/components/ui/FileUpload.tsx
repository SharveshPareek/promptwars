/** Accessible drag-and-drop file upload component. */

import React, { useRef, useState } from 'react';
import { Upload, X } from 'lucide-react';
import { clsx } from 'clsx';

interface FileUploadProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  accept?: string;
  maxSizeMB?: number;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  files,
  onFilesChange,
  accept = 'image/*,audio/*,application/pdf',
  maxSizeMB = 50,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadId = React.useId();

  const validateAndAdd = (newFiles: File[]) => {
    setError(null);
    const valid: File[] = [];
    for (const file of newFiles) {
      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`"${file.name}" exceeds ${maxSizeMB}MB limit.`);
        continue;
      }
      valid.push(file);
    }
    onFilesChange([...files, ...valid]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    validateAndAdd(Array.from(e.dataTransfer.files));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      validateAndAdd(Array.from(e.target.files));
    }
  };

  const removeFile = (index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  };

  return (
    <div>
      <label htmlFor={uploadId} className="block text-sm font-medium text-gray-700 mb-2">
        Upload files (images, audio, PDFs)
      </label>

      <button
        type="button"
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onClick={() => inputRef.current?.click()}
        aria-label="Drop files here or click to upload"
        className={clsx(
          'w-full border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200',
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        )}
      >
        <input
          ref={inputRef}
          id={uploadId}
          type="file"
          multiple
          accept={accept}
          onChange={handleChange}
          className="hidden"
          aria-hidden="true"
        />
        <Upload className="mx-auto h-10 w-10 text-gray-400 mb-3" aria-hidden="true" />
        <p className="text-gray-600 font-medium">
          Drag & drop files here, or click to browse
        </p>
        <p className="text-gray-400 text-sm mt-1">
          Images, audio recordings, or PDFs (max {maxSizeMB}MB)
        </p>
      </button>

      {error && (
        <p className="text-red-600 text-sm mt-2" role="alert">
          {error}
        </p>
      )}

      {files.length > 0 && (
        <ul className="mt-4 space-y-2" aria-label="Selected files">
          {files.map((file, idx) => (
            <li
              key={`${file.name}-${idx}`}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(idx);
                }}
                className="ml-3 p-1 text-gray-400 hover:text-red-600 rounded focus-visible:outline-2 focus-visible:outline-red-500"
                aria-label={`Remove ${file.name}`}
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
