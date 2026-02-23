import type { Section, AnalyzeResponse, Provider } from '../types/resume';
import { SectionBlock } from './SectionBlock';
import { SummaryPanel } from './SummaryPanel';
import { SuggestionsList } from './SuggestionsList';

interface Props {
  fileName: string;
  sections: Section[];
  analysis: AnalyzeResponse;
  provider: Provider;
  onEnhance: () => void;
  enhancing: boolean;
  onReset: () => void;
}

export function ResumeViewer({
  fileName,
  sections,
  analysis,
  provider,
  onEnhance,
  enhancing,
  onReset,
}: Props) {
  return (
    <div className="review-page">
      <header className="review-header">
        <div className="review-header-left">
          <button className="btn-ghost" onClick={onReset}>← New Upload</button>
          <h2 className="file-name">{fileName}</h2>
          <span className={`provider-badge provider-badge-${provider}`}>
            {provider === 'claude' ? 'Claude' : 'Gemini'}
          </span>
        </div>
        <button className="btn-primary" onClick={onEnhance} disabled={enhancing}>
          {enhancing ? 'Enhancing…' : '✨ Enhance Resume'}
        </button>
      </header>

      <div className="review-layout">
        <aside className="review-sidebar">
          <SummaryPanel score={analysis.overall_score} summary={analysis.summary} />
          <SuggestionsList suggestions={analysis.suggestions} />
        </aside>

        <main className="review-main">
          <div className="section-list">
            {sections.map(section => (
              <SectionBlock
                key={section.id}
                section={section}
                annotations={analysis.annotations}
              />
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
