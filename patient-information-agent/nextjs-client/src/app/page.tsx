"use client";
jsx;

import Image from "next/image";
import { useRef, useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { jsx } from "react/jsx-runtime";
import { MicVAD } from "@ricky0123/vad-web";
// ======================
// import Cart from "./components/cart/Cart";
// import ProductDetails from "./components/product-details/ProductDetails";
// import OrderConfirmation from "./components/order-confirmation/OrderConfirmation";
// import Menu from "./components/menu/Menu";
// ======================
import styles from "./Home.module.css";
import WelcomeScreen from "./components/welcome-screen/WelcomeScreen";
import { BottomCTA } from "./components/base/Base";
import PreInteractionComponent from "./components/pre-interaction-widget/PreInteractionComponent";
import PatientIntakeForm from "./components/patient-intake-form/PatientIntakeForm";
import ChatWindow from "./components/chat-window/ChatWindow";
import { ChatMessage } from "./types/chat";
import { SkinConfigurations } from "./types/skinConfig";

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

const skinConfig = SkinConfigurations["patient-information-agent"];

// Change this line near the top of the file
const TTS_SAMPLE_RATE = process.env.TTS_SAMPLE_RATE || "24000";

export default function Home() {
  const recordingContextRef = useRef<AudioContext | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const incomingAudioBufferRef = useRef<ArrayBuffer[]>([]);
  const isPlayingAudioRef = useRef(false);

  const [isMicOn, setIsMicOn] = useState(false);
  const isMicOnRef = useRef(false);
  const [isVoiceMode, setIsVoiceMode] = useState(true);
  const [isSpeechDetected, setIsSpeechDetected] = useState(false);
  const isSpeechDetectedRef = useRef(false);

  const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [latestWidget, setLatestWidget] = useState<{
    type: string;
    details: string;
  } | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const [isAgentThinking, setIsAgentThinking] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);

  const agentSpeakingTimeout = useRef<NodeJS.Timeout | null>(null);

  const [loadingButtons, setLoadingButtons] = useState<{
    [key: string]: boolean;
  }>({});
  const currentBufferSourceRef = useRef<AudioBufferSourceNode | null>(null);

  const [currentPage, setCurrentPage] = useState("welcome");
  const widgetQueueRef = useRef<ChatMessage[]>([]); // queue used for widgets to make them play at the right time

  useEffect(() => {
    const initializeVAD = async () => {
      console.log(`initializing the VAD`);
      const micVAD = await MicVAD.new({
        minSpeechFrames: 5,
        onSpeechStart: () => {
          if (isMicOnRef.current) {
            setIsSpeechDetected(true);
            console.log("User started talking");
            incomingAudioBufferRef.current = [];

            if (currentBufferSourceRef.current) {
              console.log("stopping the current playback");
              currentBufferSourceRef.current.stop();
              currentBufferSourceRef.current.disconnect();
              currentBufferSourceRef.current = null;
            }
          } else {
            console.log("User stopped talking");
            setIsSpeechDetected(false);
          }
        },
        onSpeechEnd: (audio) => {
          console.log("User stopped talking");
          setIsSpeechDetected(false);
        }
      });
      micVAD.start();
    };
    initializeVAD();
  }, []);

  useEffect(() => {
    isSpeechDetectedRef.current = isSpeechDetected;
    isMicOnRef.current = isMicOn;
  }, [isSpeechDetected, isMicOn]);

  const playReceivedAudio = useCallback(
    (arrayBuffer: ArrayBuffer | null) => {
      if (playbackContextRef.current) {
        if (arrayBuffer !== null && !isSpeechDetectedRef.current) {
          incomingAudioBufferRef.current.push(arrayBuffer as ArrayBuffer);
        }
        if (
          incomingAudioBufferRef.current.length > 0 &&
          !isPlayingAudioRef.current &&
          !isSpeechDetectedRef.current
        ) {
          const audioData =
            incomingAudioBufferRef.current.shift() as ArrayBuffer;
          const int16Array = new Int16Array(audioData);

          if (!isAgentSpeaking) {
            setIsAgentSpeaking(true);
            console.log("starting icon animation");
          }

          const durationSec = int16Array.length / 16000;
          if (durationSec === 0) {
            return;
          }
          if (agentSpeakingTimeout.current) {
            clearTimeout(agentSpeakingTimeout.current as NodeJS.Timeout);
          }
          agentSpeakingTimeout.current = setTimeout(() => {
            console.log("stopping icon animation");
            setIsAgentSpeaking(false);
          }, durationSec * 1000);

          const float32Array = new Float32Array(int16Array.length);
          for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 0x8000;
          }

          const channels = 1;
          const sampleRate = parseInt(TTS_SAMPLE_RATE, 10);
          const buffer = playbackContextRef.current.createBuffer(
            channels,
            float32Array.length,
            sampleRate
          );
          buffer.getChannelData(0).set(float32Array);

          const source = playbackContextRef.current.createBufferSource();
          source.buffer = buffer;
          source.connect(playbackContextRef.current.destination);
          source.start();
          currentBufferSourceRef.current = source; // Store the reference to the current BufferSource
          console.log("start playing audio");
          isPlayingAudioRef.current = true;

          source.onended = () => {
            source.disconnect();
            isPlayingAudioRef.current = false;
            console.log("end playing audio");
            playReceivedAudio(null);
            processWidgetQueue(); // Process the widget queue after audio ends
          };
        }
      }
    },
    [isPlayingAudioRef, isSpeechDetectedRef, isAgentSpeaking]
  );

  useEffect(() => {
    if (!socketRef.current) {
      const socket = new WebSocket(
        `ws://${NEXT_PUBLIC_ORCHESTRATOR_HOST}:${NEXT_PUBLIC_ORCHESTRATOR_PORT}${NEXT_PUBLIC_ORCHESTRATOR_PATH}`
      );
      socketRef.current = socket;
      socket.binaryType = "arraybuffer";

      socket.onopen = () => {
        console.log("WebSocket connection established");
      };

      socketRef.current.onmessage = (event) => {
        console.log("Message received from server :" + event);
        if (typeof event.data === "string") {
          const message = JSON.parse(event.data);
          let content, widget: any;
          if (message.type === "widget") {
            widget = message.content;
            content = "";
            if (isPlayingAudioRef.current) {
              // Enqueue the widget message if audio is playing
              console.log(`queuing the widget message`);
              widgetQueueRef.current.push({
                sender: message.user,
                type: message.type,
                message: message.content,
                timestamp: new Date()
              });
              console.log(
                `widget queue length: ${widgetQueueRef.current.length}`
              );
            } else {
              // Display the widget message immediately if audio is not playing
              setChatHistory((currentChatHistory) => [
                ...currentChatHistory,
                {
                  sender: message.user,
                  type: message.type,
                  message: message.content,
                  timestamp: new Date()
                }
              ]);
            }
          } else if (message.type === "action") {
            if (message.content === "agent_started_thinking") {
              setIsAgentThinking(true);
            } else if (message.content === "agent_ended_thinking") {
              setTimeout(() => {
                setIsAgentThinking(false);
              }, 800);
            }
            if (message.content === "clear_audio_buffer") {
              console.log("Clearing audio buffer");
              incomingAudioBufferRef.current = [];
            }
            return; // do not continue or set the chat history
          } else {
            content = message.content;

            setChatHistory((currentChatHistory) => [
              ...currentChatHistory,
              {
                sender: message.user,
                type: message.type,
                message: message.content,
                timestamp: new Date()
              }
            ]);
          }
        } else if (event.data instanceof ArrayBuffer) {
          // Handle binary messages
          playReceivedAudio(event.data);
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      socket.onclose = () => {
        console.log("WebSocket connection closed");
      };
    }
  }, [playReceivedAudio, isSpeechDetected]);

  const sendPCMData = useCallback(
    (pcmData: Int16Array) => {
      // Send PCM data to the WebSocket server if the connection is open
      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(pcmData.buffer);
      }
    },
    [socketRef.current]
  );

  const processWidgetQueue = () => {
    console.log(
      `processing the widget queue with length: ${widgetQueueRef.current.length}`
    );
    while (widgetQueueRef.current.length > 0 && !isPlayingAudioRef.current) {
      const widgetMessage = widgetQueueRef.current.shift();
      if (widgetMessage) {
        setChatHistory((currentChatHistory) => [
          ...currentChatHistory,
          widgetMessage
        ]);
      }
    }
  };

  const startAudioCapture = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error("MediaDevices are not supported by this browser.");
      return;
    }

    if (!recordingContextRef.current) {
      recordingContextRef.current = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: 16000
      });
      console.log(`AudioContext CREATED ${recordingContextRef.current}`);
      await recordingContextRef.current.audioWorklet.addModule(
        "/audio-processor.js"
      );
    } else {
      console.log(`AudioContext RESUMED ${recordingContextRef.current}`);
    }

    // Request permission to access the microphone and get the audio stream
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        noiseSuppression: true,
        autoGainControl: true,
        echoCancellation: true
      }
    });
    let track = stream.getAudioTracks()[0];

    // Create a MediaStreamSource from the audio stream
    const mediaStreamSource =
      recordingContextRef.current.createMediaStreamSource(stream);
    mediaStreamRef.current = stream;

    // Create a AudioWorkletNode to process the audio data
    let workletNode = audioWorkletNodeRef.current;
    if (!workletNode) {
      workletNode = new AudioWorkletNode(
        recordingContextRef.current,
        "audio-processor"
      );
      audioWorkletNodeRef.current = workletNode;
    }

    // Connect the media stream source to the worklet node
    mediaStreamSource.connect(workletNode);

    // Connect the worklet node to the audio context destination (speakers)
    workletNode.connect(recordingContextRef.current.destination);
    workletNode.port.onmessage = (event) => {
      if (event.data.pcmData) {
        sendPCMData(event.data.pcmData);
      }
    };
  }, [sendPCMData]);

  const stopAudioCapture = useCallback(() => {
    if (recordingContextRef.current) {
      // Disconnect the worklet node from the audio context's destination
      if (audioWorkletNodeRef.current) {
        audioWorkletNodeRef.current.disconnect();
      }
      // Stop all tracks in the MediaStream
      if (mediaStreamRef.current) {
        const track = mediaStreamRef.current.getAudioTracks()[0];
        if (track) {
          track.enabled = false; // This effectively mutes the track
        }
      }
    }
  }, [recordingContextRef, mediaStreamRef]);

  const handleRecordClick = useCallback(() => {
    if (!playbackContextRef.current) {
      playbackContextRef.current = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: parseInt(TTS_SAMPLE_RATE, 10)
      });
    }

    if (!isMicOn) {      
      startAudioCapture();
      setIsMicOn(true);
    } else {      
      stopAudioCapture();
      setIsMicOn(false);
      setIsSpeechDetected(false);
    }
  }, [startAudioCapture, stopAudioCapture, isMicOn]);

  const handleStartClick = useCallback(() => {
    if (!playbackContextRef.current) {
      playbackContextRef.current = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: parseInt(TTS_SAMPLE_RATE, 10)
      });
    }

    const audio = new Audio(`${skinConfig.greetingSrc}`);
    setIsAgentSpeaking(true);
    audio.play();
    setCurrentPage("home");
    audio.onended = () => {
      setIsAgentSpeaking(false);
    };

    handleRecordClick();
  }, [isAgentSpeaking, handleRecordClick]);

  const toggleVoiceMode = useCallback(() => {
    if (isVoiceMode === true) {
      setIsVoiceMode(false);
      stopAudioCapture();
      setIsMicOn(false);
    } else {
      setIsVoiceMode(true);
    }
  }, [isVoiceMode, handleRecordClick, isMicOn]);

  const handleSendMessage = async () => {
    try {
      if (socketRef.current) {
        const payload = {
          type: "text",
          content: message
        };
        socketRef.current.send(JSON.stringify(payload));
        console.log("Message sent successfully:", message);

        setChatHistory((currentChatHistory) => [
          ...currentChatHistory,
          { sender: "user", message: `${message}`, timestamp: new Date() }
        ]);

        setMessage("");
      }
    } catch (error) {
      console.error("Error sending message to backend:", error);
    }
  };

  const sendAction = async (tool: string, parameters: any) => {
    try {
      if (socketRef.current) {
        const payload = {
          type: "action",
          content: {
            tool: tool,
            parameters: JSON.stringify(parameters)
          },
          modality: isVoiceMode ? "audio" : "text"
        };
        socketRef.current.send(JSON.stringify(payload));
        console.log("Action sent successfully:", payload);
      }
    } catch (error) {
      console.error("Error sending action to backend:", error);
    }
  };

  const handleButtonClick = (buttonId: string, action: () => void) => {
    setLoadingButtons((prevState) => ({ ...prevState, [buttonId]: true }));
    action();
  };

  const renderWidget = useCallback(
    (widget: any) => {
      if (!widget) {
        widget = {
          type: "pre-interaction",
          details: "{}"
        };
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

      // ======================
      // switch (widget.type) {
      //   case "shopify-product-list":
      //     return (
      //       <Menu
      //         products={details}
      //         loadingButtons={loadingButtons}
      //         showDetails={showDetails}
      //       />
      //     );

      //   case "shopify-product-details":
      //     return (
      //       <ProductDetails
      //         loadingButtons={loadingButtons}
      //         product={details}
      //         add_to_cart={addToCart}
      //         chatHistory={chatHistory}
      //       />
      //     );

      //   case "shopify-cart-summary":
      //     return (
      //       <>
      //         <Cart
      //           cart={details}
      //           loadingButtons={loadingButtons}
      //           deleteAction={deleteFromCart}
      //         />
      //         <BottomCTA
      //           onClick={submitOrder}
      //           isDisabled={details.cart_summary.line_items.length === 0}
      //           isLoading={loadingButtons["submit-order"]}
      //         >
      //           <span>ORDER NOW</span>
      //           <Image
      //             src="/right-caret.svg"
      //             width={40}
      //             height={40}
      //             alt="Right Caret"
      //           />
      //         </BottomCTA>
      //       </>
      //     );

      //   case "shopify-order-confirmation":
      //     setCurrentPage("order-confirmation");
      //     if (isMicOn) {
      //       // make sure we mute the mic when we show the order confirmation
      //       handleRecordClick();
      //     }
      //     return null;
      // ======================
      if (widget.type === "patient-information") {
        return <PatientIntakeForm details={details} />;
      } else if (widget.type === "pre-interaction") {
        return <PreInteractionComponent agentType={"patient-information-agent"} />;
      } else {
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
              {isSpeechDetected && (
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
                  src={isMicOn ? "/mic_on.svg" : "/mic_off.svg"}
                  width={60}
                  height={60}
                  alt="Microphone Icon"
                />

                <span className={styles.controlLabel}>
                  {isMicOn ? "Mute" : "Unmute"}
                </span>
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
      {/* ======================
      {currentPage === "order-confirmation" && (
        <OrderConfirmation confirmation={JSON.parse(latestWidget!.details)} />
      )}
      ====================== */}
    </main>
  );
}
