export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatBandwidth = (bandwidth?: number): string => {
  if (!bandwidth) return 'Unlimited';
  return formatBytes(bandwidth) + '/s';
};

export const parseBandwidth = (value: string): number | undefined => {
  if (!value || value.toLowerCase() === 'unlimited') return undefined;
  
  const match = value.match(/^(\d+(?:\.\d+)?)\s*([kmgtpKMGTP])?[bB]?$/);
  if (!match) return undefined;
  
  const num = parseFloat(match[1]);
  const unit = match[2]?.toUpperCase() || '';
  
  const multipliers: Record<string, number> = {
    '': 1,
    'K': 1024,
    'M': 1024 * 1024,
    'G': 1024 * 1024 * 1024,
    'T': 1024 * 1024 * 1024 * 1024,
    'P': 1024 * 1024 * 1024 * 1024 * 1024,
  };
  
  return Math.floor(num * (multipliers[unit] || 1));
};