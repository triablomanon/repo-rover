// geminiService.ts - Service for interacting with Repo Rover API

import type { ChatResponse, InitPaperResponse, SessionStatus, PaperInfo, SearchPaperResponse, SelectPaperResponse } from '../types';

const API_URL = (import.meta as any).env.VITE_API_URL ?? "http://localhost:5000/api";

// Session management
let currentSessionId: string | null = null;

/**
 * Create a new session
 */
export const createSession = async (): Promise<string> => {
  try {
    const res = await fetch(`${API_URL}/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      throw new Error(`Failed to create session: ${res.status}`);
    }

    const data = await res.json();
    currentSessionId = data.session_id;
    return data.session_id;
  } catch (err) {
    console.error("Error creating session:", err);
    throw err;
  }
};

/**
 * Get current session ID (create if doesn't exist)
 */
export const getSessionId = async (): Promise<string> => {
  if (!currentSessionId) {
    return await createSession();
  }
  return currentSessionId;
};

/**
 * Search for papers (returns options for user selection)
 */
export const searchPaper = async (query: string, useGemini: boolean = false): Promise<SearchPaperResponse> => {
  try {
    const sessionId = await getSessionId();

    const res = await fetch(`${API_URL}/search-paper`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, query, use_gemini: useGemini }),
    });

    const data = await res.json();
    return data;
  } catch (err) {
    console.error("Error searching paper:", err);
    return {
      success: false,
      error: "Network error",
      message: "Failed to connect to the server. Please try again.",
    };
  }
};

/**
 * Select a paper from search results
 */
export const selectPaper = async (selection: number | string): Promise<SelectPaperResponse> => {
  try {
    const sessionId = await getSessionId();

    const res = await fetch(`${API_URL}/select-paper`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, selection }),
    });

    const data = await res.json();
    return data;
  } catch (err) {
    console.error("Error selecting paper:", err);
    return {
      success: false,
      error: "Network error",
      message: "Failed to connect to the server. Please try again.",
    };
  }
};

/**
 * Initialize paper analysis pipeline with specific ArXiv ID
 */
export const initPaper = async (arxivId: string): Promise<InitPaperResponse> => {
  try {
    const sessionId = await getSessionId();

    const res = await fetch(`${API_URL}/init-paper`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, arxiv_id: arxivId }),
    });

    const data = await res.json();
    return data;
  } catch (err) {
    console.error("Error initializing paper:", err);
    return {
      success: false,
      error: "Network error",
      message: "Failed to connect to the server. Please try again.",
    };
  }
};

/**
 * Send a chat message (query about the paper)
 */
export const sendChatMessage = async (message: string): Promise<ChatResponse> => {
  try {
    const sessionId = await getSessionId();

    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    const data = await res.json();
    return data;
  } catch (err) {
    console.error("Error sending chat message:", err);
    return {
      success: false,
      error: "Network error",
      message: "Failed to connect to the server. Please try again.",
    };
  }
};

/**
 * Get session status
 */
export const getSessionStatus = async (): Promise<SessionStatus> => {
  try {
    const sessionId = await getSessionId();

    const res = await fetch(`${API_URL}/status?session_id=${sessionId}`);
    const data = await res.json();
    return data;
  } catch (err) {
    console.error("Error getting session status:", err);
    return {
      initialized: false,
      session_valid: false,
    };
  }
};

/**
 * Get current paper info
 */
export const getPaperInfo = async (): Promise<PaperInfo | null> => {
  try {
    const sessionId = await getSessionId();

    const res = await fetch(`${API_URL}/paper-info?session_id=${sessionId}`);

    if (!res.ok) {
      return null;
    }

    const data = await res.json();
    return data.success ? data.paper : null;
  } catch (err) {
    console.error("Error getting paper info:", err);
    return null;
  }
};

/**
 * Reset session (start over with new paper)
 */
export const resetSession = async (): Promise<string> => {
  try {
    const sessionId = await getSessionId();

    const res = await fetch(`${API_URL}/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });

    const data = await res.json();
    currentSessionId = data.session_id;
    return data.session_id;
  } catch (err) {
    console.error("Error resetting session:", err);
    throw err;
  }
};
