import type { Section, Annotation } from '../types/resume';
import { AnnotationCallout } from './AnnotationCallout';

interface Props {
  section: Section;
  annotations: Annotation[];
}

interface Span {
  start: number;
  end: number;
  severity: string;
  idx: number;
}

const SEVERITY_RANK: Record<string, number> = { error: 3, warning: 2, info: 1 };

function highlightText(text: string, annotations: Annotation[]): React.ReactNode[] {
  const spans: Span[] = [];

  annotations.forEach((ann, idx) => {
    const excerpt = ann.excerpt.trim();
    if (!excerpt) return;
    let pos = 0;
    while (true) {
      const found = text.indexOf(excerpt, pos);
      if (found === -1) break;
      spans.push({ start: found, end: found + excerpt.length, severity: ann.severity, idx });
      pos = found + excerpt.length;
    }
  });

  if (spans.length === 0) return splitNewlines(text, 'base');

  // Sort by start; on overlap keep highest severity
  spans.sort((a, b) => a.start - b.start || (SEVERITY_RANK[b.severity] ?? 0) - (SEVERITY_RANK[a.severity] ?? 0));
  const merged: Span[] = [];
  for (const s of spans) {
    const last = merged[merged.length - 1];
    if (last && s.start < last.end) continue;
    merged.push(s);
  }

  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  for (const span of merged) {
    if (cursor < span.start) {
      nodes.push(...splitNewlines(text.slice(cursor, span.start), `pre-${span.idx}`));
    }
    nodes.push(
      <mark key={`mark-${span.idx}-${span.start}`} className={`highlight highlight-${span.severity}`}>
        {text.slice(span.start, span.end)}
      </mark>
    );
    cursor = span.end;
  }
  if (cursor < text.length) {
    nodes.push(...splitNewlines(text.slice(cursor), 'tail'));
  }
  return nodes;
}

function splitNewlines(text: string, prefix: string): React.ReactNode[] {
  const lines = text.split('\n');
  return lines.flatMap((line, j) =>
    j < lines.length - 1
      ? [line, <br key={`${prefix}-br-${j}`} />]
      : [line]
  );
}

export function SectionBlock({ section, annotations }: Props) {
  const sectionAnnotations = annotations.filter(a => a.section_id === section.id);
  const hasAnnotations = sectionAnnotations.length > 0;

  return (
    <div className={`section-block ${hasAnnotations ? 'has-annotations' : ''}`}>
      <div className="section-content-wrap">
        <h3 className="section-title">{section.title}</h3>
        <div className="section-text">
          {highlightText(section.content, sectionAnnotations)}
        </div>
      </div>

      {hasAnnotations && (
        <div className="callout-column">
          {sectionAnnotations.map((ann, i) => (
            <AnnotationCallout
              key={`${ann.section_id}-${ann.excerpt.slice(0, 20)}-${i}`}
              annotation={ann}
              index={i}
            />
          ))}
        </div>
      )}
    </div>
  );
}
