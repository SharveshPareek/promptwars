/** Application header with branding. */

import React from 'react';
import { ShieldCheck } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center gap-3">
        <ShieldCheck className="h-8 w-8 text-blue-600" aria-hidden="true" />
        <div>
          <h1 className="text-xl font-bold text-gray-900">CrisisLens</h1>
          <p className="text-sm text-gray-500">
            AI-Powered Medical Emergency Triage
          </p>
        </div>
        <span className="ml-auto text-xs bg-green-100 text-green-700 px-2.5 py-1 rounded-full font-medium">
          Powered by Gemini
        </span>
      </div>
    </header>
  );
};
