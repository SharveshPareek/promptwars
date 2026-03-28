/** CrisisLens - Main Application */

import { Header } from './components/Header';
import { InputPanel } from './components/InputPanel';
import { ActionPanel } from './components/ActionPanel';
import { useAnalyze } from './hooks/useAnalyze';

function App() {
  const { result, loading, stage, stageMessage, error, analyze } = useAnalyze();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded"
      >
        Skip to main content
      </a>

      <Header />

      <main
        id="main-content"
        className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6"
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-140px)]">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 overflow-y-auto">
            <InputPanel onSubmit={analyze} loading={loading} />
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 overflow-y-auto">
            <ActionPanel
              result={result}
              loading={loading}
              stage={stage}
              stageMessage={stageMessage}
              error={error}
            />
          </div>
        </div>
      </main>

      <footer className="text-center py-3 text-xs text-gray-400 border-t border-gray-200">
        <p>
          CrisisLens is an AI-assisted tool. Always call emergency services for
          life-threatening situations. Not a substitute for professional medical advice.
        </p>
      </footer>
    </div>
  );
}

export default App;
