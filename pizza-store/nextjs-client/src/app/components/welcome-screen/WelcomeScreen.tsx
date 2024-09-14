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
    <div className={styles.welcomeScreen} style={{
      display: 'flex',
      flexDirection: 'row',
      alignItems: 'center',
    }}>
    
      <div className={styles.welcomeScreenButton} style={{ flex: '1' }}>

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
