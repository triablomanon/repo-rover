// ChatPanel.tsx - Chat interface component for Repo Rover

import React, { useState, useRef, useEffect } from 'react';
import { searchPaper, selectPaper, initPaper, sendChatMessage, resetSession, getShowcasePapers, initShowcasePaper } from '../services/geminiService';
import type { Message, PaperInfo, PaperOption, ShowcasePaper } from '../types';
import ShowcasePapers from './ShowcasePapers';
import VoiceRecorder from './VoiceRecorder';
import {
  HighlightIcon,
  AtSymbolIcon,
  PlusCircleIcon,
  SparkleIcon,
  ArrowUpIcon,
} from './Icons';

interface ChatPanelProps {
  onPaperLoaded: (paperInfo: PaperInfo) => void;
  onShowPaper: () => void;
  isPaperVisible: boolean;
}

const WelcomeScreen: React.FC<{ 
  showcasePapers: ShowcasePaper[]; 
  onShowcaseSelect: (paper: ShowcasePaper) => void;
  isLoadingShowcase: boolean;
}> = ({ showcasePapers, onShowcaseSelect, isLoadingShowcase }) => (
  <div className="text-center py-12">
    <SparkleIcon className="mx-auto h-16 w-16 text-rose-500 mb-6" />
    <h2 className="text-3xl md:text-4xl font-bold text-slate-800 mb-4">Welcome to ArXini</h2>
    <p className="text-lg text-slate-600 mb-8">
      Deep Research, Decoded.
    </p>

    <div className="p-4 space-y-4 max-w-6xl mx-auto">
      {/* Showcase Papers */}
      <ShowcasePapers 
        papers={showcasePapers}
        onPaperSelect={onShowcaseSelect}
        isLoading={isLoadingShowcase}
      />
      
      <div className="bg-gradient-to-r from-rose-50 to-amber-50 border border-rose-200 rounded-2xl p-8 shadow-sm">
        <h3 className="font-semibold text-slate-800 mb-4 text-xl">Get Started</h3>
        <p className="text-base text-slate-700 mb-5">
          Enter the title or ArXiv ID of a research paper to analyze its code implementation.
        </p>
        <div className="bg-white rounded-lg p-4 text-left">
          <p className="text-sm text-slate-500 mb-3 uppercase tracking-wide">Example queries</p>
          <ul className="text-base text-slate-600 space-y-2">
            <li>• "Attention Is All You Need"</li>
            <li>• "1706.03762" (ArXiv ID)</li>
            <li>• "Graph Convolutional Networks"</li>
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <HighlightIcon className="h-7 w-7 text-rose-600 mb-3" />
          <h3 className="font-semibold text-gray-800 text-base">Gemini AI Search</h3>
          <p className="text-base text-gray-500 mt-1">Intelligent paper discovery using Gemini</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <AtSymbolIcon className="h-7 w-7 text-rose-600 mb-3" />
          <h3 className="font-semibold text-gray-800 text-base">Code Analysis</h3>
          <p className="text-base text-gray-500 mt-1">RAG-powered Q&A about implementations</p>
        </div>
      </div>
    </div>
  </div>
);

const LoadingStages = [
  "Thinking...",
];

const ChatPanel: React.FC<ChatPanelProps> = ({ onPaperLoaded, onShowPaper, isPaperVisible }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPaperInitialized, setIsPaperInitialized] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [currentPaper, setCurrentPaper] = useState<PaperInfo | null>(null);

  // NEW: Paper selection state
  const [awaitingPaperSelection, setAwaitingPaperSelection] = useState(false);
  const [paperOptions, setPaperOptions] = useState<PaperOption[]>([]);

  // NEW: Showcase papers state
  const [showcasePapers, setShowcasePapers] = useState<ShowcasePaper[]>([]);
  const [isLoadingShowcase, setIsLoadingShowcase] = useState(true);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load showcase papers on mount
  useEffect(() => {
    const loadShowcasePapers = async () => {
      setIsLoadingShowcase(true);
      try {
        const result = await getShowcasePapers();
        if (result.success && result.papers) {
          setShowcasePapers(result.papers);
        }
      } catch (error) {
        console.error('Failed to load showcase papers:', error);
      } finally {
        setIsLoadingShowcase(false);
      }
    };
    
    loadShowcasePapers();
  }, []);

  // Simulate loading stage progression
  useEffect(() => {
    if (isLoading && !isPaperInitialized && !awaitingPaperSelection) {
      const interval = setInterval(() => {
        setLoadingStage((prev) => (prev + 1) % LoadingStages.length);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isLoading, isPaperInitialized, awaitingPaperSelection]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user'
    };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      // STEP 1: User is selecting from paper options
      if (awaitingPaperSelection) {
        const selection = currentInput.trim();

        // Handle cancel
        if (selection.toLowerCase() === 'cancel') {
          setAwaitingPaperSelection(false);
          setPaperOptions([]);
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: "Paper selection cancelled. Start over with a new search.",
            sender: 'ai',
          };
          setMessages((prev) => [...prev, aiMessage]);
          setIsLoading(false);
          return;
        }

        // Try to handle as selection first
        const result = await selectPaper(selection);

        if (result.selected && result.arxiv_id) {
          // User picked a paper - show PDF immediately, then initialize
          setAwaitingPaperSelection(false);
          setPaperOptions([]);

          // Show PDF viewer IMMEDIATELY with the selected paper info
          if (result.pdf_url && result.title) {
            const paperInfo: PaperInfo = {
              title: result.title,
              arxiv_id: result.arxiv_id || '',
              authors: [],
              summary: '',
              pdf_url: result.pdf_url,
              published: '',
            };
            onPaperLoaded(paperInfo);
            onShowPaper();
          }

          const confirmMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `Great! The PDF is now displayed on the left.\n\nInitializing code analysis pipeline... (30-60 seconds)`,
            sender: 'ai',
          };
          setMessages((prev) => [...prev, confirmMessage]);

          // Initialize the pipeline with the ArXiv ID
          setLoadingStage(0);
          const initResult = await initPaper(result.arxiv_id);

          if (initResult.success && initResult.paper_info) {
            setIsPaperInitialized(true);
            setCurrentPaper(initResult.paper_info);
            // PDF is already showing, just update paper info
            onPaperLoaded(initResult.paper_info);

            const successMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: `✓ Code analysis complete! Indexed ${initResult.indexed_files} code files.\n\nAsk me anything about the implementation!`,
              sender: 'ai',
            };
            setMessages((prev) => [...prev, successMessage]);
          } else {
            const errorMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: initResult.message || 'Failed to initialize paper. Please try again.',
              sender: 'ai',
              isError: true,
            };
            setMessages((prev) => [...prev, errorMessage]);
          }
          setIsLoading(false);
          return;
        } else {
          // Invalid selection - treat as NEW search query instead
          setAwaitingPaperSelection(false);
          setPaperOptions([]);
          
          const infoMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: "Starting a new search for your query...",
            sender: 'ai',
          };
          setMessages((prev) => [...prev, infoMessage]);
          
          // Fall through to paper search logic below (don't return here)
        }
      }

      // STEP 2: First message - search for paper
      if (!isPaperInitialized) {
        const result = await searchPaper(currentInput);

        if (result.needs_selection && result.options) {
          // Got multiple options - ask user to select
          setAwaitingPaperSelection(true);
          setPaperOptions(result.options);

          // Short AI message (do not dump full option text)
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `Found ${result.options.length} papers. Which one would you like to analyze?`,
            sender: 'ai',
          };
          setMessages((prev) => [...prev, aiMessage]);
        } else if (result.success && result.paper) {
          // Direct match (ArXiv ID) - show PDF immediately, then initialize

          // Show PDF viewer IMMEDIATELY with the paper info
          if ((result.paper as any).pdf_url && result.paper.title) {
            const paperInfo: PaperInfo = {
              title: result.paper.title,
              arxiv_id: result.paper.arxiv_id,
              authors: [],
              summary: '',
              pdf_url: (result.paper as any).pdf_url,
              published: '',
            };
            onPaperLoaded(paperInfo);
            onShowPaper();
          }

          const confirmMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `${result.message}\n\nThe PDF is now displayed on the left.\n\nInitializing code analysis pipeline... (30-60 seconds)`,
            sender: 'ai',
          };
          setMessages((prev) => [...prev, confirmMessage]);

          setLoadingStage(0);
          const initResult = await initPaper(result.paper.arxiv_id);

          if (initResult.success && initResult.paper_info) {
            setIsPaperInitialized(true);
            setCurrentPaper(initResult.paper_info);
            // PDF is already showing, just update paper info
            onPaperLoaded(initResult.paper_info);

            const successMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: `✓ Code analysis complete! Indexed ${initResult.indexed_files} code files.\n\nAsk me anything about the implementation!`,
              sender: 'ai',
            };
            setMessages((prev) => [...prev, successMessage]);
          } else {
            const errorMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: initResult.message || 'Failed to initialize paper.',
              sender: 'ai',
              isError: true,
            };
            setMessages((prev) => [...prev, errorMessage]);
          }
        } else {
          // No results or error
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: result.message || 'Failed to find paper. Try a different query or ArXiv ID.',
            sender: 'ai',
            isError: true,
          };
          setMessages((prev) => [...prev, errorMessage]);
        }

        setIsLoading(false);
        return;
      }

      // STEP 3: Subsequent messages - Q&A about code
      const response = await sendChatMessage(currentInput);

      if (response.success && response.answer) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response.answer,
          sender: 'ai',
        };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response.message || 'Failed to get a response. Please try again.',
          sender: 'ai',
          isError: true,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm having trouble connecting right now. Please try again later.",
        sender: 'ai',
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetSession();
      setIsPaperInitialized(false);
      setCurrentPaper(null);
      setMessages([]);
      setInput('');
      setAwaitingPaperSelection(false);
      setPaperOptions([]);
    } catch (error) {
      console.error('Error resetting:', error);
    }
  };

  // Handler for showcase paper selection
  const handleShowcaseSelect = async (paper: ShowcasePaper) => {
    if (isLoading) return;
    setIsLoading(true);
    
    try {
      // Add user message showing which paper they selected
      const userMessage: Message = {
        id: Date.now().toString(),
        text: `Explore: ${paper.title}`,
        sender: 'user',
      };
      setMessages([userMessage]);
      
      // Initialize the showcase paper
      const result = await initShowcasePaper(paper.arxiv_id);
      
      if (result.success && result.paper_info) {
        setIsPaperInitialized(true);
        setCurrentPaper(result.paper_info);
        
        // Show PDF immediately
        onPaperLoaded(result.paper_info);
        onShowPaper();
        
        // Add success message
        const successMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `✓ Ready to explore "${paper.title}"!\n\nI've analyzed ${result.indexed_files || 'the'} code files. Ask me anything about the implementation!`,
          sender: 'ai',
        };
        setMessages((prev) => [...prev, successMessage]);
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: result.message || 'Failed to load showcase paper. Please try again.',
          sender: 'ai',
          isError: true,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error loading showcase paper:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm having trouble loading this paper. Please try again.",
        sender: 'ai',
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler for clicking the Select button on a paper option
  const handleSelectOption = async (index: number) => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const result = await selectPaper(index + 1);
        if (result.selected && result.arxiv_id) {
        setAwaitingPaperSelection(false);
        setPaperOptions([]);

        // Push a green confirmation message into chat
        const confirmMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `✓ Selected Paper: ${result.title}`,
          sender: 'ai',
        };
        setMessages((prev) => [...prev, confirmMessage]);

        // Show PDF viewer IMMEDIATELY with the selected paper info
        if (result.pdf_url && result.title) {
          const paperInfo: PaperInfo = {
            title: result.title,
            arxiv_id: result.arxiv_id || '',
            authors: [],
            summary: '',
            pdf_url: result.pdf_url,
            published: '',
          };
          onPaperLoaded(paperInfo);
          onShowPaper();
        }

        // Initialize pipeline
        setLoadingStage(0);
        const initResult = await initPaper(result.arxiv_id || '');
        if (initResult.success && initResult.paper_info) {
          setIsPaperInitialized(true);
          setCurrentPaper(initResult.paper_info);
          onPaperLoaded(initResult.paper_info);

          const successMessage: Message = {
            id: (Date.now() + 2).toString(),
            text: `✓ Code analysis complete! Indexed ${initResult.indexed_files} code files.\n\nAsk me anything about the implementation!`,
            sender: 'ai',
          };
          setMessages((prev) => [...prev, successMessage]);
        } else {
          const errorMessage: Message = {
            id: (Date.now() + 2).toString(),
            text: initResult.message || 'Failed to initialize paper. Please try again.',
            sender: 'ai',
            isError: true,
          };
          setMessages((prev) => [...prev, errorMessage]);
        }
      } else if (result.message) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: result.message,
          sender: 'ai',
          isError: !result.success,
        };
        setMessages((prev) => [...prev, aiMessage]);
      }
    } catch (err) {
      console.error('Select error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getPlaceholder = () => {
    if (awaitingPaperSelection) {
      return `Select 1-${paperOptions.length} or type "cancel"...`;
    }
    if (!isPaperInitialized) {
      return "Enter a paper title or ArXiv ID to get started...";
    }
    return "Ask about the code implementation...";
  };

  // Handler for voice transcription complete
  const handleVoiceTranscription = async (transcription: string) => {
    if (!transcription.trim() || isLoading) return;

    // Process the transcription directly (same as if user typed and clicked send)
    const userMessage: Message = {
      id: Date.now().toString(),
      text: transcription,
      sender: 'user',
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput(''); // Clear input
    setIsLoading(true);

    try {
      // STEP 1: User is selecting from paper options
      if (awaitingPaperSelection) {
        const selection = transcription.trim();

        // Handle cancel
        if (selection.toLowerCase() === 'cancel') {
          setAwaitingPaperSelection(false);
          setPaperOptions([]);
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: "Paper selection cancelled. Start over with a new search.",
            sender: 'ai',
          };
          setMessages((prev) => [...prev, aiMessage]);
          setIsLoading(false);
          return;
        }

        // Handle selection
        const result = await selectPaper(selection);

        if (result.selected && result.arxiv_id) {
          setAwaitingPaperSelection(false);
          setPaperOptions([]);

          const confirmMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `✓ Selected Paper: ${result.title}`,
            sender: 'ai',
          };
          setMessages((prev) => [...prev, confirmMessage]);

          if (result.pdf_url && result.title) {
            const paperInfo: PaperInfo = {
              title: result.title,
              arxiv_id: result.arxiv_id || '',
              authors: [],
              summary: '',
              pdf_url: result.pdf_url,
              published: '',
            };
            onPaperLoaded(paperInfo);
            onShowPaper();
          }

          setLoadingStage(0);
          const initResult = await initPaper(result.arxiv_id || '');
          if (initResult.success && initResult.paper_info) {
            setIsPaperInitialized(true);
            setCurrentPaper(initResult.paper_info);
            onPaperLoaded(initResult.paper_info);

            const successMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: `✓ Code analysis complete! Indexed ${initResult.indexed_files} code files.\n\nAsk me anything about the implementation!`,
              sender: 'ai',
            };
            setMessages((prev) => [...prev, successMessage]);
          } else {
            const errorMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: initResult.message || 'Failed to initialize paper. Please try again.',
              sender: 'ai',
              isError: true,
            };
            setMessages((prev) => [...prev, errorMessage]);
          }
        } else if (result.message) {
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: result.message,
            sender: 'ai',
            isError: !result.success,
          };
          setMessages((prev) => [...prev, aiMessage]);
        }

        setIsLoading(false);
        return;
      }

      // STEP 2: First message - search for paper
      if (!isPaperInitialized) {
        const result = await searchPaper(transcription);

        if (result.needs_selection && result.options) {
          setAwaitingPaperSelection(true);
          setPaperOptions(result.options);

          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `Found ${result.options.length} papers. Which one would you like to analyze?`,
            sender: 'ai',
          };
          setMessages((prev) => [...prev, aiMessage]);
        } else if (result.success && result.paper) {
          setLoadingStage(0);
          const initResult = await initPaper(result.paper.arxiv_id);

          if (initResult.success && initResult.paper_info) {
            setIsPaperInitialized(true);
            setCurrentPaper(initResult.paper_info);
            onPaperLoaded(initResult.paper_info);
            onShowPaper();

            const successMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: `✓ Code analysis complete! Indexed ${initResult.indexed_files} code files.\n\nAsk me anything about the implementation!`,
              sender: 'ai',
            };
            setMessages((prev) => [...prev, successMessage]);
          } else {
            const errorMessage: Message = {
              id: (Date.now() + 2).toString(),
              text: initResult.message || 'Failed to initialize paper. Please try again.',
              sender: 'ai',
              isError: true,
            };
            setMessages((prev) => [...prev, errorMessage]);
          }
        } else {
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: result.message || 'Failed to find paper. Try a different query or ArXiv ID.',
            sender: 'ai',
            isError: true,
          };
          setMessages((prev) => [...prev, errorMessage]);
        }

        setIsLoading(false);
        return;
      }

      // STEP 3: Subsequent messages - Q&A about code
      const response = await sendChatMessage(transcription);

      if (response.success && response.answer) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response.answer,
          sender: 'ai',
        };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response.message || 'Failed to get a response. Please try again.',
          sender: 'ai',
          isError: true,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm having trouble connecting right now. Please try again later.",
        sender: 'ai',
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex flex-col flex-1 h-screen bg-gradient-to-br from-slate-50 via-white to-rose-50/30 ${isPaperVisible ? 'lg:w-1/2' : 'w-full'}`}>
      <header className="flex-shrink-0 h-20 border-b border-slate-200 flex items-center justify-between px-6 bg-white/90 backdrop-blur shadow-sm">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 truncate">ArXini - Your AI research assistant</h1>
        </div>
        <div className="flex items-center gap-3">
          {currentPaper && !isPaperVisible && (
            <button
              onClick={onShowPaper}
              className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Show PDF
            </button>
          )}
          {isPaperInitialized && (
            <button
              onClick={handleReset}
              className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              New Paper
            </button>
          )}
          <div className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-white border border-gray-200 rounded-lg">
            <SparkleIcon className="w-4 h-4 text-blue-500" />
            <span className="text-slate-600">Powered by Gemini</span>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {messages.length === 0 && !isLoading && (
            <WelcomeScreen 
              showcasePapers={showcasePapers}
              onShowcaseSelect={handleShowcaseSelect}
              isLoadingShowcase={isLoadingShowcase}
            />
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
              {msg.sender === 'ai' && (
                <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-white shadow-md ${msg.isError ? 'bg-red-500' : 'bg-gradient-to-br from-rose-500 to-orange-500'}`}>
                  <SparkleIcon className="w-5 h-5" />
                </div>
              )}
              <div
                className={`max-w-2xl px-5 py-3.5 rounded-2xl shadow-sm ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-lg'
                    : msg.isError
                    ? 'bg-red-50 border border-red-200 text-red-800 rounded-bl-lg'
                    : 'bg-white border border-slate-200 text-slate-900 rounded-bl-lg'
                }`}
              >
                <p className="text-base leading-relaxed whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          ))}

          {/* Render clickable paper option cards when awaiting selection */}
          {awaitingPaperSelection && paperOptions.length > 0 && (
            <div className="mt-4 grid grid-cols-1 gap-3 max-w-5xl mx-auto">
              {paperOptions.map((opt, i) => (
                <div key={opt.index} className="flex items-start justify-between bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div className="text-base text-slate-500 font-semibold">{opt.index}.</div>
                      <div className="font-semibold text-slate-900 text-lg">{opt.title}</div>
                    </div>
                    <div className="text-base text-slate-700 mt-2 font-medium">{opt.authors}</div>
                    <div className="text-base text-blue-600 mt-1.5 hover:text-blue-800 transition-colors">
                      <a href={`https://arxiv.org/abs/${opt.arxiv_id}`} target="_blank" rel="noreferrer">arXiv:{opt.arxiv_id}</a>
                    </div>
                    {opt.summary && <div className="text-base text-slate-600 mt-2 leading-relaxed">{opt.summary}</div>}
                  </div>
                  <div className="flex flex-col items-end ml-4">
                    <button
                      onClick={() => handleSelectOption(i)}
                      disabled={isLoading}
                      className="px-5 py-2.5 text-base font-semibold text-white bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 shadow-sm transition-all"
                    >
                      Select
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {isLoading && (
            <div className="flex gap-3">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-rose-500 to-orange-500 flex items-center justify-center flex-shrink-0 text-white shadow-md">
                <SparkleIcon className="w-5 h-5 animate-pulse" />
              </div>
              <div className="max-w-2xl px-5 py-3.5 rounded-2xl bg-white border border-slate-200 text-slate-900 rounded-bl-lg shadow-sm">
                {!isPaperInitialized && !awaitingPaperSelection ? (
                  <div>
                    <p className="text-base font-medium text-slate-700 mb-2">
                      {LoadingStages[loadingStage]}
                    </p>
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-rose-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-rose-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-rose-400 rounded-full animate-bounce"></div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse"></div>
                  </div>
                )}
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      </main>

      <footer className="flex-shrink-0 p-4 bg-white/80 backdrop-blur border-t border-slate-200">
        <div className="max-w-5xl mx-auto">
          <form onSubmit={handleSendMessage} className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={getPlaceholder()}
              className="w-full pl-5 pr-28 py-4 bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm text-sm"
              disabled={isLoading}
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <VoiceRecorder
                onTranscriptionComplete={handleVoiceTranscription}
                isDisabled={isLoading}
              />
              <button
                type="submit"
                className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg flex items-center justify-center hover:from-blue-600 hover:to-blue-700 disabled:from-slate-300 disabled:to-slate-400 transition-all shadow-sm"
                disabled={!input.trim() || isLoading}
              >
                <ArrowUpIcon className="w-5 h-5 transform -rotate-90" />
              </button>
            </div>
          </form>
        </div>
      </footer>
    </div>
  );
};

export default ChatPanel;
