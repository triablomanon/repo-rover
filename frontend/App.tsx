// App.tsx - Main application component

import React, { useState } from 'react';
import PdfViewer from './components/PdfViewer';
import ChatPanel from './components/ChatPanel';
import type { PaperInfo } from './types';

const App: React.FC = () => {
  const [isPaperVisible, setIsPaperVisible] = useState(false);
  const [paperInfo, setPaperInfo] = useState<PaperInfo | null>(null);

  const handlePaperLoaded = (info: PaperInfo) => {
    setPaperInfo(info);
  };

  const handleShowPaper = () => {
    setIsPaperVisible(true);
  };

  const handleHidePaper = () => {
    setIsPaperVisible(false);
  };

  return (
    <div className="flex h-screen bg-white font-sans text-gray-900">
      {isPaperVisible && paperInfo && <PdfViewer pdfUrl={paperInfo.pdf_url} title={paperInfo.title} onClose={handleHidePaper} />}
      <ChatPanel
        onPaperLoaded={handlePaperLoaded}
        onShowPaper={handleShowPaper}
        isPaperVisible={isPaperVisible}
      />
    </div>
  );
};

export default App;
