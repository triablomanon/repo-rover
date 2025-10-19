// types.ts - TypeScript type definitions

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  isError?: boolean;
  isLoading?: boolean;
}

export interface PaperInfo {
  title: string;
  arxiv_id: string;
  authors: string[];
  summary: string;
  pdf_url: string;
  published: string;
}

export interface CodeSnippet {
  text: string;
  score: number;
  metadata: Record<string, any>;
  file_path?: string;
  document_title?: string;
  document_id?: string;
}

export interface Citation {
  file_path?: string;
  line_start?: number;
  line_end?: number;
  snippet_preview: string;
  score: number;
}

export interface ChatResponse {
  success: boolean;
  answer?: string;
  code_snippets?: CodeSnippet[];
  citations?: Citation[];  // NEW: Structured citations
  confidence?: 'low' | 'medium' | 'high';
  num_sources?: number;
  error?: string;
  message?: string;
}

export interface PaperOption {
  index: number;
  title: string;
  arxiv_id: string;
  authors: string;
  summary: string;
}

export interface SearchPaperResponse {
  success: boolean;
  needs_selection?: boolean;
  options?: PaperOption[];
  message: string;
  can_search_more?: boolean;
  suggest_gemini?: boolean;
  paper?: {
    title: string;
    arxiv_id: string;
    authors: string;
  };
  error?: string;
}

export interface SelectPaperResponse {
  success: boolean;
  selected?: boolean;
  arxiv_id?: string;
  title?: string;
  cancelled?: boolean;
  needs_selection?: boolean;
  options?: PaperOption[];
  message: string;
  can_search_more?: boolean;
  error?: string;
}

export interface InitPaperResponse {
  success: boolean;
  message: string;
  paper_info?: PaperInfo;
  repo_url?: string;
  indexed_files?: number | string;
  error?: string;
}

export interface SessionStatus {
  initialized: boolean;
  session_valid: boolean;
  has_error?: boolean;
  error_message?: string;
}

export interface AppState {
  sessionId: string | null;
  paperInfo: PaperInfo | null;
  isInitialized: boolean;
  isPaperVisible: boolean;
}
