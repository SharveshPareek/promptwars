/** Left panel: multimodal input (text + files + voice). */

import React, { useState, useCallback } from 'react';
import { Send } from 'lucide-react';
import { Button } from './ui/Button';
import { FileUpload } from './ui/FileUpload';
import { AudioRecorder } from './AudioRecorder';
import { useAudioRecorder } from '../hooks/useAudioRecorder';

interface InputPanelProps {
  onSubmit: (text: string, files: File[]) => void;
  loading: boolean;
}

export const InputPanel: React.FC<InputPanelProps> = ({ onSubmit, loading }) => {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const { isRecording, startRecording, stopRecording } = useAudioRecorder();
  const textareaId = React.useId();

  const handleStopRecording = useCallback(() => {
    const audioFile = stopRecording();
    if (audioFile) {
      setFiles((prev) => [...prev, audioFile]);
    }
  }, [stopRecording]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() && files.length === 0) return;
    onSubmit(text, files);
  };

  const hasInput = text.trim().length > 0 || files.length > 0;

  return (
    <section aria-labelledby="input-heading" className="flex flex-col h-full">
      <h2 id="input-heading" className="text-lg font-semibold text-gray-900 mb-4">
        Describe the Situation
      </h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5 flex-1">
        {/* Text input */}
        <div>
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            What's happening?
          </label>
          <textarea
            id={textareaId}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Describe the emergency situation... e.g., 'My grandmother took these medications and is feeling dizzy and nauseous'"
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl resize-none text-gray-800 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            disabled={loading}
          />
        </div>

        {/* File upload */}
        <FileUpload files={files} onFilesChange={setFiles} />

        {/* Audio recorder */}
        <AudioRecorder
          isRecording={isRecording}
          onStart={startRecording}
          onStop={handleStopRecording}
        />

        {/* Submit */}
        <div className="mt-auto pt-4">
          <Button
            type="submit"
            variant="primary"
            loading={loading}
            disabled={!hasInput || loading}
            className="w-full"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
            {loading ? 'Analyzing...' : 'Analyze Situation'}
          </Button>
        </div>
      </form>
    </section>
  );
};
