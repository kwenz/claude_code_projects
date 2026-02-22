import { useRef, useState, DragEvent, ChangeEvent } from 'react';
import type { Provider } from '../types/resume';

interface Props {
  onFile: (file: File) => void;
  loading: boolean;
  error: string | null;
  provider: Provider;
  onProviderChange: (p: Provider) => void;
}

export function UploadZone({ onFile, loading, error, provider, onProviderChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onFile(file);
  }

  return (
    <div className="upload-page">
      <div className="upload-hero">
        <h1>Resume Reviewer</h1>
        <p className="subtitle">Upload your resume and get AI-powered feedback instantly.</p>
      </div>

      <div className="provider-toggle">
        <button
          className={`provider-pill ${provider === 'claude' ? 'active' : ''}`}
          onClick={() => onProviderChange('claude')}
          disabled={loading}
        >
          Claude
        </button>
        <button
          className={`provider-pill ${provider === 'gemini' ? 'active' : ''}`}
          onClick={() => onProviderChange('gemini')}
          disabled={loading}
        >
          Gemini
        </button>
      </div>

      <div
        className={`drop-zone ${dragging ? 'dragging' : ''} ${loading ? 'loading' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !loading && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          style={{ display: 'none' }}
          onChange={handleChange}
        />

        {loading ? (
          <div className="dz-content">
            <div className="spinner" />
            <p>Uploading &amp; analyzing…</p>
          </div>
        ) : (
          <div className="dz-content">
            <div className="dz-icon">📄</div>
            <p className="dz-main">Drop your resume here or <span className="link">browse</span></p>
            <p className="dz-sub">PDF or DOCX · max 10 MB</p>
          </div>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}
    </div>
  );
}
