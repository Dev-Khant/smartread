import React, { useState, useCallback } from 'react';
import { CaretLeft, CaretRight } from "@phosphor-icons/react";
import { motion, AnimatePresence } from 'framer-motion';

interface PageScrollBarProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

// Common button styles to reduce duplication
const buttonStyles = {
  navigation: `p-2 rounded-full bg-zinc-800 transition-colors group`,
  navigationDisabled: `opacity-50 cursor-not-allowed`,
  navigationEnabled: `hover:bg-zinc-700`,
  icon: `text-zinc-400 group-hover:text-zinc-300`
};

export const PageScrollBar: React.FC<PageScrollBarProps> = ({
  currentPage,
  totalPages,
  onPageChange,
}) => {
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Save to localStorage whenever we change pages
  const handlePageChange = useCallback((newPage: number) => {
    if (newPage === currentPage || newPage < 1 || newPage > totalPages || isTransitioning) {
      return;
    }
    
    // Set transitioning state to prevent multiple clicks
    setIsTransitioning(true);
    
    // Store page in localStorage
    localStorage.setItem('currentPage', newPage.toString());
    
    // Call the change handler
    onPageChange(newPage);
    
    // Reset transition state after a delay
    setTimeout(() => {
      setIsTransitioning(false);
    }, 800);
  }, [currentPage, totalPages, isTransitioning, onPageChange]);

  // Handle button clicks to go left or right
  const handleButtonClick = useCallback((direction: 'left' | 'right') => {
    const newPage = direction === 'left' 
      ? Math.max(1, currentPage - 1)
      : Math.min(totalPages, currentPage + 1);
    
    handlePageChange(newPage);
  }, [currentPage, totalPages, handlePageChange]);

  // Generate page number buttons
  const renderPageButtons = () => {
    const buttons = [];
    const maxButtonsToShow = 5;
    
    // Calculate start and end pages to show
    let startPage = Math.max(1, currentPage - Math.floor(maxButtonsToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxButtonsToShow - 1);
    
    // Adjust startPage if endPage is at max
    if (endPage === totalPages) {
      startPage = Math.max(1, endPage - maxButtonsToShow + 1);
    }
    
    // Show first page if we're not starting at 1
    if (startPage > 1) {
      buttons.push(
        <PageButton 
          key="first" 
          page={1} 
          isActive={currentPage === 1}
          isDisabled={isTransitioning}
          onClick={() => handlePageChange(1)} 
        />
      );
      
      // Add ellipsis if we're not starting at 2
      if (startPage > 2) {
        buttons.push(
          <div key="ellipsis-start" className="text-zinc-500 px-1">...</div>
        );
      }
    }
    
    // Add page buttons
    for (let i = startPage; i <= endPage; i++) {
      buttons.push(
        <PageButton 
          key={i} 
          page={i} 
          isActive={currentPage === i}
          isDisabled={isTransitioning}
          onClick={() => handlePageChange(i)} 
        />
      );
    }
    
    // Show last page if we're not ending at totalPages
    if (endPage < totalPages) {
      // Add ellipsis if we're not ending at totalPages-1
      if (endPage < totalPages - 1) {
        buttons.push(
          <div key="ellipsis-end" className="text-zinc-500 px-1">...</div>
        );
      }
      
      buttons.push(
        <PageButton 
          key="last" 
          page={totalPages} 
          isActive={currentPage === totalPages}
          isDisabled={isTransitioning}
          onClick={() => handlePageChange(totalPages)} 
        />
      );
    }
    
    return buttons;
  };

  return (
    <div className="fixed right-0 bottom-0 left-0 w-full flex flex-col items-center bg-zinc-900/80 backdrop-blur-sm rounded-t-lg shadow-lg z-50 py-2">
      <div className="flex items-center justify-center space-x-1 sm:space-x-2">
        {/* Left button */}
        <motion.button
          type="button"
          onClick={() => handleButtonClick('left')}
          disabled={currentPage <= 1 || isTransitioning}
          whileTap={{ scale: 0.95 }}
          className={`${buttonStyles.navigation}
            ${currentPage <= 1 || isTransitioning ? buttonStyles.navigationDisabled : buttonStyles.navigationEnabled}`}
        >
          <CaretLeft weight="bold" className={`w-3 h-3 sm:w-4 sm:h-4 ${buttonStyles.icon}`} />
        </motion.button>

        {/* Page buttons */}
        <div className="flex items-center px-1 sm:px-2">
          {totalPages > 1 ? (
            renderPageButtons()
          ) : (
            <div className="text-zinc-400 text-xs sm:text-sm font-medium">
              Page 1 of 1
            </div>
          )}
        </div>

        {/* Right button */}
        <motion.button
          type="button"
          onClick={() => handleButtonClick('right')}
          disabled={currentPage >= totalPages || isTransitioning}
          whileTap={{ scale: 0.95 }}
          className={`${buttonStyles.navigation}
            ${currentPage >= totalPages || isTransitioning ? buttonStyles.navigationDisabled : buttonStyles.navigationEnabled}`}
        >
          <CaretRight weight="bold" className={`w-3 h-3 sm:w-4 sm:h-4 ${buttonStyles.icon}`} />
        </motion.button>
      </div>
    </div>
  );
};

// Page button component
const PageButton: React.FC<{
  page: number;
  isActive: boolean;
  isDisabled: boolean;
  onClick: () => void;
}> = ({ page, isActive, isDisabled, onClick }) => {
  return (
    <motion.button
      whileHover={!isActive && !isDisabled ? { scale: 1.05 } : {}}
      whileTap={!isDisabled ? { scale: 0.95 } : {}}
      onClick={onClick}
      disabled={isDisabled}
      className={`
        min-w-[24px] h-6 sm:min-w-[32px] sm:h-8 
        rounded px-1 text-xs sm:text-sm font-medium
        transition-colors
        ${isActive 
          ? 'bg-zinc-700 text-white' 
          : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300'}
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {page}
    </motion.button>
  );
};