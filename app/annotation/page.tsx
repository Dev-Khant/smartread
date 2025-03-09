"use client";

import { XLogo, GithubLogo, ArrowLeft } from "@phosphor-icons/react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";

export default function Annotation() {
  // Get the URL from search params
  const searchParams = useSearchParams();
  const router = useRouter();
  const url = searchParams.get("url");

  // Get the launch post URL from environment variable
  const githubUrl = process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com/yourusername/yt-operator";
  const xAccountUrl = process.env.NEXT_PUBLIC_X_ACCOUNT_URL || "https://twitter.com/yourusername";

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col">
      {/* Back button */}
      <motion.button
        onClick={() => router.push('/')}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5, duration: 0.3 }}
        className="absolute top-6 left-6 p-3 rounded-full bg-zinc-800/50 hover:bg-zinc-800 transition-colors group"
        aria-label="Go back to home"
      >
        <ArrowLeft 
          className="w-5 h-5 text-zinc-400 group-hover:text-zinc-300 transition-colors" 
          weight="bold"
        />
      </motion.button>

      {/* Main content area with flex-grow to push footer down */}
      <main className="flex-grow flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">Processing Paper</h1>
          {url && (
            <p className="text-zinc-400 text-sm max-w-md mx-auto break-all">
              {url}
            </p>
          )}
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