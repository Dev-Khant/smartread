import { useState, FormEvent, useEffect } from 'react';

interface UrlFormProps {
  onSubmit: (url: string) => void;
  currentUrl: string | null;
}

const UrlForm: React.FC<UrlFormProps> = ({ onSubmit, currentUrl }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!currentUrl) {
      setUrl('');
    }
  }, [currentUrl]);

  const exampleUrls = {
    'AlexNet': 'https://proceedings.neurips.cc/paper_files/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf',
    'Attention Is All You Need': 'https://arxiv.org/pdf/1706.03762',
    'DeepSeek-R1': 'https://arxiv.org/pdf/2501.12948',
  };

  const handleExampleClick = (exampleUrl: string) => {
    setUrl(exampleUrl);
    // Programmatically submit the form
    onSubmit(exampleUrl);
  };

  const validateUrl = (input: string): boolean => {
    try {
      new URL(input);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (!validateUrl(url)) {
      setError('Please enter a valid URL');
      return;
    }

    onSubmit(url);
    setUrl('');
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
      <div className="relative overflow-hidden rounded-xl bg-[#121212] border border-zinc-800/80 focus-within:border-zinc-500/60">
        <div className="relative flex items-center z-[2]">
          <div className="absolute left-4 flex items-center pointer-events-none">
            <svg className="w-5 h-5 text-zinc-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste the pdf URL"
            className="w-full bg-transparent text-zinc-200 placeholder-zinc-500 px-12 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 border-none truncate pr-28"
            aria-label="Paper URL input"
          />
          <div className="absolute right-4 flex gap-2 items-center">
            <div className="w-[1px] h-8 bg-zinc-800/90"></div>
            <button
              type="submit"
              className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-4 py-1.5 rounded-lg transition-colors"
            >
              Extract
            </button>
          </div>
        </div>
      </div>
      {error && (
        <div className="mt-3">
          <div className="bg-[#121212] rounded-xl overflow-hidden border border-red-500/20 p-2.5 text-red-400 text-xs">
            {error}
          </div>
        </div>
      )}
      <div className="mt-4 flex justify-center gap-4">
        {Object.entries(exampleUrls).map(([name, url]) => (
          <button
            key={name}
            type="button"
            onClick={() => handleExampleClick(url)}
            className="px-4 py-2 bg-[#121212] hover:bg-zinc-800 text-zinc-400 text-xs rounded-lg border border-zinc-800/80 transition-colors flex items-center gap-3"
          >
            <span className="text-zinc-500">↗</span>
            <span>{name}</span>
          </button>
        ))}
      </div>
    </form>
  );
};

export default UrlForm;
