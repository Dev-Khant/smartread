import { useState, useEffect, useCallback, useRef } from 'react';

interface ExtractionData {
  status: string;
  message: string;
  data: {
    total_pages: number;
    page: any;
  };
  isPageChange?: boolean;
}

interface UseOptimizedExtractionReturn {
  extractFromUrl: (url: string) => Promise<ExtractionData>;
  changePage: (pageNumber: number) => Promise<ExtractionData>;
  loading: boolean;
  error: string | null;
  data: ExtractionData | null;
  reset: () => void;
  currentUrl: string | null;
  progress: number;
  retryCount: number;
}

export const useOptimizedExtraction = (): UseOptimizedExtractionReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ExtractionData | null>(() => {
    if (typeof window !== 'undefined') {
      const savedData = localStorage.getItem('extractionData');
      return savedData ? JSON.parse(savedData) : null;
    }
    return null;
  });
  const [currentUrl, setCurrentUrl] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('currentUrl');
    }
    return null;
  });
  const [progress, setProgress] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  
  // Refs for cleanup
  const abortControllerRef = useRef<AbortController | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
  }, []);

  // Persist data to localStorage
  useEffect(() => {
    if (data && !data.isPageChange) {
      localStorage.setItem('extractionData', JSON.stringify(data));
    }
  }, [data]);

  useEffect(() => {
    if (currentUrl) {
      localStorage.setItem('currentUrl', currentUrl);
    } else {
      localStorage.removeItem('currentUrl');
    }
  }, [currentUrl]);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  // Enhanced fetch function with retry logic and progress tracking
  const fetchWithRetry = async (
    url: string,
    pageNumber: number = 1,
    isPageChange: boolean = false,
    maxRetries: number = 3
  ): Promise<ExtractionData> => {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        // Cleanup previous request
        cleanup();
        
        // Create new abort controller
        abortControllerRef.current = new AbortController();
        
        setRetryCount(attempt);
        setProgress(0);
        
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/extract`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, page_number: pageNumber }),
            signal: abortControllerRef.current.signal,
          }
        );

        // Simulate progress for better UX
        const progressInterval = setInterval(() => {
          setProgress(prev => Math.min(prev + 10, 90));
        }, 200);

        if (!response.ok) {
          clearInterval(progressInterval);
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const fetchedData = await response.json();
        clearInterval(progressInterval);
        setProgress(100);
        
        // Add metadata
        const enhancedData = { ...fetchedData, isPageChange };
        setData(enhancedData);
        setError(null);
        setRetryCount(0);
        
        return enhancedData;
        
      } catch (err) {
        lastError = err as Error;
        
        // Don't retry if request was aborted
        if (lastError.name === 'AbortError') {
          throw lastError;
        }
        
        // Don't retry on client errors (4xx)
        if (lastError.message.includes('HTTP 4')) {
          throw lastError;
        }
        
        // Wait before retry with exponential backoff
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          await new Promise(resolve => {
            retryTimeoutRef.current = setTimeout(resolve, delay);
          });
        }
      }
    }
    
    // All retries failed
    throw lastError || new Error('Request failed after all retries');
  };

  // Optimized page change with debouncing
  const debouncedChangePage = useCallback(
    (() => {
      let timeoutId: NodeJS.Timeout;
      
      return async (pageNumber: number): Promise<ExtractionData> => {
        // Clear previous timeout
        clearTimeout(timeoutId);
        
        return new Promise((resolve, reject) => {
          timeoutId = setTimeout(async () => {
            try {
              if (!currentUrl) {
                throw new Error('No URL available for page change');
              }
              
              setLoading(true);
              setError(null);
              
              const result = await fetchWithRetry(currentUrl, pageNumber, true);
              resolve(result);
            } catch (err) {
              const error = err as Error;
              setError(error.message);
              setData(null);
              reject(error);
            } finally {
              setLoading(false);
              setProgress(0);
            }
          }, 300); // 300ms debounce
        });
      };
    })(),
    [currentUrl]
  );

  // Main extraction function
  const extractFromUrl = async (url: string): Promise<ExtractionData> => {
    try {
      setLoading(true);
      setError(null);
      setData(null);
      setProgress(0);
      
      // Clear previous data
      localStorage.removeItem('extractionData');
      setCurrentUrl(url);
      
      const result = await fetchWithRetry(url, 1, false);
      return result;
      
    } catch (err) {
      const error = err as Error;
      setError(error.message);
      setCurrentUrl(null);
      throw error;
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  // Reset function
  const reset = useCallback(() => {
    cleanup();
    setLoading(false);
    setError(null);
    setData(null);
    setCurrentUrl(null);
    setProgress(0);
    setRetryCount(0);
    localStorage.removeItem('extractionData');
    localStorage.removeItem('currentUrl');
  }, [cleanup]);

  // Preload next page for better UX
  const preloadNextPage = useCallback(async (currentPage: number, totalPages: number) => {
    if (currentPage < totalPages && currentUrl) {
      try {
        // Preload in background without updating state
        await fetchWithRetry(currentUrl, currentPage + 1, true, 1);
      } catch (err) {
        // Silently fail for preloading
        console.log('Preload failed:', err);
      }
    }
  }, [currentUrl]);

  return {
    extractFromUrl,
    changePage: debouncedChangePage,
    loading,
    error,
    data,
    reset,
    currentUrl,
    progress,
    retryCount,
  };
};
