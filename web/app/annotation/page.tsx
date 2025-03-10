"use client";

import { useEffect, useState } from 'react';
import { ArrowLeft } from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useExtraction } from "@/hooks/extraction";

interface ProcessedPaperData {
  title?: string;
  abstract?: string;
  content?: string;
  // Add other fields as needed
}

export default function AnnotationPage() {
  const router = useRouter();
  const { data, reset } = useExtraction();
  const [processedPaperData, setProcessedPaperData] = useState<ProcessedPaperData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Directly check localStorage first
    const savedData = localStorage.getItem('extractionData');
    console.log('Data in localStorage:', savedData); // Debug log

    let extractionData = null;
    if (savedData) {
      try {
        extractionData = JSON.parse(savedData);
        console.log('Parsed localStorage data:', extractionData);
      } catch (e) {
        console.error('Error parsing localStorage data:', e);
      }
    }

    // Use either the prop data or localStorage data
    const dataToProcess = data || extractionData;
    console.log('Data to process:', dataToProcess);

    if (!dataToProcess) {
      console.log('No data available, redirecting to home');
      router.push('/');
      return;
    }

    try {
      const processed = processPaperData(dataToProcess);
      console.log('Processed data:', processed);
      setProcessedPaperData(processed);
    } catch (error) {
      console.error('Error processing paper data:', error);
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  }, [data, router]);

  const handleBack = () => {
    reset(); // Reset the extraction state
    router.push('/');
  };

  const processPaperData = (data: any): ProcessedPaperData => {
    if (!data) return { title: '', abstract: '', content: '' };
    
    return {
      title: data.title || '',
      abstract: data.abstract || '',
      content: data.content || '',
      // Add other field transformations as needed
    };
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] text-white flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin h-8 w-8 border-4 border-zinc-400 border-t-transparent rounded-full mx-auto"></div>
          <p className="text-zinc-400">Loading paper data...</p>
        </div>
      </div>
    );
  }

  // Don't render anything if no data
  if (!processedPaperData) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">No Paper Data Found</h1>
          <p className="text-zinc-400">Please upload a paper first.</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-200 transition-colors"
          >
            Go Back Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col">
      {/* Back button */}
      <motion.button
        onClick={handleBack}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5, duration: 0.3 }}
        className="fixed top-6 left-6 p-3 rounded-full bg-zinc-800/50 hover:bg-zinc-800 transition-colors group z-50"
        aria-label="Go back to home"
      >
        <ArrowLeft 
          className="w-5 h-5 text-zinc-400 group-hover:text-zinc-300 transition-colors" 
          weight="bold"
        />
      </motion.button>

      {/* Main content */}
      <main className="flex-grow h-[calc(100vh-2rem)] overflow-y-scroll scrollbar-hide py-4 px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-xl font-bold mb-4">Raw Data:</h2>
          <pre className="bg-zinc-900 p-4 rounded-lg overflow-x-auto mb-8">
            {JSON.stringify(data || JSON.parse(localStorage.getItem('extractionData') || '{}'), null, 2)}
          </pre>

          <h2 className="text-xl font-bold mb-4">Processed Data:</h2>
          <pre className="bg-zinc-900 p-4 rounded-lg overflow-x-auto">
            {JSON.stringify(processedPaperData, null, 2)}
          </pre>
        </div>
      </main>
    </div>
  );
}