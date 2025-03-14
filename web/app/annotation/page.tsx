"use client";

import { useEffect, useState, useRef, useCallback } from 'react';
import { ArrowLeft } from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useExtraction } from "@/hooks/extraction";
import { PaperContent } from "@/components/PaperContent";
import { ResourceDisplay } from "@/components/ResourceDisplay";
import { PageScrollBar } from "@/components/PageScrollBar";

interface Resource {
  title: string;
  link: string;
  snippet?: string;
  imageUrl?: string;
  image_url?: string;
  duration?: string;
}

interface ProcessedPaperData {
  title?: string;
  abstract?: string;
  content?: string;
  total_pages?: number;
  page?: {
    index: number;
    content: string;
    images?: Array<{
      id: string;
      image_url: string;
    }>;
    resources?: {
      [key: string]: {
        articles: Resource[];
        videos: Resource[] | { searchParameters: any; credits: number };
      };
    };
  };
}

export default function AnnotationPage() {
  const router = useRouter();
  const { data, reset, changePage, loading, currentUrl } = useExtraction();
  const [processedPaperData, setProcessedPaperData] = useState<ProcessedPaperData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [selectedHighlight, setSelectedHighlight] = useState<string | null>(null);
  const [currentPageNumber, setCurrentPageNumber] = useState(1);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const mainContentRef = useRef<HTMLDivElement>(null);
  const [totalPages, setTotalPages] = useState(0);
  const [content, setContent] = useState('');

  // Process resources to handle both regular video arrays and search parameter objects
  const processResources = (index: string) => {
    if (!processedPaperData?.page?.resources || !processedPaperData.page.resources[index]) {
      return { articles: [], videos: [] };
    }

    const resourceData = processedPaperData.page.resources[index];
    const videos = Array.isArray(resourceData.videos) 
      ? resourceData.videos 
      : [];

    return {
      articles: resourceData.articles || [],
      videos
    };
  };

  // Handle initial data loading
  useEffect(() => {
    const loadInitialData = () => {
      if (data) {
        // Only update page number if this is not a page change
        if (!data.isPageChange) {
          setCurrentPageNumber(1);
        }
        setTotalPages(data.total_pages);
        setContent(data.content);
        
        try {
          const processed = processPaperData(data);
          setProcessedPaperData(processed);
          setInitialLoadDone(true);
        } catch (error) {
          console.error('Error processing paper data:', error);
        } finally {
          // Make sure to turn off loading once data is processed
          setIsLoading(false);
        }
      }
    };

    loadInitialData();
  }, [data]);

  // Sync with extraction loading state
  useEffect(() => {
    setIsLoading(loading);
  }, [loading]);

  const handleBack = () => {
    reset();
    router.push('/');
  };

  const processPaperData = (data: any): ProcessedPaperData => {
    if (!data?.data) return { title: '', abstract: '', content: '' };
    return {
      total_pages: data.data.total_pages,
      page: {
        ...data.data.page,
        resources: data.data.page.resources,
      },
    };
  };

  const handlePageChange = useCallback(async (pageNumber: number) => {
    try {
      console.log('AnnotationPage: Handling page change to:', pageNumber);
      if (pageNumber === currentPageNumber || pageNumber < 1 || pageNumber > (processedPaperData?.total_pages || 1)) {
        console.log('AnnotationPage: Invalid page number or same page, skipping');
        return;
      }
      
      // Update page number immediately to prevent UI jumps
      // This is crucial for the scrollbar to maintain its position
      setCurrentPageNumber(pageNumber);
      
      // Store current page in localStorage for persistence
      localStorage.setItem('currentPage', pageNumber.toString());
      
      // Create a loading timeout that will only show loading state if operation takes too long
      const loadingTimeout = setTimeout(() => {
        setIsLoading(true);
      }, 300);
      
      console.log('AnnotationPage: Calling changePage');
      const newData = await changePage(pageNumber);
      
      // Clear the loading timeout if data loaded quickly
      clearTimeout(loadingTimeout);
      
      if (newData) {
        console.log('AnnotationPage: Got new data, processing');
        const processed = processPaperData(newData);
        setProcessedPaperData(processed);
        
        // Smooth scroll to top
        if (mainContentRef.current) {
          mainContentRef.current.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        console.log('AnnotationPage: Page change complete');
      }
    } catch (error) {
      console.error('AnnotationPage: Error changing page:', error);
      throw error;
    } finally {
      // Small delay before removing loading state for smoother transitions
      setTimeout(() => {
        setIsLoading(false);
      }, 100);
    }
  }, [currentPageNumber, processedPaperData?.total_pages, changePage]);

const handleDownload = async () => {
  if (!currentUrl) return;
  try {
    setIsDownloading(true);
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/pdf/download`, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ pdf_url: currentUrl }),
    });
    if (response.ok) {
      const result = await response.json();
      if (result.status === 'success' && result.data.pdf_url) {
        window.open(result.data.pdf_url, '_blank');
      } else {
        console.error('Failed to download PDF');
      }
    } else {
      console.error('Failed to download PDF');
    }
  } catch (error) {
    console.error('Error downloading PDF:', error);
  } finally {
    setIsDownloading(false);
  }
};

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
  console.log("currentPageNumber", currentPageNumber);

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col">
      <motion.button
        onClick={handleBack}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5, duration: 0.3 }}
        className={`fixed top-6 left-6 p-3 rounded-full bg-zinc-800/50 hover:bg-zinc-800 transition-colors group z-50 ${selectedHighlight ? 'opacity-70 hover:opacity-75' : ''}`}
        aria-label="Go back to home"
      >
        <ArrowLeft 
          className="w-5 h-5 text-zinc-400 group-hover:text-zinc-300 transition-colors" 
          weight="bold"
        />
      </motion.button>

      <main 
        ref={mainContentRef}
        className={`flex-grow h-[calc(100vh-3.5rem)] overflow-y-scroll scrollbar-hide py-8 px-8 relative pb-16`}
      >
        <AnimatePresence>
          {isLoading && (
            <motion.div 
              key="loader"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0 flex items-center justify-center z-50 bg-[#0f0f0f]/50 backdrop-blur-sm"
            >
              <motion.div 
                animate={{ rotate: 360 }} 
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="h-8 w-8 border-4 border-zinc-400 border-t-transparent rounded-full"
              />
            </motion.div>
          )}
        </AnimatePresence>
        
        <AnimatePresence mode="wait">
          <motion.div 
            key={currentPageNumber}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="relative max-w-4xl mx-auto"
          >
            <motion.div 
              className="bg-zinc-900 p-8 rounded-xl shadow-xl"
              animate={{
                scale: selectedHighlight ? 0.98 : 1,
                transition: { duration: 0.5 }
              }}
              layoutId="paperContent"
            >
              {processedPaperData?.page && (
                <PaperContent 
                  content={processedPaperData.page.content}
                  images={processedPaperData.page.images}
                  onHighlightClick={setSelectedHighlight}
                  isBlurred={!!selectedHighlight}
                />
              )}
            </motion.div>
          </motion.div>
        </AnimatePresence>
      </main>

      <AnimatePresence>
        {selectedHighlight && (
          <ResourceDisplay
            {...processResources(selectedHighlight)}
            onClose={() => setSelectedHighlight(null)}
          />
        )}
      </AnimatePresence>

      <motion.button
        onClick={handleDownload}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="fixed right-6 bottom-16 p-3 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors z-50"
        aria-label="Download PDF"
        disabled={isDownloading}
      >
        {isDownloading ? (
          <motion.div 
            animate={{ rotate: 360 }} 
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="h-5 w-5 border-2 border-zinc-400 border-t-transparent rounded-full" 
          />
        ) : (
          'Download PDF'
        )}
      </motion.button>

      <PageScrollBar 
        currentPage={currentPageNumber}
        totalPages={processedPaperData?.total_pages || 1}
        onPageChange={handlePageChange}
      />
    </div>
  );
}