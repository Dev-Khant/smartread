import { X } from "@phosphor-icons/react";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useRef } from "react";

interface Resource {
  title: string;
  link: string;
  snippet?: string;
  image_url?: string;
  duration?: string;
}

interface ResourceDisplayProps {
  articles: Resource[];
  videos: Resource[];
  onClose: () => void;
}

export const ResourceDisplay: React.FC<ResourceDisplayProps> = ({ articles, videos, onClose }) => {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 pointer-events-none">
        <motion.div
          ref={panelRef}
          initial={{ x: "100vw" }}
          animate={{ x: 0 }}
          exit={{ x: "100vw" }}
          transition={{ type: "spring", damping: 30, stiffness: 300 }}
          className="fixed right-0 top-0 h-screen w-[500px] bg-zinc-900 border-l border-zinc-800 overflow-hidden shadow-2xl flex flex-col pointer-events-auto"
          style={{ 
            transform: 'translateX(0)', // Force hardware acceleration
            willChange: 'transform' 
          }}
        >
          <div className="flex flex-col h-full">
            <div className="flex-none">
              <div className="flex justify-between items-center p-6 border-b border-zinc-800 bg-zinc-900">
                <h2 className="text-xl font-semibold text-white">Related Resources</h2>
                <button
                  onClick={onClose}
                  className="p-3 rounded-full bg-zinc-800/50 hover:bg-zinc-800 transition-colors group"
                  aria-label="Close resources panel"
                >
                  <X className="w-5 h-5 text-zinc-400 group-hover:text-zinc-300 transition-colors" weight="bold" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              <div className="divide-y divide-zinc-800">
                {articles.length > 0 && (
                  <div>
                    <div className="bg-zinc-900 py-3 px-6">
                      <h3 className="text-lg font-medium text-white flex items-center gap-2">
                        Articles
                        <span className="text-sm text-zinc-500 font-normal">({articles.length})</span>
                      </h3>
                    </div>
                    <div className="px-6 py-4 space-y-4">
                      {articles.map((article, index) => (
                        <motion.a
                          key={index}
                          href={article.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block p-4 rounded-xl bg-zinc-800/50 hover:bg-zinc-800 transition-all group relative"
                          onClick={(e) => e.stopPropagation()}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                          whileHover={{ scale: 1.02 }}
                        >
                          <h4 className="text-sm font-medium text-white mb-2 group-hover:text-blue-400 transition-colors line-clamp-2">
                            {article.title}
                          </h4>
                          {article.snippet && (
                            <p className="text-xs text-zinc-400 line-clamp-3 group-hover:text-zinc-300 transition-colors">
                              {article.snippet}
                            </p>
                          )}
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl" />
                        </motion.a>
                      ))}
                    </div>
                  </div>
                )}

                {videos.length > 0 && (
                  <div>
                    <div className="bg-zinc-900 py-3 px-6">
                      <h3 className="text-lg font-medium text-white flex items-center gap-2">
                        Videos
                        <span className="text-sm text-zinc-500 font-normal">({videos.length})</span>
                      </h3>
                    </div>
                    <div className="px-6">
                      {videos.map((video, index) => (
                        <motion.a
                          key={index}
                          href={video.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block rounded-xl bg-zinc-800/50 hover:bg-zinc-800 transition-all group relative overflow-hidden mb-4 last:mb-0"
                          onClick={(e) => e.stopPropagation()}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: (articles.length + index) * 0.1 }}
                          whileHover={{ scale: 1.02 }}
                        >
                          {(video.image_url) && (
                            <div className="aspect-video relative">
                              <img
                                src={video.image_url}
                                alt={video.title}
                                className="w-full h-full object-cover"
                                loading="lazy"
                              />
                              {video.duration && (
                                <span className="absolute bottom-2 right-2 px-2 py-1 text-xs bg-black/80 text-white rounded-md backdrop-blur-sm">
                                  {video.duration}
                                </span>
                              )}
                              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent opacity-60 group-hover:opacity-40 transition-opacity duration-700" />
                              <div className="absolute inset-0 bg-blue-500/20 opacity-0 group-hover:opacity-30 transition-opacity duration-700" />
                            </div>
                          )}
                          <div className="px-3 py-2">
                            <h4 className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors line-clamp-2">
                              {video.title}
                            </h4>
                          </div>
                        </motion.a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}; 