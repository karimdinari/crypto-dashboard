// Import all asset images
import bitcoinImg from '@/assets/bitcoin.png';
import ethereumImg from '@/assets/etheruem.png';
import eurusdImg from '@/assets/EURUSD.png';
import gbpusdImg from '@/assets/GBPUSD.png';
import goldImg from '@/assets/gold.png';
import silverImg from '@/assets/silver.png';

// Map symbols to their images
export const ASSET_IMAGES: Record<string, string> = {
  'BTC/USD': bitcoinImg,
  'BTC': bitcoinImg,
  'ETH/USD': ethereumImg,
  'ETH': ethereumImg,
  'EUR/USD': eurusdImg,
  'EUR': eurusdImg,
  'EURUSD': eurusdImg,
  'GBP/USD': gbpusdImg,
  'GBP': gbpusdImg,
  'GBPUSD': gbpusdImg,
  'XAU/USD': goldImg,
  'XAU': goldImg,
  'GOLD': goldImg,
  'XAG/USD': silverImg,
  'XAG': silverImg,
  'XAG XAGUSD': silverImg,
  'SILVER': silverImg,
};

// Get image for a symbol
export const getAssetImage = (symbol: string): string | undefined => {
  // Try direct match first
  if (ASSET_IMAGES[symbol]) {
    return ASSET_IMAGES[symbol];
  }
  
  // Try extracting the first part (before space)
  const basePart = symbol.split(' ')[0];
  if (ASSET_IMAGES[basePart]) {
    return ASSET_IMAGES[basePart];
  }
  
  // Try splitting by slash
  const slashPart = symbol.split('/')[0];
  if (ASSET_IMAGES[slashPart]) {
    return ASSET_IMAGES[slashPart];
  }
  
  return undefined;
};

// Get a fallback color for assets without images
export const getAssetColor = (symbol: string): string => {
  const colors: Record<string, string> = {
    'BTC': 'bg-orange-500/10 border-orange-500/20',
    'ETH': 'bg-purple-500/10 border-purple-500/20',
    'EUR': 'bg-blue-500/10 border-blue-500/20',
    'GBP': 'bg-red-500/10 border-red-500/20',
    'XAU': 'bg-yellow-500/10 border-yellow-500/20',
    'XAG': 'bg-gray-500/10 border-gray-500/20',
  };
  const key = symbol.split('/')[0];
  return colors[key] || 'bg-primary/10 border-primary/20';
};
