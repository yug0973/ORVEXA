const isProd = import.meta.env.PROD;

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || (isProd ? '' : 'http://localhost:8000');

export const getWebSocketUrl = (path: string): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  if (import.meta.env.VITE_WS_URL) {
    return `${import.meta.env.VITE_WS_URL}${path}`;
  }
  
  if (isProd) {
    return `${protocol}//${window.location.host}${path}`;
  }
  
  return `ws://localhost:8000${path}`;
};
