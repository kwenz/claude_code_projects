import './App.css';
import { useResumeSession } from './hooks/useResumeSession';
import { UploadZone } from './components/UploadZone';
import { ResumeViewer } from './components/ResumeViewer';
import { EnhancedView } from './components/EnhancedView';

export default function App() {
  const session = useResumeSession();

  if (session.view === 'enhanced' && session.enhanced && session.analysis) {
    return (
      <EnhancedView
        originalSections={session.sections}
        enhanced={session.enhanced}
        fileName={session.fileName}
        onBack={session.goToReview}
        onReset={session.reset}
      />
    );
  }

  if (session.view === 'review' && session.analysis) {
    return (
      <ResumeViewer
        fileName={session.fileName}
        sections={session.sections}
        analysis={session.analysis}
        provider={session.provider}
        onEnhance={session.enhance}
        enhancing={session.loading}
        onReset={session.reset}
      />
    );
  }

  return (
    <UploadZone
      onFile={session.uploadAndAnalyze}
      loading={session.loading}
      error={session.error}
      provider={session.provider}
      onProviderChange={session.setProvider}
    />
  );
}
