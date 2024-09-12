import React from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import styles from "./WelcomeScreen.module.css";
import { SkinConfig } from "../../types/skinConfig";
import { WidgetWrapper, BottomCTA } from "../base/Base";

interface WelcomeScreenProps {
  onStart: () => void;
  config: SkinConfig;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStart, config }) => {
  return (
    <div className={styles.welcomeScreen}>
      {" "}
      <WidgetWrapper title="" useScrollableList={false}>
        <motion.img
          className={styles.welcomeScreenLogo}
          src={config.welcomeScreenLogoSrc}
          alt="WelcomeLogo"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            delay: 0.2,
            type: "spring",
            stiffness: 260,
            damping: 20
          }}
        />
        {config.welcomeText && (
          <motion.h1
            className={styles.welcomeText}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            {config.welcomeText}
          </motion.h1>
        )}
      </WidgetWrapper>
      <div className={styles.welcomeScreenButton}>
        {" "}
        <BottomCTA onClick={onStart}>
          <span>{config.buttonText}</span>
          <Image
            src="/right-caret.svg"
            width={45}
            height={45}
            alt="Right Caret"
          />
        </BottomCTA>
      </div>
    </div>
  );
};

export default WelcomeScreen;
