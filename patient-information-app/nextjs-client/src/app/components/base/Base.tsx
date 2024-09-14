// components.tsx
import React from "react";
import { motion } from "framer-motion";
import styles from "./Base.module.css";
import { useRef, useEffect, useState } from "react";

export const WidgetWrapper: React.FC<{
  title: string;
  children: React.ReactNode;
  useScrollableList?: boolean;
}> = ({ title, children, useScrollableList = true }) => {
  const [scrollPercentage, setScrollPercentage] = useState(0);
  return (
    <div className={styles.widgetWrapper}>
      <motion.h1
        className={styles.widgetTitle}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{
          opacity: 1,
          transform: "scale(1)"
        }}
        transition={{ duration: 0.45 }}
      >
        {title}
      </motion.h1>
      {useScrollableList ? (
        <ScrollableList setScrollPercentage={setScrollPercentage}>
          {children}
        </ScrollableList>
      ) : (
        children
      )}
      {scrollPercentage > 0 && (
        <motion.div
          className={styles.fadeEffect}
          style={{ opacity: scrollPercentage }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        />
      )}
    </div>
  );
};

interface ItemCardProps {
  image: string;
  title: string;
  subtitle?: string;
  onClick?: (event: any) => void;
  actionIcon?: React.ReactNode;
  isHighlighted?: boolean;
}

export const ItemCard: React.FC<ItemCardProps> = ({
  image,
  title,
  subtitle,
  onClick,
  actionIcon,
  isHighlighted
}) => (
  <motion.div
    className={styles.card}
    initial={{ opacity: 0 }}
    animate={{
      opacity: 1,
      scale: isHighlighted ? [1, 0.97, 1] : 1,
      boxShadow: isHighlighted
        ? [
            "0 0 0 3px color-mix(in srgb, var(--secondary-color) 30%, transparent), 0 4px 12px rgba(0, 0, 0, 0.1)",
            "0 0 0 6px color-mix(in srgb, var(--secondary-color) 20%, transparent), 0 6px 16px rgba(0, 0, 0, 0.15)",
            "0 0 0 3px color-mix(in srgb, var(--secondary-color) 30%, transparent), 0 4px 12px rgba(0, 0, 0, 0.1)"
          ]
        : "0 2px 4px rgba(0, 0, 0, 0.1)",
      backgroundColor: isHighlighted
        ? "color-mix(in srgb, var(--secondary-color) 10%, white 90%)"
        : "white"
    }}
    style={{
      marginLeft: isHighlighted ? "0" : "0.25rem",
      marginRight: isHighlighted ? "0" : "0.25rem"
    }}
    exit={{ opacity: 0 }}
    transition={
      isHighlighted
        ? {
            duration: 1.5,
            repeat: Infinity,
            repeatType: "reverse",
            ease: [0.4, 0, 0.6, 1]
          }
        : { duration: 0.3 }
    }
  >
    <img src={image} alt={title} className={styles.cardImage} />
    <motion.div className={styles.cardContent}>
      <h2 className={styles.cardTitle}>{title}</h2>
      {subtitle && <p className={styles.cardSubtitle}>{subtitle}</p>}
    </motion.div>
    {actionIcon && (
      <motion.button onClick={onClick} className={styles.cardAction}>
        {actionIcon}
      </motion.button>
    )}
  </motion.div>
);

interface ScrollableListProps {
  children: React.ReactNode;
  setScrollPercentage: (percentage: number) => void;
}

export const ScrollableList: React.FC<ScrollableListProps> = ({
  children,
  setScrollPercentage
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scrollContainer = scrollRef.current;

    if (!scrollContainer) return;

    let startY: number;
    let startScrollTop: number;
    let animationFrameId: number;

    const handleScroll = () => {
      if (scrollContainer) {
        const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
        const scrollableDistance = scrollHeight - clientHeight;
        const currentScroll = Math.min(scrollTop / scrollableDistance, 1);
        console.log("Scroll container:", scrollContainer);
        console.log("Scroll top:", scrollTop);
        console.log("Scroll height:", scrollHeight);
        console.log("Client height:", clientHeight);
        console.log("Scrollable distance:", scrollableDistance);
        console.log("Current scroll:", currentScroll);
        setScrollPercentage(1 - currentScroll);
      }
    };

    const handleTouchStart = (e: TouchEvent) => {
      startY = e.touches[0].pageY;
      startScrollTop = scrollContainer.scrollTop;

      if (startScrollTop <= 0) {
        scrollContainer.scrollTop = 1;
      }

      if (
        startScrollTop + scrollContainer.offsetHeight >=
        scrollContainer.scrollHeight
      ) {
        scrollContainer.scrollTop =
          scrollContainer.scrollHeight - scrollContainer.offsetHeight - 1;
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (!startY) return;

      const y = e.touches[0].pageY;
      const distance = startY - y;

      animationFrameId = requestAnimationFrame(() => {
        scrollContainer.scrollTop = startScrollTop + distance;
      });
    };

    const handleTouchEnd = () => {
      startY = 0;
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };

    scrollContainer.addEventListener("touchstart", handleTouchStart);
    scrollContainer.addEventListener("touchmove", handleTouchMove);
    scrollContainer.addEventListener("touchend", handleTouchEnd);
    scrollContainer.addEventListener("scroll", handleScroll);

    // Initial check
    handleScroll();

    return () => {
      scrollContainer.removeEventListener("touchstart", handleTouchStart);
      scrollContainer.removeEventListener("touchmove", handleTouchMove);
      scrollContainer.removeEventListener("touchend", handleTouchEnd);
      scrollContainer.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <div className={styles.scrollWrapper}>
      <div ref={scrollRef} className={styles.scrollContainer}>
        {children}
      </div>
    </div>
  );
};
export const BottomCTA: React.FC<{
  children: React.ReactNode;
  isLoading?: boolean;
  onClick?: (event: any) => void;
  isDisabled?: boolean;
}> = ({ children, isLoading, onClick, isDisabled }) => (
  <motion.div
    className={styles.bottomCTA}
    initial={{ opacity: 0, y: 50 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 50 }}
    transition={{ duration: 0.3 }}
    whileTap={!isDisabled ? { scale: 0.95 } : undefined}
  >
    <button disabled={isDisabled} onClick={onClick}>
      {isLoading ? <div className={styles.loadingSpinner} /> : children}
    </button>
  </motion.div>
);
