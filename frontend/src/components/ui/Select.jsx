import { useState, useRef, useEffect, createContext, useContext } from 'react';

const SelectContext = createContext(null);

export const Select = ({ children, value, onValueChange, className = '' }) => {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
      <div ref={containerRef} className={`relative ${className}`}>
        {children}
      </div>
    </SelectContext.Provider>
  );
};

export const SelectTrigger = ({ children, className = '' }) => {
  const ctx = useContext(SelectContext);

  return (
    <div className="cursor-pointer" onClick={() => ctx?.setOpen?.(!ctx?.open)}>
      <div className={`
        w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white
        flex items-center justify-between gap-2
        hover:border-gray-600
        focus-within:ring-2 focus-within:ring-blue-500/50 focus-within:border-blue-500
        transition-colors
        ${className}
      `}>
        {children}
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${ctx?.open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
};

export const SelectValue = ({ placeholder, className = '' }) => {
  const ctx = useContext(SelectContext);
  const display = ctx?.value || placeholder || 'Выбрать...';
  return <span className={`${ctx?.value ? 'text-white' : 'text-gray-500'} ${className}`}>{display}</span>;
};

export const SelectContent = ({ children, className = '' }) => {
  const ctx = useContext(SelectContext);
  if (!ctx?.open) return null;

  return (
    <div className={`
      absolute top-full left-0 right-0 mt-1 z-50 max-h-60 overflow-y-auto
      bg-gray-900 border border-gray-700 rounded-lg shadow-lg
      ${className}
    `}>
      {children}
    </div>
  );
};

export const SelectItem = ({ children, value, className = '' }) => {
  const ctx = useContext(SelectContext);
  const isActive = ctx?.value === value;

  const handleClick = () => {
    ctx?.onValueChange?.(value);
    ctx?.setOpen?.(false);
  };

  return (
    <div
      onClick={handleClick}
      className={`
        px-3 py-2 text-sm cursor-pointer transition-colors
        ${isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'}
        ${className}
      `}
    >
      {children}
    </div>
  );
};
