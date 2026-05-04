import React from 'react';

type Status = 'active' | 'idle' | 'offline' | 'open' | 'matched' | 'closed' | string;

interface BadgeProps {
  children: React.ReactNode;
  variant?: Status;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'offline', className = '' }) => {
  const getVariantStyles = (v: string) => {
    switch (v) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'idle':
        return 'bg-amber-100 text-amber-800';
      case 'offline':
      case 'closed':
        return 'bg-gray-100 text-gray-800';
      case 'open':
        return 'bg-blue-100 text-blue-800';
      case 'matched':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getVariantStyles(variant)} ${className}`}>
      {children}
    </span>
  );
};
