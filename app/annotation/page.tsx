"use client";

import { useEffect, useState } from 'react';
import { ArrowLeft } from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useExtraction } from "@/hooks/extraction";
import PaperViewer from '@/components/PaperViewer';
import { ProcessedPaperData, processPaperData } from '@/utils/paperProcessor';

export default function AnnotationPage() {
  const router = useRouter();
  const { data, reset } = useExtraction();
  const [processedPaperData, setProcessedPaperData] = useState<ProcessedPaperData | null>(null);

  useEffect(() => {
    if (!data) {
      router.push('/');
      return;
    }

    // Process the paper data when it's available
    const processed = processPaperData(data);
    setProcessedPaperData(processed);
  }, [data, router]);

  const handleBack = () => {
    reset(); // Reset the extraction state
    router.push('/');
  };

  // Don't render anything if no data
  if (!data || !processedPaperData) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">No Paper Data Found</h1>
          <p className="text-zinc-400">Please upload a paper first.</p>
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
      <main className="flex-grow h-[calc(100vh-2rem)] overflow-y-scroll scrollbar-hide py-4">
        <PaperViewer data={processedPaperData} />
      </main>
    </div>
  );
}