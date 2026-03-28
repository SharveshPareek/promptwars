/** Audio recorder component with visual feedback. */

import React from 'react';
import { Mic, MicOff } from 'lucide-react';
import { clsx } from 'clsx';

interface AudioRecorderProps {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  isRecording,
  onStart,
  onStop,
}) => {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={isRecording ? onStop : onStart}
        className={clsx(
          'inline-flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-200',
          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500',
          isRecording
            ? 'bg-red-100 text-red-700 hover:bg-red-200 border border-red-300'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
        )}
        aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}
        aria-pressed={isRecording}
      >
        {isRecording ? (
          <>
            <MicOff className="h-4 w-4" aria-hidden="true" />
            Stop Recording
          </>
        ) : (
          <>
            <Mic className="h-4 w-4" aria-hidden="true" />
            Record Voice
          </>
        )}
      </button>

      {isRecording && (
        <span
          className="flex items-center gap-2 text-sm text-red-600"
          aria-live="polite"
        >
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
          </span>
          Recording...
        </span>
      )}
    </div>
  );
};
