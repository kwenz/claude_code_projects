import type { Annotation } from '../types/resume';

interface Props {
  annotation: Annotation;
  index: number;
}

const SEVERITY_LABELS: Record<string, string> = {
  error: '✗ Issue',
  warning: '⚠ Warning',
  info: 'ℹ Tip',
};

export function AnnotationCallout({ annotation, index }: Props) {
  return (
    <div className={`callout callout-${annotation.severity}`} data-index={index}>
      <div className="callout-header">
        <span className="callout-severity">{SEVERITY_LABELS[annotation.severity]}</span>
        <span className="callout-category">{annotation.category}</span>
      </div>
      <p className="callout-comment">{annotation.comment}</p>
    </div>
  );
}
