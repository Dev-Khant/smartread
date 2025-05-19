import { useEffect, useRef, useCallback } from 'react';

interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  interactionTime: number;
  memoryUsage?: number;
}

interface UsePerformanceMonitorOptions {
  trackPageLoad?: boolean;
  trackRender?: boolean;
  trackInteractions?: boolean;
  trackMemory?: boolean;
  onMetrics?: (metrics: PerformanceMetrics) => void;
}

export const usePerformanceMonitor = (options: UsePerformanceMonitorOptions = {}) => {
  const {
    trackPageLoad = true,
    trackRender = true,
    trackInteractions = true,
    trackMemory = false,
    onMetrics,
  } = options;

  const metricsRef = useRef<Partial<PerformanceMetrics>>({});
  const renderStartRef = useRef<number>(0);
  const interactionStartRef = useRef<number>(0);

  // Track page load performance
  useEffect(() => {
    if (!trackPageLoad) return;

    const measurePageLoad = () => {
      if (typeof window !== 'undefined' && 'performance' in window) {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          const loadTime = navigation.loadEventEnd - navigation.fetchStart;
          metricsRef.current.loadTime = loadTime;
        }
      }
    };

    // Measure after page load
    if (document.readyState === 'complete') {
      measurePageLoad();
    } else {
      window.addEventListener('load', measurePageLoad);
      return () => window.removeEventListener('load', measurePageLoad);
    }
  }, [trackPageLoad]);

  // Track render performance
  useEffect(() => {
    if (!trackRender) return;

    renderStartRef.current = performance.now();

    return () => {
      const renderTime = performance.now() - renderStartRef.current;
      metricsRef.current.renderTime = renderTime;
    };
  });

  // Track memory usage
  useEffect(() => {
    if (!trackMemory || !('memory' in performance)) return;

    const measureMemory = () => {
      const memory = (performance as any).memory;
      if (memory) {
        metricsRef.current.memoryUsage = memory.usedJSHeapSize;
      }
    };

    measureMemory();
    const interval = setInterval(measureMemory, 5000); // Every 5 seconds

    return () => clearInterval(interval);
  }, [trackMemory]);

  // Track user interactions
  const trackInteraction = useCallback((interactionType: string) => {
    if (!trackInteractions) return;

    interactionStartRef.current = performance.now();

    // Use requestIdleCallback to measure after interaction is processed
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        const interactionTime = performance.now() - interactionStartRef.current;
        metricsRef.current.interactionTime = interactionTime;
        
        // Report metrics if callback provided
        if (onMetrics) {
          onMetrics(metricsRef.current as PerformanceMetrics);
        }
      });
    }
  }, [trackInteractions, onMetrics]);

  // Get current metrics
  const getMetrics = useCallback((): Partial<PerformanceMetrics> => {
    return { ...metricsRef.current };
  }, []);

  // Get Web Vitals
  const getWebVitals = useCallback(() => {
    if (typeof window === 'undefined' || !('performance' in window)) {
      return null;
    }

    const vitals = {
      // First Contentful Paint
      fcp: 0,
      // Largest Contentful Paint
      lcp: 0,
      // First Input Delay
      fid: 0,
      // Cumulative Layout Shift
      cls: 0,
    };

    // Get FCP
    const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
    if (fcpEntry) {
      vitals.fcp = fcpEntry.startTime;
    }

    // Get LCP
    const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
    if (lcpEntries.length > 0) {
      vitals.lcp = lcpEntries[lcpEntries.length - 1].startTime;
    }

    // Get CLS
    const clsEntries = performance.getEntriesByType('layout-shift');
    let clsScore = 0;
    clsEntries.forEach((entry: any) => {
      if (!entry.hadRecentInput) {
        clsScore += entry.value;
      }
    });
    vitals.cls = clsScore;

    return vitals;
  }, []);

  // Performance observer for advanced metrics
  useEffect(() => {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        // Log performance entries for debugging
        if (process.env.NODE_ENV === 'development') {
          console.log('Performance entry:', entry);
        }
      });
    });

    // Observe different types of performance entries
    try {
      observer.observe({ entryTypes: ['measure', 'navigation', 'resource'] });
    } catch (e) {
      // Some browsers might not support all entry types
      console.warn('Performance observer error:', e);
    }

    return () => observer.disconnect();
  }, []);

  return {
    trackInteraction,
    getMetrics,
    getWebVitals,
  };
};

// Performance monitoring component
export const PerformanceMonitor: React.FC<{
  children: React.ReactNode;
  onMetrics?: (metrics: any) => void;
}> = ({ children, onMetrics }) => {
  const { getMetrics, getWebVitals } = usePerformanceMonitor({
    onMetrics,
  });

  useEffect(() => {
    // Report metrics periodically
    const interval = setInterval(() => {
      const metrics = getMetrics();
      const vitals = getWebVitals();
      
      if (onMetrics) {
        onMetrics({ ...metrics, vitals });
      }
    }, 10000); // Every 10 seconds

    return () => clearInterval(interval);
  }, [getMetrics, getWebVitals, onMetrics]);

  return <>{children}</>;
};

// Custom hook for measuring specific operations
export const useMeasure = () => {
  const measure = useCallback((name: string, fn: () => void | Promise<void>) => {
    const start = performance.now();
    
    const result = fn();
    
    if (result instanceof Promise) {
      return result.then((value) => {
        const end = performance.now();
        performance.mark(`${name}-end`);
        performance.measure(name, `${name}-start`, `${name}-end`);
        console.log(`${name} took ${end - start} milliseconds`);
        return value;
      });
    } else {
      const end = performance.now();
      performance.mark(`${name}-end`);
      performance.measure(name, `${name}-start`, `${name}-end`);
      console.log(`${name} took ${end - start} milliseconds`);
      return result;
    }
  }, []);

  return { measure };
};
