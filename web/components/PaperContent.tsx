import { useEffect, useRef, useState } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import { motion, AnimatePresence } from "framer-motion";
import { X } from "@phosphor-icons/react";
import Script from 'next/script';
import katex from 'katex';
import 'katex/dist/katex.min.css';

// Add MathJax type declarations
declare global {
  interface Window {
    MathJax?: {
      typesetPromise?: () => Promise<void>;
      tex?: {
        inlineMath: string[][];
        displayMath: string[][];
        processEscapes: boolean;
        packages: string[];
      };
      svg?: {
        fontCache: string;
      };
      options?: {
        skipHtmlTags: string[];
        processHtmlClass: string;
      };
      startup?: {
        pageReady: () => Promise<void>;
      };
    };
  }
}

interface PaperContentProps {
  content: string;
  images?: Array<{
    id: string;
    image_url: string;
  }>;
  onHighlightClick?: (index: string) => void;
  isBlurred?: boolean;
}

export const PaperContent: React.FC<PaperContentProps> = ({ content, images, onHighlightClick, isBlurred = false }) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [maximizedImage, setMaximizedImage] = useState<string | null>(null);

  useEffect(() => {
    const handleHighlightClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const highlightElement = target.closest('highlight');
      if (highlightElement) {
        const index = highlightElement.getAttribute('index');
        if (index && onHighlightClick) {
          event.preventDefault();
          event.stopPropagation();
          onHighlightClick(index);
        }
      }
    };

    const handleImageClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (target.tagName.toLowerCase() === 'img') {
        const src = target.getAttribute('src');
        if (src) {
          setMaximizedImage(src);
        }
      }
    };

    const contentElement = contentRef.current;
    if (contentElement) {
      contentElement.addEventListener('click', handleHighlightClick);
      contentElement.addEventListener('click', handleImageClick);
      return () => {
        contentElement.removeEventListener('click', handleHighlightClick);
        contentElement.removeEventListener('click', handleImageClick);
      };
    }
  }, [onHighlightClick]);

  // Initialize MathJax when content changes
  useEffect(() => {
    if (window.MathJax) {
      window.MathJax.typesetPromise?.();
    }
  }, [content]);

  const processContent = (htmlContent: string, imageData?: Array<{ id: string; image_url: string }>) => {
    if (!imageData) return htmlContent;

    let processedContent = htmlContent;
    
    // Process images
    imageData.forEach(image => {
      const regex = new RegExp(`src=["']${image.id}["']`, 'g');
      processedContent = processedContent.replace(regex, `src="${image.image_url}"`);
    });

    // Process display math expressions (those between $$ $$)
    processedContent = processedContent.replace(/\$\$([\s\S]+?)\$\$/g, (match, latex) => {
      try {
        const cleanLatex = latex.trim()
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&amp;/g, '&')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'")
          .replace(/\s+/g, ' '); // Normalize whitespace
        return katex.renderToString(cleanLatex, {
          displayMode: true,
          throwOnError: false,
          strict: false,
          trust: true,
          output: 'html',
          macros: {
            "\\mathbf": "\\boldsymbol"
          }
        });
      } catch (e) {
        console.error('KaTeX display math error:', e);
        return match;
      }
    });

    // Process inline math expressions (those between single $)
    processedContent = processedContent.replace(/\$([^\$]+?)\$/g, (match, latex) => {
      try {
        const cleanLatex = latex.trim()
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&amp;/g, '&')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'")
          .replace(/\s+/g, ' '); // Normalize whitespace
        return katex.renderToString(cleanLatex, {
          displayMode: false,
          throwOnError: false,
          strict: false,
          trust: true,
          output: 'html',
          macros: {
            "\\mathbf": "\\boldsymbol"
          }
        });
      } catch (e) {
        console.error('KaTeX inline math error:', e);
        return match;
      }
    });

    // Fix common LaTeX command issues
    processedContent = processedContent
      .replace(/\\text\s+/g, '\\text{') // Fix \text spacing
      .replace(/\\_/g, '_') // Fix underscores
      .replace(/\\pi(?![a-zA-Z])/g, '\\pi '); // Ensure \pi has proper spacing

    return processedContent;
  };

  const sanitizerConfig = {
    ALLOWED_TAGS: [
      'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'strong', 'em', 'img', 'code', 'pre', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'br', 'hr', 'sup', 'sub', 'span', 'div', 'highlight',
      'svg', 'path', 'line', 'rect', 'circle', 'ellipse', 'polyline', 'polygon',
      // Add KaTeX-specific tags
      'annotation', 'semantics', 'math', 'mrow', 'mi', 'mo', 'mn', 'msup', 'msub', 'msubsup', 'mfrac', 'mtable', 'mtr', 'mtd', 'mover', 'munder', 'munderover',
      'mtext', 'merror', 'mspace'
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'class', 'id', 'style', 'loading', 'index',
      'viewBox', 'd', 'fill', 'stroke', 'stroke-width',
      'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
      'points', 'transform', 'width', 'height',
      'xmlns', 'display', 'dir', 'aria-hidden', 'data-*'
    ],
    ADD_TAGS: ['highlight'],
    ADD_ATTR: ['index']
  };

  const processedContent = processContent(content, images);
  const sanitizedContent = DOMPurify.sanitize(processedContent, sanitizerConfig);

  const contentStyles = `
    .prose {
      position: relative;
      z-index: 1;
    }

    .prose > * + * {
      margin-top: 1.5em;
    }

    .prose h1, .prose h2, .prose h3, .prose h4 {
      position: relative;
      text-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
    }

    .prose p {
      line-height: 1.8;
      letter-spacing: 0.01em;
    }

    /* Math styles */
    .MathJax {
      font-size: 1.1em !important;
      outline: none;
    }

    .MathJax_Display {
      overflow-x: auto;
      overflow-y: hidden;
      margin: 1em 0 !important;
    }

    mjx-container {
      overflow-x: auto;
      overflow-y: hidden;
      max-width: 100%;
    }

    mjx-container[jax="CHTML"][display="true"] {
      margin: 1em 0 !important;
      display: flex !important;
      justify-content: center;
      align-items: center;
    }

    mjx-container[jax="CHTML"] {
      line-height: 0;
    }

    highlight {
      display: inline;
      background: linear-gradient(120deg, rgba(255, 214, 0, 0.2) 0%, rgba(255, 214, 0, 0.3) 100%);
      border-radius: 0.25em;
      padding: 0.1em 0.2em;
      box-decoration-break: clone;
      -webkit-box-decoration-break: clone;
      position: relative;
      text-shadow: none;
      cursor: pointer;
      transition: all 0.2s ease;
      z-index: 10;
    }

    highlight:hover {
      background: linear-gradient(120deg, rgba(255, 214, 0, 0.3) 0%, rgba(255, 214, 0, 0.4) 100%);
      transform: translateY(-1px);
    }

    highlight::before {
      display: none;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 2rem 0;
      background: rgba(31, 41, 55, 0.5);
      backdrop-filter: blur(4px);
      border-radius: 0.5rem;
      overflow: hidden;
    }

    th, td {
      border: 1px solid rgba(55, 65, 81, 0.5);
      padding: 0.75rem;
    }

    th {
      background-color: rgba(31, 41, 55, 0.8);
      backdrop-filter: blur(4px);
    }

    blockquote {
      border-left: 4px solid rgba(55, 65, 81, 0.8);
      padding: 1rem 1.5rem;
      margin: 1.5rem 0;
      font-style: italic;
      background: rgba(31, 41, 55, 0.2);
      backdrop-filter: blur(4px);
      border-radius: 0 0.5rem 0.5rem 0;
    }

    img {
      display: block;
      margin: 2.5rem auto;
      max-width: 100%;
      height: auto;
      border-radius: 0.75rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      transition: transform 0.3s ease;
      cursor: pointer;
    }

    .prose img:hover {
      transform: scale(1.02);
    }

    /* Remove hover effects for maximized image */
    .maximized-image {
      cursor: default;
      transform: none !important;
      transition: none !important;
    }

    pre {
      background: rgba(31, 41, 55, 0.6) !important;
      backdrop-filter: blur(4px);
      border-radius: 0.5rem;
      padding: 1rem;
      margin: 1.5rem 0;
      overflow-x: auto;
    }

    code {
      background: rgba(31, 41, 55, 0.6);
      padding: 0.2em 0.4em;
      border-radius: 0.25em;
      font-size: 0.875em;
    }

    /* KaTeX styles */
    .katex {
      font-size: 1.1em !important;
      font-family: KaTeX_Main, 'Times New Roman', serif;
      line-height: 1.4;
      white-space: normal;
      text-indent: 0;
      text-rendering: auto;
      pointer-events: none;
    }

    .katex-display {
      display: block;
      margin: 1.5em 0;
      text-align: center;
      overflow-x: auto;
      overflow-y: hidden;
      padding: 0.5em 0;
    }

    .katex-display > .katex {
      display: inline-block;
      text-align: center;
      max-width: 100%;
    }

    .katex-html {
      overflow-x: auto;
      overflow-y: hidden;
      pointer-events: none;
      max-width: 100%;
    }

    /* Fix spacing around math expressions */
    p .katex {
      margin: 0 0.2em;
    }

    /* Ensure proper spacing for text mode in math */
    .katex .text {
      font-family: inherit;
      white-space: pre-wrap;
    }
  `;

  return (
    <>
      <style>{contentStyles}</style>
      <Script
        id="mathjax-script"
        strategy="afterInteractive"
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        onLoad={() => {
          window.MathJax = {
            tex: {
              inlineMath: [['$', '$'], ['\\(', '\\)']],
              displayMath: [['$$', '$$'], ['\\[', '\\]']],
              processEscapes: true,
              packages: ['base', 'ams', 'noerrors', 'noundefined']
            },
            svg: {
              fontCache: 'global'
            },
            options: {
              skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
              processHtmlClass: 'tex2jax_process'
            },
            startup: {
              pageReady: () => {
                return Promise.resolve(window.MathJax?.typesetPromise?.() || undefined);
              }
            }
          };
          window.MathJax?.typesetPromise?.();
        }}
      />
      <div 
        ref={contentRef}
        className={`prose prose-invert prose-headings:text-white prose-p:text-gray-300 prose-strong:text-white prose-a:text-blue-400 hover:prose-a:text-blue-300 prose-code:text-gray-300 prose-pre:bg-zinc-800/60 prose-pre:text-gray-300 max-w-none transition-all duration-500 tex2jax_process ${isBlurred ? 'blur-[1px] opacity-60' : ''}`}
        dangerouslySetInnerHTML={{ __html: sanitizedContent }}
      />

      <AnimatePresence mode="wait">
        {maximizedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90"
            onClick={() => setMaximizedImage(null)}
          >
            <button
              onClick={() => setMaximizedImage(null)}
              className="absolute top-6 right-6 p-3 rounded-full bg-zinc-800/50 hover:bg-zinc-800 transition-colors group"
              aria-label="Close maximized image"
            >
              <X className="w-5 h-5 text-zinc-400 group-hover:text-zinc-300 transition-colors" weight="bold" />
            </button>
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ 
                duration: 0.2,
                ease: "easeInOut"
              }}
              className="max-w-[90vw] max-h-[90vh] relative"
              onClick={(e) => e.stopPropagation()}
            >
              <img
                src={maximizedImage}
                alt="Maximized view"
                className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl maximized-image"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}; 