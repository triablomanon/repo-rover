// ChatPanel.tsx - Chat interface component for Repo Rover

import React, { useState, useRef, useEffect } from 'react';
import { searchPaper, selectPaper, initPaper, sendChatMessage, resetSession } from '../services/geminiService';
import type { Message, PaperInfo, PaperOption } from '../types';
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

const WelcomeScreen: React.FC = () => (
  <div className="text-center py-10">
    <SparkleIcon className="mx-auto h-12 w-12 text-rose-500 mb-6" />
    <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome to Repo Rover</h2>
    <p className="text-gray-600 mb-8">
      From research paper to running code in 60 seconds
    </p>

    <div className="p-4 space-y-4 max-w-2xl mx-auto">
      <div className="bg-gradient-to-r from-rose-50 to-pink-50 border border-rose-200 rounded-xl p-6">
        <h3 className="font-semibold text-gray-800 mb-2 text-lg">Get Started</h3>
        <p className="text-sm text-gray-700 mb-4">
          Enter the title or ArXiv ID of a research paper to analyze its code implementation.
        </p>
        <div className="bg-white rounded-lg p-3 text-left">
          <p className="text-xs text-gray-500 mb-1">Example queries:</p>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• "Attention Is All You Need"</li>
            <li>• "1706.03762" (ArXiv ID)</li>
            <li>• "Graph Convolutional Networks"</li>
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <HighlightIcon className="h-6 w-6 text-rose-600 mb-2" />
          <h3 className="font-semibold text-gray-800">Gemini AI Search</h3>
          <p className="text-sm text-gray-500">Intelligent paper discovery using Gemini</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <AtSymbolIcon className="h-6 w-6 text-rose-600 mb-2" />
          <h3 className="font-semibold text-gray-800">Code Analysis</h3>
          <p className="text-sm text-gray-500">RAG-powered Q&A about implementations</p>
        </div>
      </div>
    </div>
  </div>
);

const LoadingStages = [
  "Finding paper...",
  "Locating code repository...",
  "Cloning repository...",
  "Indexing code with ChromaDB...",
  "Initializing query pipeline...",
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

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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

        // Handle selection
        const result = await selectPaper(selection);

        if (result.selected && result.arxiv_id) {
          // User picked a paper - show PDF immediately, then initialize
          setAwaitingPaperSelection(false);
          setPaperOptions([]);

          // Show PDF viewer IMMEDIATELY with the selected paper info
          if (result.pdf_url && result.title) {
            const paperInfo = {
              title: result.title,
              arxiv_id: result.arxiv_id,
              pdf_url: result.pdf_url,
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
        } else if (result.message) {
          // Error or other response
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
        const result = await searchPaper(currentInput);

        if (result.needs_selection && result.options) {
          // Got multiple options - ask user to select
          setAwaitingPaperSelection(true);
          setPaperOptions(result.options);

          const optionsText = result.options.map(opt =>
            `${opt.index}. **${opt.title}**\n   ${opt.authors}\n   ArXiv: ${opt.arxiv_id}`
          ).join('\n\n');

          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: `${result.message}\n\n${optionsText}\n\nReply with the number (1-${result.options.length}) or type "cancel".`,
            sender: 'ai',
          };
          setMessages((prev) => [...prev, aiMessage]);
        } else if (result.success && result.paper) {
          // Direct match (ArXiv ID) - show PDF immediately, then initialize

          // Show PDF viewer IMMEDIATELY with the paper info
          if (result.paper.pdf_url && result.paper.title) {
            const paperInfo = {
              title: result.paper.title,
              arxiv_id: result.paper.arxiv_id,
              pdf_url: result.paper.pdf_url,
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
        let answerText = response.answer;

        // Add source info if available
        if (response.num_sources && response.num_sources > 0) {
          answerText += `\n\n*Based on ${response.num_sources} code snippet${response.num_sources > 1 ? 's' : ''} (confidence: ${response.confidence})*`;
        }

        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: answerText,
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

  const getPlaceholder = () => {
    if (awaitingPaperSelection) {
      return `Select 1-${paperOptions.length} or type "cancel"...`;
    }
    if (!isPaperInitialized) {
      return "Enter a paper title or ArXiv ID to get started...";
    }
    return "Ask about the code implementation...";
  };

  return (
    <div className={`flex flex-col h-screen bg-gray-50/50 ${isPaperVisible ? 'w-1/2' : 'w-full max-w-4xl mx-auto'}`}>
      <header className="flex-shrink-0 h-16 border-b border-gray-200 flex items-center justify-between px-6">
        <div>
          <h1 className="font-semibold text-lg">Repo Rover</h1>
          {currentPaper && (
            <p className="text-xs text-gray-500 truncate max-w-md">{currentPaper.title}</p>
          )}
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
            <span>Gemini 2.5 Flash</span>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        <div className="space-y-6">
          {messages.length === 0 && !isLoading && <WelcomeScreen />}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
              {msg.sender === 'ai' && (
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white ${msg.isError ? 'bg-red-500' : 'bg-rose-500'}`}>
                  <SparkleIcon className="w-5 h-5" />
                </div>
              )}
              <div
                className={`max-w-lg px-4 py-3 rounded-2xl ${
                  msg.sender === 'user'
                    ? 'bg-blue-500 text-white rounded-br-lg'
                    : msg.isError
                    ? 'bg-red-50 border border-red-200 text-red-800 rounded-bl-lg'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-lg'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-rose-500 flex items-center justify-center flex-shrink-0 text-white">
                <SparkleIcon className="w-5 h-5 animate-pulse" />
              </div>
              <div className="max-w-lg px-4 py-3 rounded-2xl bg-white border border-gray-200 text-gray-800 rounded-bl-lg">
                {!isPaperInitialized && !awaitingPaperSelection ? (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      {LoadingStages[loadingStage]}
                    </p>
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-rose-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-rose-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-rose-400 rounded-full animate-bounce"></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">This may take 30-60 seconds...</p>
                  </div>
                ) : (
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                  </div>
                )}
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      </main>

      <footer className="flex-shrink-0 p-4 bg-gray-50/50">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSendMessage} className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={getPlaceholder()}
              className="w-full pl-4 pr-14 py-3 bg-white border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 bg-gray-800 text-white rounded-lg flex items-center justify-center hover:bg-gray-900 disabled:bg-gray-300 transition-colors"
              disabled={!input.trim() || isLoading}
            >
              <ArrowUpIcon className="w-5 h-5 transform -rotate-90" />
            </button>
          </form>
        </div>
      </footer>
    </div>
  );
};

export default ChatPanel;
