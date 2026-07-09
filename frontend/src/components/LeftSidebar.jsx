import { useState } from 'react';

export function LeftSidebar({ isOpen, onToggle }) {
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed left-0 top-1/2 -translate-y-1/2 z-40 bg-[#1F2937] text-white p-2 rounded-r-lg hover:bg-[#374151] transition-colors"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    );
  }

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-[#111827] border-r border-[#1F2937] z-40 flex flex-col transition-transform duration-300">
      <div className="p-4 border-b border-[#1F2937] flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Меню</h2>
        <button
          onClick={onToggle}
          className="p-1 hover:bg-[#1F2937] rounded-lg transition-colors"
        >
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </aside>
  );
}
