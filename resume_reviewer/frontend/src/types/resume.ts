export interface Section {
  id: string;
  title: string;
  content: string;
}

export interface UploadResponse {
  session_id: string;
  file_name: string;
  sections: Section[];
}

export interface Annotation {
  section_id: string;
  excerpt: string;
  severity: 'error' | 'warning' | 'info';
  comment: string;
  category: string;
}

export interface Suggestion {
  priority: number;
  title: string;
  detail: string;
}

export interface AnalyzeResponse {
  overall_score: number;
  summary: string;
  annotations: Annotation[];
  suggestions: Suggestion[];
}

export interface EnhancedSection {
  id: string;
  title: string;
  content: string;
}

export interface EnhanceResponse {
  enhanced_sections: EnhancedSection[];
  change_summary: string;
}

export type AppView = 'upload' | 'review' | 'enhanced';
export type Provider = 'claude' | 'gemini';
