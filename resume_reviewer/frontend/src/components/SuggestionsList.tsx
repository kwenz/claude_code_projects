import type { Suggestion } from '../types/resume';

interface Props {
  suggestions: Suggestion[];
}

const PRIORITY_LABELS = ['', '🔴 High', '🟠 Medium', '🟡 Low'];

export function SuggestionsList({ suggestions }: Props) {
  return (
    <div className="suggestions-list">
      <h3>Improvement Suggestions</h3>
      <ol>
        {suggestions.map(s => (
          <li key={s.priority} className="suggestion-item">
            <div className="suggestion-header">
              <span className="priority-badge">
                {PRIORITY_LABELS[s.priority] ?? `#${s.priority}`}
              </span>
              <strong>{s.title}</strong>
            </div>
            <p>{s.detail}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
