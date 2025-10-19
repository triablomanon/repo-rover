// Icons.tsx - Reusable icon components

import React from 'react';

export const SparkleIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path fillRule="evenodd" d="M9 4.5a.75.75 0 01.721.544l.813 2.846a3.75 3.75 0 002.84 2.84l2.846.813a.75.75 0 010 1.442l-2.846.813a3.75 3.75 0 00-2.84 2.84l-.813 2.846a.75.75 0 01-1.442 0l-.813-2.846a3.75 3.75 0 00-2.84-2.84l-2.846-.813a.75.75 0 010-1.442l2.846-.813a3.75 3.75 0 002.84-2.84l.813-2.846A.75.75 0 019 4.5zM18 1.5a.75.75 0 01.728.568l.258 1.036a.75.75 0 00.54.54l1.036.258a.75.75 0 010 1.456l-1.036.258a.75.75 0 00-.54.54l-.258 1.036a.75.75 0 01-1.456 0l-.258-1.036a.75.75 0 00-.54-.54l-1.036-.258a.75.75 0 010-1.456l1.036-.258a.75.75 0 00.54-.54l.258-1.036A.75.75 0 0118 1.5zM16.5 15a.75.75 0 01.712.551l.57 2.12a.75.75 0 00.528.528l2.12.57a.75.75 0 010 1.424l-2.12.57a.75.75 0 00-.528.528l-.57 2.12a.75.75 0 01-1.424 0l-.57-2.12a.75.75 0 00-.528-.528l-2.12-.57a.75.75 0 010-1.424l2.12-.57a.75.75 0 00.528-.528l.57-2.12A.75.75 0 0116.5 15z" clipRule="evenodd" />
  </svg>
);

export const HighlightIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M19.53 6.03l-4.5-4.5a.75.75 0 00-1.06 0l-9 9a.75.75 0 000 1.06l4.5 4.5a.75.75 0 001.06 0l9-9a.75.75 0 000-1.06zM9 13.06L5.94 10 10.5 5.44 13.56 8.5 9 13.06zM21 16.5a.75.75 0 00-1.5 0v3a.75.75 0 01-.75.75H3.75a.75.75 0 01-.75-.75V3.75A.75.75 0 013.75 3h3a.75.75 0 000-1.5h-3A2.25 2.25 0 001.5 3.75v16.5A2.25 2.25 0 003.75 22.5h16.5A2.25 2.25 0 0022.5 20.25v-3.75z" />
  </svg>
);

export const AtSymbolIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zM12.75 9a.75.75 0 00-1.5 0v5.69l-1.826-.913a.75.75 0 10-.692 1.384l3.326 1.663a.75.75 0 00.692 0l3.326-1.663a.75.75 0 10-.692-1.384l-1.826.913V9z" clipRule="evenodd" />
    <path d="M12 21.75a9.75 9.75 0 100-19.5 9.75 9.75 0 000 19.5zM15.53 9.47a.75.75 0 00-1.06 0l-3 3a.75.75 0 101.06 1.06l1.72-1.72v4.19a.75.75 0 001.5 0v-5.25a.75.75 0 00-.75-.75h-5.25a.75.75 0 000 1.5h4.19l-1.72 1.72a.75.75 0 101.06 1.06l3-3a.75.75 0 000-1.06z" />
    <path d="M12 1.5c-5.798 0-10.5 4.702-10.5 10.5s4.702 10.5 10.5 10.5 10.5-4.702 10.5-10.5S17.798 1.5 12 1.5zm0 1.5c4.97 0 9 4.03 9 9s-4.03 9-9 9-9-4.03-9-9 4.03-9 9-9zm0 1.5a7.5 7.5 0 100 15 7.5 7.5 0 000-15zm0 1.5a6 6 0 110 12 6 6 0 010-12z" />
    <path d="M12 10.5a.75.75 0 01.75.75v6a.75.75 0 01-1.5 0v-6a.75.75 0 01.75-.75z" />
    <path d="M12 7.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3z" />
    <path d="M12 10.5a1 1 0 100-2 1 1 0 000 2zm0 1.5a2.5 2.5 0 110-5 2.5 2.5 0 010 5z" />
    <path d="M12 12c.966 0 1.75-.784 1.75-1.75S12.966 8.5 12 8.5s-1.75.784-1.75 1.75S11.034 12 12 12zm0-1.5c.138 0 .25.112.25.25S12.138 11 12 11s-.25-.112-.25-.25S11.862 10.5 12 10.5z" />
    <path fillRule="evenodd" d="M12 21a9 9 0 100-18 9 9 0 000 18zm0-1.5a7.5 7.5 0 100-15 7.5 7.5 0 000 15z" clipRule="evenodd" />
    <path d="M13.5 10.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
    <path d="M12 12a1 1 0 110-2 1 1 0 010 2z" />
    <path fillRule="evenodd" d="M12 1.5a10.5 10.5 0 100 21 10.5 10.5 0 000-21zM3 12a9 9 0 1118 0 9 9 0 01-18 0z" clipRule="evenodd" />
    <path fillRule="evenodd" d="M12 14.25a.75.75 0 01-.75.75H10.5a2.25 2.25 0 00-2.25 2.25v.75a.75.75 0 01-1.5 0v-.75A3.75 3.75 0 0110.5 15h.75a.75.75 0 01.75.75zm0-8.25A3.375 3.375 0 108.625 9.375 3.375 3.375 0 0012 6zM10.125 9.375a1.875 1.875 0 113.75 0 1.875 1.875 0 01-3.75 0z" clipRule="evenodd" />
    <path fillRule="evenodd" d="M16.5 8.25a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM12 10.5a2.25 2.25 0 100-4.5 2.25 2.25 0 000 4.5z" clipRule="evenodd" />
  </svg>
);


export const PlusCircleIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zM12.75 9a.75.75 0 00-1.5 0v2.25H9a.75.75 0 000 1.5h2.25V15a.75.75 0 001.5 0v-2.25H15a.75.75 0 000-1.5h-2.25V9z" clipRule="evenodd" />
  </svg>
);

export const PaperClipIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path fillRule="evenodd" d="M18.97 3.659a2.25 2.25 0 00-3.182 0l-10.121 10.121a2.25 2.25 0 000 3.182a2.25 2.25 0 003.182 0L19.5 9.404a.75.75 0 011.06 1.06l-7.667 7.667a3.75 3.75 0 11-5.303-5.303l10.121-10.121a3.75 3.75 0 015.303 5.303L6.904 21.318a.75.75 0 11-1.06-1.06l12.126-12.126a2.25 2.25 0 00-3.182-3.182L3.682 15.07a.75.75 0 01-1.06-1.06L13.743 2.888a2.25 2.25 0 013.182 0L18 4.009a.75.75 0 011.06-1.06l-.09-.09z" clipRule="evenodd" />
  </svg>
);

export const ClockIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zM12.75 6a.75.75 0 00-1.5 0v6c0 .414.336.75.75.75h4.5a.75.75 0 000-1.5h-3.75V6z" clipRule="evenodd" />
  </svg>
);

export const ArrowUpIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M12 4.5a.75.75 0 01.75.75v12.55l3.47-3.47a.75.75 0 111.06 1.06l-4.5 4.5a.75.75 0 01-1.06 0l-4.5-4.5a.75.75 0 111.06-1.06L11.25 17.8V5.25a.75.75 0 01.75-.75z" />
  </svg>
);

export const MicrophoneIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
    <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.75 6.75 0 01-6 6.705V21h2.25a.75.75 0 010 1.5h-6a.75.75 0 010-1.5H11.25v-2.295A6.75 6.75 0 015.25 12v-1.5a.75.75 0 01.75-.75z" />
  </svg>
);
