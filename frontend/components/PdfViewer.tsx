// PdfViewer.tsx - PDF viewer component for research papers

import React from 'react';

interface PdfViewerProps {
  pdfUrl: string;
  title: string;
  onClose?: () => void;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ pdfUrl, title, onClose }) => {
  return (
    <div className="w-1/2 flex-shrink-0 border-r border-gray-200 flex flex-col h-screen">
      <div className="flex-shrink-0 h-16 bg-gray-50 border-b border-gray-200 flex items-center justify-between px-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-sm font-medium truncate max-w-md" title={title}>
            {title}
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
          >
            Open PDF
          </a>
          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              title="Hide PDF viewer"
            >
              Hide PDF
            </button>
          )}
        </div>
      </div>
      <div className="flex-grow overflow-hidden bg-gray-100">
        <iframe
          src={pdfUrl}
          className="w-full h-full"
          title={title}
        />
      </div>
    </div>
  );
};

export default PdfViewer;
