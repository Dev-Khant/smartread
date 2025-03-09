import { Mistral } from '@mistralai/mistralai';
import { useState, useEffect } from 'react';

export const useExtraction = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(() => {
    // Initialize data from localStorage if available
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('extractionData');
      return saved ? JSON.parse(saved) : null;
    }
    return null;
  });

  // Update localStorage when data changes
  useEffect(() => {
    if (data) {
      localStorage.setItem('extractionData', JSON.stringify(data));
    } else {
      localStorage.removeItem('extractionData');
    }
  }, [data]);

  const extractFromUrl = async (url: string) => {
    try {
      setLoading(true);
      setError(null);
      setData(null); // Reset data before new extraction
      localStorage.removeItem('extractionData'); // Clear stored data
      
      const apiKey = process.env.NEXT_PUBLIC_MISTRAL_API_KEY;
      if (!apiKey) {
        throw new Error('Mistral API key is not configured');
      }

      const client = new Mistral({ apiKey });

      // First check if the URL is valid
      try {
        new URL(url);
      } catch {
        throw new Error('Invalid URL provided');
      }

      const ocrResponse = await client.ocr.process({
        model: "mistral-ocr-latest",
        document: {
          type: "document_url",
          documentUrl: url
        },
        includeImageBase64: true
      });

      if (!ocrResponse) {
        throw new Error('No response received from Mistral API');
      }

      console.log(ocrResponse);
      setData(ocrResponse);
      return ocrResponse;
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
