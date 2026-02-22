import axios from 'axios';
import type { UploadResponse, AnalyzeResponse, EnhanceResponse } from '../types/resume';
import type { Provider } from '../types/resume';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export async function uploadResume(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<UploadResponse>('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function analyzeResume(session_id: string, provider: Provider): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>('/analyze', { session_id, provider });
  return data;
}

export async function enhanceResume(session_id: string, provider: Provider): Promise<EnhanceResponse> {
  const { data } = await api.post<EnhanceResponse>('/enhance', { session_id, provider });
  return data;
}
