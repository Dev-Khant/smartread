"use client";

import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isFirstMount, setIsFirstMount] = useState(true);

  useEffect(() => {
    setIsFirstMount(false);
  }, []);
  
  // Different animation variants based on the current page
  const pageVariants = {
    home: {
      initial: { x: "-100%", opacity: 0 },
      animate: { x: 0, opacity: 1 },
      exit: { x: "100%", opacity: 0 },
    },
    annotation: {
      initial: { x: "100%", opacity: 0 },
      animate: { x: 0, opacity: 1 },
      exit: { x: "-100%", opacity: 0 },
    },
  };

  // Select the appropriate variant based on the current path
  const variant = pathname === "/" ? "home" : "annotation";

  // Skip animation for home page on first mount
  const shouldAnimate = !(isFirstMount && pathname === "/");

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pathname}
        variants={pageVariants}
        initial={shouldAnimate ? pageVariants[variant].initial : false}
        animate={shouldAnimate ? pageVariants[variant].animate : { x: 0, opacity: 1 }}
        exit={pageVariants[variant].exit}
        transition={{
          type: "spring",
          stiffness: 60,
          damping: 15,
          mass: 0.2,
          restSpeed: 0.1,
          restDelta: 0.1,
          velocity: 2,
          bounce: 0
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}