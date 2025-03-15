"use client";

import UrlForm from "@/components/UrlForm";
import { useState } from "react";
import { XLogo, GithubLogo } from "@phosphor-icons/react";
import { Toaster } from "sonner";
import { LineShadowText } from "@/components/magicui/line-shadow-text";
import { ShimmerButton } from "@/components/magicui/shimmer-button";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useExtraction } from "@/hooks/extraction";

export default function Home() {
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);
  const { extractFromUrl, loading } = useExtraction();
  const router = useRouter();

  // Get the launch post URL from environment variable
  const launchPostUrl = process.env.NEXT_PUBLIC_LAUNCH_POST_URL || "https://twitter.com";
  const githubUrl = process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/yourusername/yt-operator";
  const xAccountUrl = process.env.NEXT_PUBLIC_X_ACCOUNT_URL || "https://twitter.com/yourusername";

  const handleUrlSubmit = async (url: string) => {
    try {
      setCurrentUrl(url);
      const extractedData = await extractFromUrl(url);
      if (extractedData) {
        router.push('/annotation');
      }
    } catch (error) {
      console.error('Error extracting data:', error);
      // Handle error appropriately
      setCurrentUrl(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col overflow-y-scroll scrollbar-hide">
      <Toaster 
        theme="dark" 
        position="top-center"
        toastOptions={{
          style: {
            background: "#121212",
            border: "1px solid rgba(63, 63, 70, 0.5)",
            color: "#e4e4e7"
          }
        }}
      />
      {/* Main content area with flex-grow to push footer down */}
      <main className="flex-grow">
        <div className="container mx-auto px-4 py-8 md:py-12 space-y-8 md:space-y-12">
          {/* Hero Section - Modern and clean design */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center space-y-4 md:space-y-5 mb-6 md:mb-10"
          >
            <div className="inline-block mb-2">
              <a 
                href={launchPostUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ShimmerButton className="inline-flex items-center px-3 py-1 rounded-full border border-zinc-700/50 text-xs font-medium text-zinc-300">
                  <XLogo className="h-3.5 w-3.5 mr-1.5 text-zinc-400" />
                  Launch Post
                </ShimmerButton>
              </a>
            </div>
            <h1 className="text-balance text-4xl font-semibold leading-none tracking-tighter sm:text-5xl md:text-6xl lg:text-8xl">
              <LineShadowText className="italic" shadowColor="white">
                SmartRead
              </LineShadowText>
            </h1>
            <p className="text-sm md:text-base text-zinc-400 max-w-4xl mx-auto px-2">
              AI tool that automatically annotates technical PDFs, and shows related articles and videos for better understanding
            </p>
          </motion.div>

          {/* Form Section */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="pt-5 md:pt-7"
          >
            <div className="relative">
              {loading ? (
                <div className="text-center space-y-4">
                  <h2 className="text-xl font-semibold text-zinc-200">Processing Paper</h2>
                  <div className="animate-pulse flex flex-col items-center gap-4">
                    <div className="h-8 w-8 border-4 border-zinc-400 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-zinc-400 text-sm">This may take a few moments...</p>
                  </div>
                </div>
              ) : (
                <>
                  <UrlForm onSubmit={handleUrlSubmit} currentUrl={currentUrl} />
                  
                  {/* Current URL display - Positioned absolutely */}
                  {currentUrl && (
                    <div className="absolute w-full text-center mt-1">
                      <button 
                        onClick={() => setCurrentUrl(null)}
                        className="text-xs text-zinc-400 hover:text-zinc-300 underline"
                      >
                        Reset results
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </motion.div>

          {/* Features Section */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="max-w-4xl mx-auto pt-12 md:pt-15"
          >
            <h2 className="text-xl md:text-2xl font-semibold mb-4 md:mb-6 text-center text-zinc-200">Features</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-6">
              <div className="bg-[#121212] rounded-xl p-4 md:p-6 border border-zinc-800/50">
                <div className="flex items-start">
                  <div className="mr-3 md:mr-4">
                    <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-indigo-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 md:w-6 md:h-6 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-base md:text-lg font-medium text-zinc-200 mb-1 md:mb-2">Smart Annotation</h3>
                    <p className="text-xs md:text-sm text-zinc-400">View key insights and important highlights from the pdf</p>
                  </div>
                </div>
              </div>
              <div className="bg-[#121212] rounded-xl p-4 md:p-6 border border-zinc-800/50">
                <div className="flex items-start">
                  <div className="mr-3 md:mr-4">
                    <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-emerald-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 md:w-6 md:h-6 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-base md:text-lg font-medium text-zinc-200 mb-1 md:mb-2">Related Resources</h3>
                    <p className="text-xs md:text-sm text-zinc-400">Get related articles and videos on selected technical highlights for improved understanding</p>
                  </div>
                </div>
              </div>
              <div className="bg-[#121212] rounded-xl p-4 md:p-6 border border-zinc-800/50">
                <div className="flex items-start">
                  <div className="mr-3 md:mr-4">
                    <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-amber-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 md:w-6 md:h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-base md:text-lg font-medium text-zinc-200 mb-1 md:mb-2">Technical PDFs</h3>
                    <p className="text-xs md:text-sm text-zinc-400">Works with any technical PDF, making technical reading easier to understand</p>
                  </div>
                </div>
              </div>
              <div className="bg-[#121212] rounded-xl p-4 md:p-6 border border-zinc-800/50">
                <div className="flex items-start">
                  <div className="mr-3 md:mr-4">
                    <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-rose-500/10 flex items-center justify-center">
                      <svg className="w-5 h-5 md:w-6 md:h-6 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-base md:text-lg font-medium text-zinc-200 mb-1 md:mb-2">Download Annotated PDF</h3>
                    <p className="text-xs md:text-sm text-zinc-400">Save a copy of the annotated original PDF to keep highlights</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-6 mt-auto">
        <div className="container mx-auto px-4">
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="flex items-center space-x-4">
              <a 
                href={githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 hover:text-zinc-300 transition-colors"
                aria-label="GitHub Repository"
              >
                <GithubLogo className="w-5 h-5" />
              </a>
              <a 
                href={xAccountUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 hover:text-zinc-300 transition-colors"
                aria-label="X (Twitter) Account"
              >
                <XLogo className="w-5 h-5" />
              </a>
            </div>
            <p className="text-center text-zinc-500 text-xs flex items-center justify-center ml-5">
              © {new Date().getFullYear()} SmartRead <span className="mx-1">•</span> 
              <a 
                href={githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-400 hover:text-zinc-300 transition-colors"
              >
                Open Source
              </a><span className="mx-1">•</span>
              Built with ❤️ in India 🇮🇳
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}