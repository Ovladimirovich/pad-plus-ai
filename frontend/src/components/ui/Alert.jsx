export function Alert({ children, variant = 'default', className = '' }) {
  const variants = {
    default: 'bg-gray-800 border-gray-700 text-gray-300',
    destructive: 'bg-red-900/30 border-red-800 text-red-300',
    success: 'bg-green-900/30 border-green-800 text-green-300',
  };

  return (
    <div className={`px-4 py-3 rounded-lg border ${variants[variant] || variants.default} ${className}`} role="alert">
      {children}
    </div>
  );
}

export function AlertDescription({ children, className = '' }) {
  return <div className={`text-sm ${className}`}>{children}</div>;
}

export default Alert;
