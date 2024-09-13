"use client";
jsx;

import Image from "next/image";
import { useRef, useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { jsx } from "react/jsx-runtime";
import { MicVAD } from "@ricky0123/vad-web";
import Cart from "./components/cart/Cart";
import ProductDetails from "./components/product-details/ProductDetails";
import OrderConfirmation from "./components/order-confirmation/OrderConfirmation";
import styles from "./Home.module.css";
import Menu from "./components/menu/Menu";
import WelcomeScreen from "./components/welcome-screen/WelcomeScreen";
import { BottomCTA } from "./components/base/Base";
import PreInteractionComponent from "./components/pre-interaction-widget/PreInteractionComponent";
// ======================
// import PatientIntakeForm from "./components/patient-intake-form/PatientIntakeForm";
// ======================
import ChatWindow from "./components/chat-window/ChatWindow";
import { SkinConfigurations } from "./types/skinConfig";

import xRxClient, { ChatMessage } from "../../../xrx-core/react-xrx-client/src";

declare global {
  interface Window {
    webkitAudioContext: typeof AudioContext;
  }
}

const NEXT_PUBLIC_ORCHESTRATOR_HOST =
  process.env.NEXT_PUBLIC_ORCHESTRATOR_HOST || "localhost";
const NEXT_PUBLIC_ORCHESTRATOR_PORT =
  process.env.NEXT_PUBLIC_ORCHESTRATOR_PORT || "8000";
const NEXT_PUBLIC_ORCHESTRATOR_PATH =
  process.env.NEXT_PUBLIC_ORCHESTRATOR_PATH || "/api/v1/ws";
const NEXT_PUBLIC_UI_DEBUG_MODE =
  process.env.NEXT_PUBLIC_UI_DEBUG_MODE === "true";
const TTS_SAMPLE_RATE = process.env.TTS_SAMPLE_RATE || "24000";
const STT_SAMPLE_RATE = process.env.STT_SAMPLE_RATE || "16000";
const NEXT_PUBLIC_GREETING_FILENAME = process.env.NEXT_PUBLIC_GREETING_FILENAME || "pizza-greeting.mp3";
  
// see SkinConfigurations for available agents
const NEXT_PUBLIC_AGENT = process.env.NEXT_PUBLIC_AGENT || "pizza-agent";
const skinConfig = SkinConfigurations[NEXT_PUBLIC_AGENT];


export default function Home() {

  const {
    // State variables
    isRecording,
    isVoiceMode,
    isUserSpeaking,
    chatHistory,
    isAgentSpeaking,
    isAgentThinking,
    isAudioPlaying,
    showStartButton,
    isAudioGenerationDone,

    // Set functions
    setIsRecording,
    setIsVoiceMode,
    setIsUserSpeaking,
    setChatHistory,
    setIsAgentSpeaking,
    setIsAgentThinking,
    setIsAudioPlaying,
    setShowStartButton,
    setIsAudioGenerationDone,

    // Handler functions
    startAgent,
    toggleIsRecording,
    toggleVoiceMode,
    sendMessage,
    sendAction

  } = xRxClient({
    orchestrator_host: NEXT_PUBLIC_ORCHESTRATOR_HOST,
    orchestrator_port: NEXT_PUBLIC_ORCHESTRATOR_PORT,
    orchestrator_path: NEXT_PUBLIC_ORCHESTRATOR_PATH,
    greeting_filename: NEXT_PUBLIC_GREETING_FILENAME,
    orchestrator_ssl: false,
    stt_sample_rate: parseInt(STT_SAMPLE_RATE, 10),
    tts_sample_rate: parseInt(TTS_SAMPLE_RATE, 10),
  });

  const [message, setMessage] = useState("");
  const [latestWidget, setLatestWidget] = useState<{
    type: string;
    details: string;
  } | null>(null);


  const [loadingButtons, setLoadingButtons] = useState<{
    [key: string]: boolean;
  }>({});
  const [currentPage, setCurrentPage] = useState("welcome");

  /* Click Handlers */
  const handleStartClick = () => {
    startAgent();
    setCurrentPage("home");
  }

  const handleMessageChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(event.target.value);
  }
  
  const handleRecordClick = () => {
    toggleIsRecording();
  }

  const handleSendMessage = () => {
    sendMessage(message);
    setMessage('');
  }

  const handleButtonClick = (buttonId: string, action: () => void) => {
    setLoadingButtons((prevState) => ({ ...prevState, [buttonId]: true }));
    action();
  };

  const showDetails = (element: any, productId: number) => {
    handleButtonClick(`details-${productId}`, () => {
      console.log("Showing details for product", productId);
      sendAction("get_product_details", { product_id: productId });
    });
  };

  const addToCart = (variantId: number, quantity: number) => {
    handleButtonClick(`add-${variantId}`, () => {
      console.log("Adding to cart:", variantId, quantity);
      sendAction("add_item_to_cart", {
        variant_id: variantId,
        quantity: quantity
      });
    });
  };

  const deleteFromCart = (element: any, variantId: number) => {
    handleButtonClick(`delete-${variantId}`, () => {
      console.log("Deleting from cart:", variantId);
      sendAction("delete_item_from_cart", { variant_id: variantId });
    });
  };

  const submitOrder = (element: any) => {
    handleButtonClick("submit-order", () => {
      console.log("Submitting order");
      sendAction("submit_cart_for_order", {});
    });
  };

  const renderWidget = useCallback(
    (widget: any) => {
      if (!widget) {
        if (!NEXT_PUBLIC_AGENT) {
          return null;
        } else {
          widget = {
            type: "pre-interaction",
            details: "{}"
          };
        }
      }

      let details: any;
      try {
        details = JSON.parse(widget.details);
      } catch (error) {
        console.error(
          "Error: Invalid JSON received for widget:",
          JSON.stringify(error)
        );
        console.log(widget.details);
        details = [];
      }

      switch (widget.type) {
        case "shopify-product-list":
          return (
            <Menu
              products={details}
              loadingButtons={loadingButtons}
              showDetails={showDetails}
            />
          );

        case "shopify-product-details":
          return (
            <ProductDetails
              loadingButtons={loadingButtons}
              product={details}
              add_to_cart={addToCart}
              chatHistory={chatHistory}
            />
          );

        case "shopify-cart-summary":
          return (
            <>
              <Cart
                cart={details}
                loadingButtons={loadingButtons}
                deleteAction={deleteFromCart}
              />
              <BottomCTA
                onClick={submitOrder}
                isDisabled={details.cart_summary.line_items.length === 0}
                isLoading={loadingButtons["submit-order"]}
              >
                <span>ORDER NOW</span>
                <Image
                  src="/right-caret.svg"
                  width={40}
                  height={40}
                  alt="Right Caret"
                />
              </BottomCTA>
            </>
          );

        case "shopify-order-confirmation":
          setCurrentPage("order-confirmation");
          if (isRecording) {
            // make sure we mute the mic when we show the order confirmation
            handleRecordClick();
          }
          return null;
        // ======================
        // case "patient-information":
        //   return <PatientIntakeForm details={details} />;
        // ======================
        case "pre-interaction":
          return <PreInteractionComponent agentType={NEXT_PUBLIC_AGENT} />;
        default:
          return null;
      }
    },
    [loadingButtons, latestWidget]
  );

  useEffect(() => {
    const lastMessage = chatHistory.findLast((chat) => chat.type === "widget");
    if (lastMessage) {
      setLatestWidget(lastMessage.message as any);
    }
    setLoadingButtons({});
  }, [chatHistory]);

  return (
    <main className={styles.mainContainer}>
      {currentPage === "welcome" && (
        <WelcomeScreen onStart={handleStartClick} config={skinConfig} />
      )}
      {currentPage === "home" && (
        <>
          <div className={styles.logoContainer}>
            <motion.div
              key={isAgentThinking ? "thinking" : "not-thinking"}
              className={`${styles.logo} ${
                isAgentThinking && !isAgentSpeaking ? styles.pulsating : ""
              }`}
              animate={isAgentThinking ? { scale: [1, 1.1, 1] } : { scale: 1 }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              <Image
                src={skinConfig.logoSrc}
                alt="Main Icon"
                width={80}
                height={80}
              />
            </motion.div>
            {isAgentSpeaking && (
              <motion.div
                className={styles.talkingIndicator}
                initial={{ scaleY: 0 }}
                animate={{ scaleY: [0, 1, 0] }}
                transition={{ repeat: Infinity, duration: 0.8 }}
              />
            )}
          </div>
          <motion.div
            key={isVoiceMode ? "voice" : "chat"}
            className={styles.interactionContainer}
            initial={{ y: 0, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{
              type: "inertia",
              stiffness: 500,
              damping: 25,
              delay: 0.05,
              bounce: 0.5,
              mass: 1.2,
              velocity: 2
            }}
          >
            {isVoiceMode ? (
              renderWidget(latestWidget)
            ) : (
              <ChatWindow
                chatHistory={chatHistory}
                isVoiceMode={isVoiceMode}
                message={message}
                handleMessageChange={(
                  event: React.ChangeEvent<HTMLTextAreaElement>
                ) => setMessage(event.target.value)}
                handleSendMessage={handleSendMessage}
              />
            )}
          </motion.div>

          <motion.div
            className={styles.controlContainer}
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 30,
              delay: 0.2
            }}
          >
            {" "}
            <div className={styles.listeningIndicatorContainer}>
              {isUserSpeaking && (
                <motion.div
                  className={styles.listeningIndicator}
                  initial={{ scaleY: 0 }}
                  animate={{ scaleY: [0, 1, 0] }}
                  transition={{ repeat: Infinity, duration: 0.8 }}
                />
              )}
            </div>
            <div className={styles.buttonsContainer}>
              {NEXT_PUBLIC_UI_DEBUG_MODE && (
                <motion.button
                  className={styles.controlButton}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={toggleVoiceMode}
                >
                  <Image
                    className={styles.controlIcon}
                    src={
                      isVoiceMode
                        ? "/switch-to-chat-icon.svg"
                        : "/switch-to-voice-icon.svg"
                    }
                    width={60}
                    height={60}
                    alt="Switch Mode Icon"
                  />
                  <span className={styles.controlLabel}>
                    {isVoiceMode ? "Chat" : "Voice"}
                  </span>
                </motion.button>
              )}
              <motion.button
                className={`${styles.controlButton} ${styles.endButton}`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => window.location.reload()}
              >
                <Image
                  className={styles.controlIcon}
                  src="/end-call-icon.svg"
                  width={NEXT_PUBLIC_UI_DEBUG_MODE ? 75 : 60}
                  height={NEXT_PUBLIC_UI_DEBUG_MODE ? 75 : 60}
                  alt="End Call Icon"
                />
                <span className={styles.controlLabel}>End</span>
              </motion.button>
              <motion.button
                className={`${styles.controlButton} ${styles.muteButton}`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleRecordClick}
              >
                <Image
                  className={styles.controlIcon}
                  src={isRecording ? "/mic_on.svg" : "/mic_off.svg"}
                  width={60}
                  height={60}
                  alt="Microphone Icon"
                />

                <span className={styles.controlLabel}>
                  {isRecording ? "Mute" : "Unmute"}
                </span>
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
      {currentPage === "order-confirmation" && (
        <OrderConfirmation confirmation={JSON.parse(latestWidget!.details)} />
      )}
    </main>
  );
}
