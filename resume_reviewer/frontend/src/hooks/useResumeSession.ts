import { useState, useCallback, useRef } from 'react';
import type {
  Section,
  AnalyzeResponse,
  EnhanceResponse,
  AppView,
  Provider,
} from '../types/resume';
import { uploadResume, analyzeResume, enhanceResume } from '../api/client';

interface SessionState {
  sessionId: string | null;
  fileName: string;
  sections: Section[];
  analysis: AnalyzeResponse | null;
  enhanced: EnhanceResponse | null;
  view: AppView;
  loading: boolean;
  error: string | null;
  provider: Provider;
}

const initial: SessionState = {
  sessionId: null,
  fileName: '',
  sections: [],
  analysis: null,
  enhanced: null,
  view: 'upload',
  loading: false,
  error: null,
  provider: 'claude',
};

export function useResumeSession() {
  const [state, setState] = useState<SessionState>(initial);
  // Use refs so callbacks don't need state in their dep arrays
  const sessionIdRef = useRef<string | null>(null);
  const providerRef = useRef<Provider>('claude');

  const setProvider = useCallback((p: Provider) => {
    providerRef.current = p;
    setState(s => ({ ...s, provider: p }));
  }, []);

  /** Upload a file and immediately run analysis */
  const uploadAndAnalyze = useCallback(async (file: File) => {
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const upload = await uploadResume(file);
      sessionIdRef.current = upload.session_id;
      setState(s => ({
        ...s,
        sessionId: upload.session_id,
        fileName: upload.file_name,
        sections: upload.sections,
      }));

      const analysis = await analyzeResume(upload.session_id, providerRef.current);
      setState(s => ({
        ...s,
        analysis,
        view: 'review',
        loading: false,
      }));
    } catch (e: unknown) {
      setState(s => ({
        ...s,
        loading: false,
        error: extractError(e, 'Upload or analysis failed.'),
      }));
    }
  }, []);

  const enhance = useCallback(async () => {
    const sid = sessionIdRef.current;
    if (!sid) return;
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const result = await enhanceResume(sid, providerRef.current);
      setState(s => ({ ...s, enhanced: result, view: 'enhanced', loading: false }));
    } catch (e: unknown) {
      setState(s => ({
        ...s,
        loading: false,
        error: extractError(e, 'Enhancement failed.'),
      }));
    }
  }, []);

  const reset = useCallback(() => {
    sessionIdRef.current = null;
    setState(initial);
  }, []);

  const goToReview = useCallback(() => setState(s => ({ ...s, view: 'review' })), []);

  return { ...state, setProvider, uploadAndAnalyze, enhance, reset, goToReview };
}

function extractError(e: unknown, fallback: string): string {
  if (e && typeof e === 'object') {
    const ax = e as { response?: { data?: { detail?: string } }; message?: string };
    return ax.response?.data?.detail ?? ax.message ?? fallback;
  }
  return fallback;
}
