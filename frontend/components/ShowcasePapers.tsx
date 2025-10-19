// ShowcasePapers.tsx - Featured papers showcase on homepage

import React from 'react';
import type { ShowcasePaper } from '../types';
import { SparkleIcon } from './Icons';

interface ShowcasePapersProps {
  papers: ShowcasePaper[];
  onPaperSelect: (paper: ShowcasePaper) => void;
  isLoading?: boolean;
}

const ShowcasePapers: React.FC<ShowcasePapersProps> = ({ papers, onPaperSelect, isLoading }) => {
  if (papers.length === 0 && !isLoading) {
    return null;
  }

  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <SparkleIcon className="h-6 w-6 text-rose-500" />
        <h3 className="text-xl font-bold text-slate-800">Popular Papers</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading ? (
          // Loading skeleton
          <>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white border border-slate-200 rounded-xl p-5 animate-pulse">
                <div className="h-5 bg-slate-200 rounded w-3/4 mb-3"></div>
                <div className="h-4 bg-slate-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-slate-200 rounded w-full mb-2"></div>
                <div className="h-3 bg-slate-200 rounded w-5/6"></div>
              </div>
            ))}
          </>
        ) : (
          papers.map((paper) => (
            <button
              key={paper.id}
              onClick={() => onPaperSelect(paper)}
              className="bg-white border border-slate-200 rounded-xl p-5 text-left hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer group"
            >
              <h4 className="font-semibold text-slate-900 text-base mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
                {paper.title}
              </h4>
              <p className="text-sm text-slate-600 mb-2">
                {paper.authors.slice(0, 3).join(', ')}
                {paper.authors.length > 3 && ` +${paper.authors.length - 3} more`}
              </p>
              <p className="text-sm text-slate-500 line-clamp-2 mb-3">
                {paper.summary}
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs text-blue-600 font-medium">
                  arXiv:{paper.arxiv_id}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(paper.published).getFullYear()}
                </span>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
};

export default ShowcasePapers;
