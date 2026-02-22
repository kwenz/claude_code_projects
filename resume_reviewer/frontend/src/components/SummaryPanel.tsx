interface Props {
  score: number;
  summary: string;
}

export function SummaryPanel({ score, summary }: Props) {
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <div className="summary-panel">
      <div className="score-gauge">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="36" fill="none" stroke="#e5e7eb" strokeWidth="10" />
          <circle
            cx="50"
            cy="50"
            r="36"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 50 50)"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
          <text x="50" y="55" textAnchor="middle" fontSize="20" fontWeight="700" fill={color}>
            {score}
          </text>
        </svg>
        <p className="gauge-label">Overall Score</p>
      </div>

      <div className="summary-text">
        <h3>Summary</h3>
        <p>{summary}</p>
      </div>
    </div>
  );
}
