import { getAssetImage, getAssetColor } from '@/lib/assetImages';

interface AssetImageProps {
  symbol: string;
  name?: string;
  size?: 'xxs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showBorder?: boolean;
}

const sizeClasses = {
  xxs: 'w-4 h-4',
  xs: 'w-6 h-6',
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
  xl: 'w-24 h-24',
};

export const AssetImage = ({
  symbol,
  name,
  size = 'md',
  className = '',
  showBorder = true,
}: AssetImageProps) => {
  const imageUrl = getAssetImage(symbol);
  const colorBg = getAssetColor(symbol);
  const sizeClass = sizeClasses[size];

  if (imageUrl) {
    return (
      <img
        src={imageUrl}
        alt={name || symbol}
        className={`${sizeClass} object-cover rounded-lg ${
          showBorder ? 'border border-border' : ''
        } ${className}`}
        title={name || symbol}
      />
    );
  }

  // Fallback: colored badge with symbol
  const shortSymbol = symbol.split('/')[0].slice(0, 3).toUpperCase();
  return (
    <div
      className={`${sizeClass} ${colorBg} rounded-lg border flex items-center justify-center font-semibold text-xs ${className}`}
      title={name || symbol}
    >
      {shortSymbol}
    </div>
  );
};
