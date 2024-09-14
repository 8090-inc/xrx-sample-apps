import React, { useEffect } from "react";
import { motion } from "framer-motion";
import styles from "./OrderConfirmation.module.css";
import confetti from "canvas-confetti";
import { SkinConfigurations } from "../../types/skinConfig";
import { BottomCTA } from "../base/Base";
import Image from "next/image";

interface ConfirmationPayload {
  message: string;
  confirmation_number: string;
  confirmation_link: string;
}

interface OrderConfirmation {
  confirmation: ConfirmationPayload;
}

const NEXT_PUBLIC_AGENT = process.env.NEXT_PUBLIC_AGENT;
const skinConfig = SkinConfigurations[NEXT_PUBLIC_AGENT || "pizza-agent"];

const OrderConfirmation: React.FC<OrderConfirmation> = ({ confirmation }) => {
  useEffect(() => {
    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    function randomInRange(min: number, max: number) {
      return Math.random() * (max - min) + min;
    }

    const interval: NodeJS.Timeout = setInterval(function () {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        return clearInterval(interval);
      }

      const particleCount = 50 * (timeLeft / duration);

      confetti(
        Object.assign({}, defaults, {
          particleCount,
          origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
        })
      );
      confetti(
        Object.assign({}, defaults, {
          particleCount,
          origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
        })
      );
    }, 250);

    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.25 }}
    >
      <div className={styles.logo}>
        <Image
          src={skinConfig.logoSrc}
          alt="Main Icon"
          width={80}
          height={80}
        />
      </div>
      <motion.h2
        className={styles.title}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        Order Confirmed
      </motion.h2>
      <p className={styles.description}>
        Your order is confirmed, and you can track order{" "}
        <a href={confirmation.confirmation_link}>
          {confirmation.confirmation_number}
        </a>{" "}
        below.
      </p>
      <motion.div
        className={styles.btn}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
      >
        <BottomCTA
          onClick={() => window.open(confirmation.confirmation_link, "_blank")}
        >
          <span>Track Order</span>
          <Image
            src="/right-caret.svg"
            width={45}
            height={45}
            alt="Right Caret"
          />
        </BottomCTA>
      </motion.div>
      <motion.div
        className={styles.resetBtn}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        transition={{
          duration: 0.5,
          opacity: { delay: 1.5 },
          y: { delay: 1.5 },
          scale: { duration: 0.2 }
        }}
        onClick={() => {
          window.location.reload();
        }}
      >
        <Image
          src="/end-call-icon.svg"
          width={75}
          height={75}
          alt="End Call Icon"
        />
        <span>End</span>
      </motion.div>
    </motion.div>
  );
};

export default OrderConfirmation;
