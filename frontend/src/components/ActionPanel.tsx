/** Right panel: displays the structured action plan output. */

import React from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Phone,
  ShieldAlert,
  XCircle,
  Info,
  ExternalLink,
} from 'lucide-react';
import { clsx } from 'clsx';
import type { AnalysisResponse } from '../types';

interface ActionPanelProps {
  result: AnalysisResponse | null;
  loading: boolean;
  error: string | null;
}

const TRIAGE_CONFIG = {
  RED: {
    label: 'IMMEDIATE',
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-300',
    icon: AlertTriangle,
  },
  YELLOW: {
    label: 'DELAYED',
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-300',
    icon: AlertTriangle,
  },
  GREEN: {
    label: 'MINOR',
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300',
    icon: CheckCircle,
  },
  BLACK: {
    label: 'EXPECTANT',
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-300',
    icon: ShieldAlert,
  },
} as const;

export const ActionPanel: React.FC<ActionPanelProps> = ({
  result,
  loading,
  error,
}) => {
  // Empty state
  if (!result && !loading && !error) {
    return (
      <section
        aria-labelledby="output-heading"
        className="flex flex-col items-center justify-center h-full text-center px-8"
      >
        <h2 id="output-heading" className="sr-only">
          Analysis Results
        </h2>
        <ShieldAlert className="h-16 w-16 text-gray-300 mb-4" aria-hidden="true" />
        <p className="text-gray-500 text-lg font-medium">
          Results will appear here
        </p>
        <p className="text-gray-400 text-sm mt-1">
          Upload photos, record voice, or describe the situation to get started
        </p>
      </section>
    );
  }

  // Loading state
  if (loading) {
    return (
      <section
        aria-labelledby="output-heading"
        aria-busy="true"
        className="flex flex-col items-center justify-center h-full text-center px-8"
      >
        <h2 id="output-heading" className="sr-only">
          Analysis Results
        </h2>
        <div className="animate-spin h-12 w-12 border-4 border-blue-200 border-t-blue-600 rounded-full mb-4" />
        <p className="text-gray-700 font-medium" aria-live="polite">
          Analyzing situation...
        </p>
        <p className="text-gray-400 text-sm mt-1">
          Running 3 AI pipelines: Intake → Reasoning → Verification
        </p>
      </section>
    );
  }

  // Error state
  if (error) {
    return (
      <section
        aria-labelledby="output-heading"
        className="flex flex-col items-center justify-center h-full text-center px-8"
      >
        <h2 id="output-heading" className="sr-only">
          Analysis Results
        </h2>
        <XCircle className="h-12 w-12 text-red-400 mb-4" aria-hidden="true" />
        <p className="text-red-600 font-medium" role="alert">
          {error}
        </p>
      </section>
    );
  }

  if (!result) return null;

  const plan = result.action_plan;
  const triage = TRIAGE_CONFIG[plan.triage_level];
  const TriageIcon = triage.icon;

  return (
    <section aria-labelledby="output-heading" className="overflow-y-auto h-full">
      <h2 id="output-heading" className="text-lg font-semibold text-gray-900 mb-4">
        Action Plan
      </h2>

      <div className="space-y-5" aria-live="polite">
        {/* Triage Badge */}
        <div
          className={clsx(
            'flex items-center gap-3 p-4 rounded-xl border',
            triage.bg,
            triage.border
          )}
        >
          <TriageIcon className={clsx('h-6 w-6', triage.text)} aria-hidden="true" />
          <div>
            <span className={clsx('text-sm font-bold uppercase', triage.text)}>
              Triage: {plan.triage_level} — {triage.label}
            </span>
            <p className="text-sm text-gray-700 mt-0.5">
              {plan.situation_summary}
            </p>
          </div>
        </div>

        {/* Emergency Call */}
        {plan.call_emergency && (
          <a
            href={`tel:${plan.emergency_number}`}
            className="flex items-center gap-3 p-4 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors"
            role="alert"
          >
            <Phone className="h-6 w-6" aria-hidden="true" />
            <div>
              <p className="font-bold">Call {plan.emergency_number} Now</p>
              <p className="text-sm text-red-100">
                This situation requires immediate emergency services
              </p>
            </div>
          </a>
        )}

        {/* Verified Actions */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
            Verified Actions
          </h3>
          <ol className="space-y-3" aria-label="List of verified actions">
            {plan.verified_actions.map((action, idx) => (
              <li
                key={idx}
                className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <span
                    className="flex-shrink-0 w-7 h-7 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-bold"
                    aria-hidden="true"
                  >
                    {action.priority}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900">{action.action}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {action.reasoning}
                    </p>
                    <div className="flex items-center gap-3 mt-2">
                      {/* Confidence bar */}
                      <div
                        className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden"
                        role="progressbar"
                        aria-valuenow={Math.round(action.confidence * 100)}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-label={`Confidence: ${Math.round(action.confidence * 100)}%`}
                      >
                        <div
                          className={clsx(
                            'h-full rounded-full transition-all',
                            action.confidence >= 0.8
                              ? 'bg-green-500'
                              : action.confidence >= 0.5
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                          )}
                          style={{ width: `${action.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 font-mono">
                        {Math.round(action.confidence * 100)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Source: {action.source}
                    </p>
                  </div>
                </div>
                {action.do_not && (
                  <div className="mt-3 flex items-start gap-2 p-2.5 bg-red-50 rounded-lg border border-red-200">
                    <XCircle
                      className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5"
                      aria-hidden="true"
                    />
                    <p className="text-sm text-red-700">
                      <strong>Do NOT:</strong> {action.do_not}
                    </p>
                  </div>
                )}
              </li>
            ))}
          </ol>
        </div>

        {/* What NOT to do */}
        {plan.what_not_to_do.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-red-800 uppercase tracking-wide mb-2 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" aria-hidden="true" />
              What NOT to Do
            </h3>
            <ul className="space-y-1.5" aria-label="Actions to avoid">
              {plan.what_not_to_do.map((item, idx) => (
                <li key={idx} className="text-sm text-red-700 flex items-start gap-2">
                  <XCircle
                    className="h-4 w-4 flex-shrink-0 mt-0.5"
                    aria-hidden="true"
                  />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Verification Sources */}
        {plan.verification_sources.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-2">
              <Info className="h-4 w-4" aria-hidden="true" />
              Verification Sources
            </h3>
            <ul className="space-y-1" aria-label="Sources used for verification">
              {plan.verification_sources.map((source, idx) => (
                <li
                  key={idx}
                  className="text-sm text-gray-600 flex items-center gap-2"
                >
                  <ExternalLink className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
                  {source}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Overall Confidence */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
          <span className="text-sm font-medium text-gray-600">
            Overall Confidence
          </span>
          <span
            className={clsx(
              'text-lg font-bold',
              plan.confidence_overall >= 0.8
                ? 'text-green-600'
                : plan.confidence_overall >= 0.5
                  ? 'text-yellow-600'
                  : 'text-red-600'
            )}
          >
            {Math.round(plan.confidence_overall * 100)}%
          </span>
        </div>
      </div>
    </section>
  );
};
