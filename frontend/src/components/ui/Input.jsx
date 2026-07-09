import { forwardRef } from 'react';

export const Input = forwardRef(({ className = '', type = 'text', ...props }, ref) => {
  return (
    <input
      ref={ref}
      type={type}
      className={`
        w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white
        placeholder:text-gray-500
        focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors
        ${className}
      `}
      {...props}
    />
  );
});

Input.displayName = 'Input';