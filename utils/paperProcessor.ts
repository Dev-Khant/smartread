// Types for paper data structure
export interface PaperImage {
  id: string;
  topLeftX: number;
  topLeftY: number;
  bottomRightX: number;
  bottomRightY: number;
  imageBase64: string;
}

export interface PageDimensions {
  dpi: number;
  height: number;
  width: number;
}

export interface PaperPage {
  index: number;
  markdown: string;
  processedMarkdown?: string;
  images: PaperImage[];
  dimensions: PageDimensions;
}

export interface ProcessedPaperData {
  pages: PaperPage[];
  model: string;
  usageInfo: {
    pagesProcessed: number;
    docSizeBytes: number;
  };
}

// Function to process markdown content and replace image references
export function processMarkdown(markdown: string, images: PaperImage[]): string {
  let processedMarkdown = markdown;
  
  // Replace image references with base64 data
  images.forEach((image) => {
    const imagePattern = new RegExp(`!\\[.*?\\]\\(${image.id}\\)`, 'g');
    
    // Check if the base64 string already includes the data URI prefix
    const base64Data = image.imageBase64.startsWith('data:') 
      ? image.imageBase64
      : `data:image/jpeg;base64,${image.imageBase64}`;

    const imageReplacement = `
<div class="relative w-full my-4 flex justify-center">
  <img 
    src="${base64Data}"
    alt="${image.id}"
    loading="lazy"
    style="
      max-width: ${image.bottomRightX - image.topLeftX}px;
      max-height: ${image.bottomRightY - image.topLeftY}px;
      object-fit: contain;
      border-radius: 8px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    "
  />
</div>`;
    
    processedMarkdown = processedMarkdown.replace(imagePattern, imageReplacement);
  });

  return processedMarkdown;
}

// Function to calculate reading time
export function calculateReadingTime(markdown: string): number {
  const wordsPerMinute = 200;
  const words = markdown.split(/\s+/).length;
  return Math.ceil(words / wordsPerMinute);
}

// Main function to process paper data
export function processPaperData(data: ProcessedPaperData) {
  return {
    ...data,
    pages: data.pages.map((page) => ({
      ...page,
      processedMarkdown: processMarkdown(page.markdown, page.images),
      readingTime: calculateReadingTime(page.markdown)
    }))
  };
}

// Function to extract table of contents
export function extractTableOfContents(pages: PaperPage[]): Array<{ title: string; level: number }> {
  const toc: Array<{ title: string; level: number }> = [];
  
  pages.forEach((page) => {
    const headingRegex = /^(#{1,6})\s+(.+)$/gm;
    let match;
    
    while ((match = headingRegex.exec(page.markdown)) !== null) {
      const level = match[1].length;
      const title = match[2].trim();
      toc.push({ title, level });
    }
  });
  
  return toc;
}

// Function to get page metadata
export function getPageMetadata(page: PaperPage) {
  const titleMatch = page.markdown.match(/^#\s+(.+)$/m);
  const abstractMatch = page.markdown.match(/^##\s+Abstract\s+([\s\S]+?)(?=##|$)/m);
  
  return {
    title: titleMatch ? titleMatch[1] : null,
    abstract: abstractMatch ? abstractMatch[1].trim() : null,
    hasImages: page.images.length > 0,
    readingTime: calculateReadingTime(page.markdown)
  };
}

// Function to extract figures and tables
export function extractFiguresAndTables(pages: PaperPage[]): Array<{ type: 'figure' | 'table'; caption: string; pageIndex: number }> {
  const items: Array<{ type: 'figure' | 'table'; caption: string; pageIndex: number }> = [];
  
  pages.forEach((page, pageIndex) => {
    // Extract figures
    const figureRegex = /Figure\s+\d+:\s+(.+?)(?=\n|$)/g;
    let figureMatch;
    while ((figureMatch = figureRegex.exec(page.markdown)) !== null) {
      items.push({
        type: 'figure',
        caption: figureMatch[1].trim(),
        pageIndex
      });
    }
    
    // Extract tables
    const tableRegex = /Table\s+\d+:\s+(.+?)(?=\n|$)/g;
    let tableMatch;
    while ((tableMatch = tableRegex.exec(page.markdown)) !== null) {
      items.push({
        type: 'table',
        caption: tableMatch[1].trim(),
        pageIndex
      });
    }
  });
  
  return items;
} 