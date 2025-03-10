import { useState, useEffect } from 'react';

export const useExtraction = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(() => {
    // Try to load initial data from localStorage
    if (typeof window !== 'undefined') {
      const savedData = localStorage.getItem('extractionData');
      return savedData ? JSON.parse(savedData) : null;
    }
    return null;
  });

  // Update localStorage when data changes
  useEffect(() => {
    if (data) {
      localStorage.setItem('extractionData', JSON.stringify(data));
    }
  }, [data]);

  const extractFromUrl = async (url: string) => {
    try {
      setLoading(true);
      setError(null);
      setData(null); // Reset data before new extraction
      localStorage.removeItem('extractionData'); // Clear previous data

      // Call the backend API
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to extract content');
      }

      const extractedData = await response.json();
      console.log(extractedData);
      setData(extractedData);
      return extractedData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to extract content';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setLoading(false);
    setError(null);
    setData(null);
    localStorage.removeItem('extractionData');
  };

  return {
    extractFromUrl,
    loading,
    error,
    data,
    reset
  };
};
