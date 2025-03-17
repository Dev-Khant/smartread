import { useState, useEffect, useCallback } from 'react';

export const useExtraction = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentUrl, setCurrentUrl] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('currentUrl');
    }
    return null;
  });
  const [data, setData] = useState<any>(() => {
    if (typeof window !== 'undefined') {
      const savedData = localStorage.getItem('extractionData');
      return savedData ? JSON.parse(savedData) : null;
    }
    return null;
  });

  // Only update localStorage on initial data load or URL change
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

  // Common fetch function to avoid duplication
  const fetchData = async (url: string, pageNumber: number = 1, isPageChange: boolean = false) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, page_number: pageNumber }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process request');
      }

      const fetchedData = await response.json();
      setData({ ...fetchedData, isPageChange });
      return fetchedData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process request';
      setError(errorMessage);
      setData(null);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const debouncedChangePage = useCallback(async (pageNumber: number) => {
    if (!currentUrl) {
      const error = new Error('No URL available for page change');
      setError(error.message);
      throw error;
    }
    return fetchData(currentUrl, pageNumber, true);
  }, [currentUrl]);

  const extractFromUrl = async (url: string) => {
    try {
      setData(null);
      setError(null);
      localStorage.removeItem('extractionData');
      setCurrentUrl(url);
      return await fetchData(url, 1, false);
    } catch (err) {
      // Clear the URL if extraction fails
      setCurrentUrl(null);
      throw err;
    }
  };

  const reset = () => {
    setLoading(false);
    setError(null);
    setData(null);
    setCurrentUrl(null);
    localStorage.removeItem('extractionData');
    localStorage.removeItem('currentUrl');
  };

  return {
    extractFromUrl,
    changePage: debouncedChangePage,
    loading,
    error,
    data,
    reset,
    currentUrl
  };
};
