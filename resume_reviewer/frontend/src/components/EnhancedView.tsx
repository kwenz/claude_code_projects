import { useState } from 'react';
import type { Section, EnhanceResponse } from '../types/resume';

interface Props {
  originalSections: Section[];
  enhanced: EnhanceResponse;
  fileName: string;
  onBack: () => void;
  onReset: () => void;
}

export function EnhancedView({ originalSections, enhanced, fileName, onBack, onReset }: Props) {
  const [enhancedOnly, setEnhancedOnly] = useState(false);

  function handleDownload() {
    const text = enhanced.enhanced_sections
      .map(s => `${s.title}\n${'─'.repeat(s.title.length)}\n${s.content}`)
      .join('\n\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `enhanced_${fileName.replace(/\.[^.]+$/, '')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const originalMap = new Map(originalSections.map(s => [s.id, s]));

  return (
    <div className="enhanced-page">
      <header className="enhanced-header">
        <div className="enhanced-header-left">
          <button className="btn-ghost" onClick={onBack}>← Back to Review</button>
          <button className="btn-ghost" onClick={onReset}>New Upload</button>
        </div>
        <div className="enhanced-header-right">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={enhancedOnly}
              onChange={e => setEnhancedOnly(e.target.checked)}
            />
            Enhanced only
          </label>
          <button className="btn-primary" onClick={handleDownload}>⬇ Download</button>
        </div>
      </header>

      <div className="change-banner">
        <strong>Changes:</strong> {enhanced.change_summary}
      </div>

      <div className={`enhanced-grid ${enhancedOnly ? 'enhanced-only' : ''}`}>
        {!enhancedOnly && (
          <div className="side original-side">
            <h3 className="side-label">Original</h3>
            {originalSections.map(s => (
              <div key={s.id} className="compare-section original-section">
                <h4>{s.title}</h4>
                <pre className="compare-text">{s.content}</pre>
              </div>
            ))}
          </div>
        )}

        <div className="side enhanced-side">
          <h3 className="side-label">Enhanced</h3>
          {enhanced.enhanced_sections.map(s => {
            const orig = originalMap.get(s.id);
            const changed = orig ? orig.content !== s.content : true;
            return (
              <div key={s.id} className={`compare-section enhanced-section ${changed ? 'changed' : ''}`}>
                <h4>
                  {s.title}
                  {changed && <span className="changed-badge">Improved</span>}
                </h4>
                <pre className="compare-text">{s.content}</pre>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
