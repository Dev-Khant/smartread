'use client';

import { useState, useEffect, useRef } from 'react';
import { ProcessedPaperData, extractTableOfContents, getPageMetadata, extractFiguresAndTables } from '@/utils/paperProcessor';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import { motion, AnimatePresence } from 'framer-motion';
import 'katex/dist/katex.min.css';
import { CaretRight, CaretUp, CaretDown } from "@phosphor-icons/react";
import type { Element } from 'hast';

interface PaperViewerProps {
  data: ProcessedPaperData;
}

export default function PaperViewer({ data }: PaperViewerProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const toc = extractTableOfContents(data.pages);
  const figuresAndTables = extractFiguresAndTables(data.pages);
  const [scrollDirection, setScrollDirection] = useState<'up' | 'down' | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Custom components for markdown rendering
  const MarkdownComponents: Partial<Components> = {
    // Handle any custom or unknown elements by wrapping them in a span
    span: ({ children }) => {
      return <span className="text-zinc-400">{children}</span>;
    },
    img: ({ src, alt, ...props }) => {
      if (!alt) return null;
      
      const image = data.pages[currentPage].images.find(img => img.id === alt);
      if (!image) return null;

      const base64Data = image.imageBase64.startsWith('data:') 
        ? image.imageBase64
        : `data:image/jpeg;base64,${image.imageBase64}`;

      return (
        <span className="block w-full my-4 text-center">
          <img 
            {...props}
            src={base64Data}
            alt={alt}
            loading="lazy"
            className="inline-block rounded-lg shadow-lg"
            style={{
              maxWidth: `${image.bottomRightX - image.topLeftX}px`,
              maxHeight: `${image.bottomRightY - image.topLeftY}px`,
              objectFit: 'contain'
            }}
          />
        </span>
      );
    },
    table: ({ children, ...props }) => (
      <div className="my-4 w-full overflow-x-auto rounded-lg border border-zinc-800">
        <table {...props} className="w-full border-collapse min-w-full">
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }) => (
      <thead {...props} className="bg-zinc-800/50 border-b border-zinc-800">
        {children}
      </thead>
    ),
    tbody: ({ children, ...props }) => (
      <tbody {...props} className="divide-y divide-zinc-800">
        {children}
      </tbody>
    ),
    tr: ({ children, ...props }) => (
      <tr {...props} className="hover:bg-zinc-800/30 transition-colors">
        {children}
      </tr>
    ),
    th: ({ children, ...props }) => (
      <th {...props} className="px-4 py-3 text-left text-sm font-medium text-zinc-300">
        {children}
      </th>
    ),
    td: ({ children, ...props }) => (
      <td {...props} className="px-4 py-3 text-sm text-zinc-400 whitespace-pre-wrap">
        {children}
      </td>
    ),
  };

  // Scroll handling logic
  useEffect(() => {
    let lastScrollY = window.scrollY;
    let scrollTimeout: NodeJS.Timeout;

    const handleScroll = () => {
      if (isTransitioning) return;

      const currentScrollY = window.scrollY;
      const direction = currentScrollY > lastScrollY ? 'down' : 'up';
      const scrollDifference = Math.abs(currentScrollY - lastScrollY);
      
      if (scrollDifference > 50) {
        setScrollDirection(direction);
        
        if (scrollTimeout) clearTimeout(scrollTimeout);
        
        scrollTimeout = setTimeout(() => {
          if (direction === 'down' && currentPage < data.pages.length - 1) {
            setIsTransitioning(true);
            setCurrentPage(prev => prev + 1);
          } else if (direction === 'up' && currentPage > 0) {
            setIsTransitioning(true);
            setCurrentPage(prev => prev - 1);
          }
        }, 100);
      }
      
      lastScrollY = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (scrollTimeout) clearTimeout(scrollTimeout);
    };
  }, [currentPage, data.pages.length, isTransitioning]);

  // Reset transition state
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsTransitioning(false);
      setScrollDirection(null);
      // Scroll to top of content when page changes
      if (contentRef.current) {
        contentRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [currentPage]);

  // Handle click outside to close sidebar
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        setIsSidebarOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (isTransitioning) return;
      
      if (e.key === 'ArrowUp' && currentPage > 0) {
        setIsTransitioning(true);
        setScrollDirection('up');
        setCurrentPage(prev => prev - 1);
      } else if (e.key === 'ArrowDown' && currentPage < data.pages.length - 1) {
        setIsTransitioning(true);
        setScrollDirection('down');
        setCurrentPage(prev => prev + 1);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentPage, data.pages.length, isTransitioning]);

  return (
    <div className="relative min-h-screen">
      {/* Sidebar */}
      <div 
        ref={sidebarRef}
        className="fixed left-0 top-1/2 -translate-y-1/2 z-50"
      >
        <Collapsible 
          open={isSidebarOpen}
          onOpenChange={setIsSidebarOpen}
        >
          <CollapsibleTrigger className="bg-zinc-800/50 hover:bg-zinc-800 px-2 py-6 rounded-r-lg transition-colors flex items-center gap-1">
            <CaretRight 
              className="w-4 h-4 text-zinc-400 transition-transform duration-200"
              style={{ transform: isSidebarOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
            />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="bg-zinc-900/95 backdrop-blur-sm p-4 border border-zinc-800 ml-[1px] w-80 rounded-r-lg">
              <div className="max-h-[calc(100vh-200px)] overflow-hidden">
                <ScrollArea className="h-[calc(100vh-232px)]">
                  <div className="space-y-6 pr-4">
                    {/* Table of Contents */}
                    <div>
                      <h3 className="text-sm font-semibold mb-2 text-zinc-400">Table of Contents</h3>
                      <nav className="space-y-1">
                        {toc.map((item, index) => (
                          <button
                            key={index}
                            className={`block text-left w-full px-2 py-1 text-sm hover:bg-zinc-800 rounded transition-colors
                              ${item.level === 1 ? 'font-semibold' : ''}
                              ${item.level > 1 ? `ml-${item.level * 2}` : ''}`}
                            onClick={() => {
                              const targetPage = data.pages.findIndex(page => 
                                page.markdown.includes(item.title)
                              );
                              if (targetPage !== -1) {
                                setIsTransitioning(true);
                                setCurrentPage(targetPage);
                                setIsSidebarOpen(false);
                              }
                            }}
                          >
                            {item.title}
                          </button>
                        ))}
                      </nav>
                    </div>

                    {/* Figures and Tables */}
                    <div>
                      <h3 className="text-sm font-semibold mb-2 text-zinc-400">Figures & Tables</h3>
                      <div className="space-y-1">
                        {figuresAndTables.map((item, index) => (
                          <button
                            key={index}
                            className="block text-left w-full px-2 py-1 text-sm hover:bg-zinc-800 rounded transition-colors"
                            onClick={() => {
                              setIsTransitioning(true);
                              setCurrentPage(item.pageIndex);
                              setIsSidebarOpen(false);
                            }}
                          >
                            <span className="font-medium">{item.type.charAt(0).toUpperCase() + item.type.slice(1)}:</span>{' '}
                            {item.caption}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </ScrollArea>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${isSidebarOpen ? 'ml-80 blur-sm pointer-events-none' : 'ml-12'}`}>
        <div className="container mx-auto px-6 py-8 max-w-6xl">
          <div className="relative" ref={contentRef}>
            {/* Custom Page Scroller */}
            <div className="fixed right-8 top-1/2 -translate-y-1/2 flex items-center gap-4">
              <div className="text-sm text-zinc-400 w-12 text-center">
                {currentPage + 1} / {data.pages.length}
              </div>
              <div className="flex flex-col items-center gap-2">
                <button
                  className="p-1 rounded-full bg-zinc-800/50 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-300 transition-colors disabled:opacity-30 disabled:hover:bg-zinc-800/50 disabled:hover:text-zinc-400"
                  disabled={currentPage === 0}
                  onClick={() => {
                    setIsTransitioning(true);
                    setScrollDirection('up');
                    setCurrentPage(prev => prev - 1);
                  }}
                >
                  <CaretUp weight="bold" className="w-4 h-4" />
                </button>

                <div className="h-[75vh] w-1 bg-zinc-800/30 rounded-full relative">
                  <div 
                    className="absolute w-full rounded-full bg-zinc-600 transition-all duration-200"
                    style={{ 
                      height: `${100 / data.pages.length}%`,
                      top: `${(currentPage / (data.pages.length - 1)) * 100}%`,
                    }}
                  />
                  <div className="absolute inset-0" onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const clickPosition = (e.clientY - rect.top) / rect.height;
                    const targetPage = Math.min(
                      Math.floor(clickPosition * data.pages.length),
                      data.pages.length - 1
                    );
                    setIsTransitioning(true);
                    setCurrentPage(targetPage);
                    setScrollDirection(targetPage > currentPage ? 'down' : 'up');
                  }} />
                </div>

                <button
                  className="p-1 rounded-full bg-zinc-800/50 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-300 transition-colors disabled:opacity-30 disabled:hover:bg-zinc-800/50 disabled:hover:text-zinc-400"
                  disabled={currentPage === data.pages.length - 1}
                  onClick={() => {
                    setIsTransitioning(true);
                    setScrollDirection('down');
                    setCurrentPage(prev => prev + 1);
                  }}
                >
                  <CaretDown weight="bold" className="w-4 h-4" />
                </button>
              </div>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={currentPage}
                initial={{ 
                  opacity: 0,
                  y: scrollDirection === 'down' ? 50 : -50 
                }}
                animate={{ 
                  opacity: 1,
                  y: 0
                }}
                exit={{ 
                  opacity: 0,
                  y: scrollDirection === 'down' ? -50 : 50
                }}
                transition={{
                  type: "spring",
                  stiffness: 300,
                  damping: 30
                }}
                className={`prose prose-invert prose-lg max-w-none pr-24 transition-all duration-300 ${
                  isSidebarOpen ? 'blur-sm brightness-50' : 'blur-0 brightness-100'
                }`}
              >
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex, [rehypeRaw, { passThrough: ['think'] }]]}
                  components={MarkdownComponents}
                >
                  {data.pages[currentPage].markdown}
                </ReactMarkdown>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
} 