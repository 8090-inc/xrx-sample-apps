"use client";
jsx;

import Image from "next/image";
import { useRef, useState, useEffect, useCallback } from "react"
import { jsx } from "react/jsx-runtime";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'
import { useMicVAD } from "@ricky0123/vad-react"
import { ScaleLoader, SyncLoader, HashLoader, PulseLoader } from "react-spinners";

declare global {
  interface Window {
    webkitAudioContext: typeof AudioContext;
  }
}

const NEXT_PUBLIC_ORCHESTRATOR_HOST = process.env.NEXT_PUBLIC_ORCHESTRATOR_HOST || "localhost";
const NEXT_PUBLIC_ORCHESTRATOR_PORT = process.env.NEXT_PUBLIC_ORCHESTRATOR_PORT || "8090";
const NEXT_PUBLIC_ORCHESTRATOR_PATH = process.env.NEXT_PUBLIC_ORCHESTRATOR_PATH || "/api/v1/ws";
const NEXT_PUBLIC_GREETING_FILENAME = process.env.NEXT_PUBLIC_GREETING_FILENAME || "greeting.mp3";
const NEXT_PUBLIC_UI_DEBUG_MODE = process.env.NEXT_PUBLIC_UI_DEBUG_MODE === "true";

export default function Home() {

  const recordingContextRef = useRef<AudioContext | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const [isAudioContextStarted, setIsAudioContextStarted] = useState(false);
  const incomingAudioBufferRef = useRef<ArrayBuffer[]>([]);
  const isPlayingAudioRef = useRef(false);
  
  const [isRecording, setIsRecording] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(true);
  const [isSpeechDetected, setIsSpeechDetected] = useState(false);
  const isSpeechDetectedRef = useRef(false);

  const mediaRecorderRef = useRef<ScriptProcessorNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [isIconAnimated, setIsIconAnimated] = useState(false);
  const [isAgentThinking, setIsAgentThinking] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [loadingButtons, setLoadingButtons] = useState<{ [key: string]: boolean }>({});
  const currentBufferSourceRef = useRef<AudioBufferSourceNode | null>(null);

  const [showStartButton, setShowStartButton] = useState(true);
  const [isAudioGenerationDone, setIsAudioGenerationDone] = useState(false);

  const widgetQueueRef = useRef<ChatMessage[]>([]); // queue used for widgets to make them play at the right time

  useEffect(() => {
    const matchMedia = window.matchMedia('(prefers-color-scheme: dark)');
    setIsDarkMode(matchMedia.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setIsDarkMode(e.matches);
    };

    matchMedia.addEventListener('change', handleChange);

    return () => {
      matchMedia.removeEventListener('change', handleChange);
    };
  }, []);

  useEffect(() => {
    isSpeechDetectedRef.current = isSpeechDetected;
  }, [isSpeechDetected]);

  const vad = useMicVAD({
    startOnLoad: true,
    onSpeechStart: () => {
      if(isRecording.valueOf()) {
        console.log("User started talking");
        setIsSpeechDetected(true);
        incomingAudioBufferRef.current = [];
        setIsAudioPlaying(false);

        // Stop the current BufferSource if it's playing
        if (currentBufferSourceRef.current) {
          console.log("stopping the current playback");
          currentBufferSourceRef.current.stop();
          currentBufferSourceRef.current.disconnect();
          currentBufferSourceRef.current = null;
        }
      } else {
        setIsSpeechDetected(false);
      }
    },
    onSpeechEnd: (audio) => {
      console.log("User stopped talking");
      setIsSpeechDetected(false);
    }
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const iconAnimationTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory]);

  /*
  useEffect (() => {
    // initialize playback contetx
    if(!playbackContextRef.current) {
      playbackContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });
    }
  },[recordingContextRef, playbackContextRef, isAudioContextStarted, setIsAudioContextStarted]);
*/

  type ChatMessage = {
    sender: string;
    message: string;
    widget?: any;
    timestamp: Date;
    type?: string;
  };

  const playReceivedAudio = useCallback((arrayBuffer: ArrayBuffer | null) => {
    if (playbackContextRef.current) {
      if (arrayBuffer !== null && !isSpeechDetectedRef.current) {
        incomingAudioBufferRef.current.push(arrayBuffer as ArrayBuffer);
      }
      if (incomingAudioBufferRef.current.length > 0 && !isPlayingAudioRef.current && !isSpeechDetectedRef.current) {

        const audioData = incomingAudioBufferRef.current.shift() as ArrayBuffer;
        const int16Array = new Int16Array(audioData);

        if (!isIconAnimated) {
          setIsIconAnimated(true);
          console.log("starting icon animation");
        }
        const durationSec = (int16Array.length / 16000);
        console.log("received audio of duration : " + durationSec);
        if (iconAnimationTimeout.current) {
          clearTimeout(iconAnimationTimeout.current as NodeJS.Timeout);
        }
        iconAnimationTimeout.current = setTimeout(() => {
          console.log("stopping icon animation");
          setIsIconAnimated(false);
        }, durationSec * 1000);

        const float32Array = new Float32Array(int16Array.length);
        for (let i = 0; i < int16Array.length; i++) {
          float32Array[i] = int16Array[i] / 0x8000;
        }

        const channels = 1;
        const sampleRate = 16000;
        const buffer = playbackContextRef.current.createBuffer(channels, float32Array.length, sampleRate);
        buffer.getChannelData(0).set(float32Array);

        const source = playbackContextRef.current.createBufferSource();
        source.buffer = buffer;
        source.connect(playbackContextRef.current.destination);
        source.start();
        currentBufferSourceRef.current = source; // Store the reference to the current BufferSource
        console.log("start playing audio");
        isPlayingAudioRef.current = true;
        setIsAudioPlaying(true);
        console.log("isPlayingAudioRef.current after start:", isPlayingAudioRef.current);
        source.onended = () => {
          source.disconnect();
          isPlayingAudioRef.current = false;
          console.log("end playing audio");
          setIsAudioPlaying(false);
          console.log("isPlayingAudioRef.current after end:", isPlayingAudioRef.current);
          playReceivedAudio(null);
          processWidgetQueue(); // Process the widget queue after audio ends
        }
      }
    }
  }, [isIconAnimated, isSpeechDetected, isPlayingAudioRef, isSpeechDetectedRef]);

  const processWidgetQueue = () => {
    console.log(`processing the widget queue with length: ${widgetQueueRef.current.length}`);
    while (widgetQueueRef.current.length > 0 && !isPlayingAudioRef.current) {
      const widgetMessage = widgetQueueRef.current.shift();
      if (widgetMessage) {
        setChatHistory(currentChatHistory => [
          ...currentChatHistory,
          widgetMessage
        ]);
      }
    }
  };

  useEffect(() => {
    if (!socketRef.current) {

      const socket = new WebSocket(`ws://${NEXT_PUBLIC_ORCHESTRATOR_HOST}:${NEXT_PUBLIC_ORCHESTRATOR_PORT}${NEXT_PUBLIC_ORCHESTRATOR_PATH}`);
      socketRef.current = socket;
      socket.binaryType = 'arraybuffer';

      socket.onopen = () => {
        console.log("WebSocket connection established");
      };

      socketRef.current.onmessage = (event) => {
        console.log("Message received from server :" + event);
        if (typeof event.data === 'string') {
          const message = JSON.parse(event.data);
          let content, widget:any;
          if (message.type === 'widget') {
            console.log(`widget received from server side and audio playing has value: ${isPlayingAudioRef.current}`);
            widget = message.content;
            content = '';
            
            if (isPlayingAudioRef.current) {
              // Enqueue the widget message if audio is playing
              console.log(`queuing the widget message`);
              widgetQueueRef.current.push({
                sender: message.user,
                type: message.type,
                message: message.content,
                timestamp: new Date()
              });
              console.log(`widget queue length: ${widgetQueueRef.current.length}`);
            } else {
              // Display the widget message immediately if audio is not playing
              setChatHistory(currentChatHistory => [
                ...currentChatHistory,
                { sender: message.user, type: message.type, message: message.content, timestamp: new Date() }
              ]);
            }
          } else if(message.type === 'action') {
            if(message.content === 'agent_started_thinking') {
              setIsAgentThinking(true);
            } else if(message.content === 'agent_ended_thinking') {
              // wait a small amount of time here before making this change to allow for better animation
              setTimeout(() => {
                setIsAgentThinking(false);
              }, 800);
            }

            // determine if the audio has been generated which is currently playing
            if(message.content === 'audio_generation_done') {
              console.log(`audio generation done from server side and audio playing has value: ${isPlayingAudioRef.current}`);
              setIsAudioGenerationDone(true);
            }

            // perform action such as cancel audio.
            if(message.content === 'clear_audio_buffer') {
              console.log("Clearing audio buffer");
              incomingAudioBufferRef.current = [];
              setIsAudioPlaying(false);
            }
            return; // do not continue or set the chat history
          }
          else {
            content = message.content;
            setChatHistory(currentChatHistory => [
              ...currentChatHistory,
              { sender: message.user, type: message.type, message: message.content, timestamp: new Date() }
            ]);
          }

        } else if (event.data instanceof ArrayBuffer) {
          // Handle binary messages
          console.log("Binary message received, starting audio playback");
          playReceivedAudio(event.data);
        }
      }

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      socket.onclose = () => {
        console.log("WebSocket connection closed");
      };

    };
  }, [playReceivedAudio, isSpeechDetected]);

  const sendPCMData = useCallback((pcmData: Int16Array) => {
    // Send PCM data to the WebSocket server if the connection is open
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(pcmData.buffer);
    }
  }, [socketRef.current]);

  const startAudioCapture = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.error("MediaDevices are not supported by this browser.");
      return;
    }

    if (!recordingContextRef.current) {
      recordingContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });
      console.log(`AudioContext CREATED ${recordingContextRef.current}`);
    } else {
      await recordingContextRef.current.resume();
      console.log(`AudioContext RESUMED ${recordingContextRef.current}`);
    }

    setIsAudioContextStarted(true);

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
    const mediaStreamSource = recordingContextRef.current.createMediaStreamSource(stream);
    mediaStreamRef.current = stream;

    // Create a ScriptProcessorNode to process the audio data
    const scriptProcessor = recordingContextRef.current.createScriptProcessor(4096, 1, 1);
    mediaRecorderRef.current = scriptProcessor; // Store the reference

    // Connect the media stream source to the script processor
    mediaStreamSource.connect(scriptProcessor);

    // Connect the script processor to the audio context destination (speakers)
    scriptProcessor.connect(recordingContextRef.current.destination);

    // Event handler for processing the audio data
    scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
      const inputBuffer = audioProcessingEvent.inputBuffer;

      for (let channel = 0; channel < inputBuffer.numberOfChannels; channel++) {
        const inputData = inputBuffer.getChannelData(channel);
        const pcmData = new Int16Array(inputData.length);

        // Convert Float32Array data to Int16Array data
        for (let sample = 0; sample < inputData.length; sample++) {
          const normalizedSample = Math.max(-1, Math.min(1, inputData[sample]));
          pcmData[sample] = normalizedSample < 0
            ? normalizedSample * 0x8000
            : normalizedSample * 0x7FFF;
        }

        // Send PCM data to WebSocket server
        sendPCMData(pcmData);
      }
    };
  }, [sendPCMData]);

  const stopAudioCapture = useCallback(() => {
    if (recordingContextRef.current) {
      // Disconnect the script processor from the audio context's destination
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.disconnect();
        mediaRecorderRef.current.onaudioprocess = null; // Clear the event handler
        mediaRecorderRef.current = null; // Clear the reference
      }

      // Suspend the audio context instead of closing it
      recordingContextRef.current.suspend().then(() => {
        console.log("AudioContext suspended");
      });
    }

    setIsRecording(false);
  }, [recordingContextRef, mediaStreamRef]);

  const handleRecordClick = useCallback(() => {
    if(!playbackContextRef.current) {
      playbackContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });
    }
    if (!isRecording) {
      setShowStartButton(false);
      startAudioCapture();
      setIsRecording(true);
    } else {
      setIsAudioContextStarted(false);
      setIsRecording(false);
      stopAudioCapture();
    }
  }, [isRecording, startAudioCapture, stopAudioCapture]);


  const handleStartClick = useCallback(() => {
    const audio = new Audio(`/${NEXT_PUBLIC_GREETING_FILENAME}`);
    audio.play();
    setIsIconAnimated(true);
    audio.onended = () => {
      setIsIconAnimated(false);
    }
    setShowStartButton(false);
    if(!isRecording) {
      handleRecordClick();
    }
  }, [isRecording, isIconAnimated, handleRecordClick]);


  const handleMessageChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(event.target.value);
  }

  const toggleVoiceMode = useCallback(() => {
    if(isVoiceMode === true) {
      setIsVoiceMode(false);
      setIsRecording(false);
      setShowStartButton(false);
    } else {
      setIsVoiceMode(true);
    }
  }, [isVoiceMode, setIsVoiceMode, isRecording, setIsRecording, handleRecordClick]);

  const handleSendMessage = async () => {
    try {
      if (socketRef.current) {
        const payload = {
          type: 'text',
          content: message
        }
        socketRef.current.send(JSON.stringify(payload));
        console.log("Message sent successfully:", message);

        setChatHistory(currentChatHistory => [
          ...currentChatHistory,
          { sender: 'user', message: `${message}`, timestamp: new Date() }
        ]);

        setMessage('');

      }
    } catch (error) {
      console.error("Error sending message to backend:", error);
    }
  }

  const sendAction = async (tool: string, parameters: any) => {
    try {
      if (socketRef.current) {
        const payload = {
          type: 'action',
          content: {
            tool: tool,
            parameters: JSON.stringify(parameters)
          },
          modality: isVoiceMode ? 'audio' : 'text'
        }
        socketRef.current.send(JSON.stringify(payload));
        console.log("Action sent successfully:", payload);
      }
    } catch (error) {
      console.error("Error sending action to backend:", error);
    }
  }

  const handleButtonClick = (buttonId: string, action: () => void) => {
    setLoadingButtons(prevState => ({ ...prevState, [buttonId]: true }));
    action();
  };

  const showDetails = (element: any, productId: number) => {
    handleButtonClick(`details-${productId}`, () => {
      console.log("Showing details for product", productId);
      sendAction('get_product_details', { 'product_id': productId });
    });
  };

  const addToCart = (element: any, variantId: number, quantity: number) => {
    handleButtonClick(`add-${variantId}`, () => {
      console.log("Adding to cart:", variantId, quantity);
      sendAction('add_item_to_cart', { 'variant_id': variantId, 'quantity': quantity });
    });
  };

  const removeFromCart = (element: any, variantId: number) => {
    handleButtonClick(`remove-${variantId}`, () => {
      console.log("Removing from cart:", variantId);
      sendAction('remove_item_from_cart', { 'variant_id': variantId });
    });
  };

  const submitOrder = (element: any) => {
    handleButtonClick('submit-order', () => {
      console.log("Submitting order");
      sendAction('submit_cart_for_order', {});
    });
  };

  const renderWidget = useCallback((widget: any) => {
    let details: any;

    try { 
      details = JSON.parse(widget.details);
    } catch (error) {
      console.log("Error: we received invalid json for the widget.");
      console.log(error);
      console.log(widget.details);
      details = [];
    }

    // Simple widget rendering
    return (
      <div className="widget" id="simple-widget">
        <h3>Widget Content</h3>
        <pre>{JSON.stringify(details, null, 2)}</pre>
      </div>
    );
  }, []);

  useEffect(() => {
    // Reset loading buttons state whenever chatHistory changes
    setLoadingButtons({});
  }, [chatHistory]);

  return (
    <main className="mainContainer">
      {showStartButton && (
        <div className="startButtonContainer">
          <button className="widget-button" style={{padding: '10px 30px'}} onClick={handleStartClick}>Start</button>
        </div>
      )}
      <div className="title flex-none">
        xRx Demo
      </div>      
      <div className="chatContainer flex-auto">
        <div className={`iconContainer flex ${!isVoiceMode ? 'hidden' : ''}`}>
          <SyncLoader
                  color={"#F15950"}
                  loading={isIconAnimated}
                  size={20}
                  />
          <PulseLoader
              color={"#F15950"}
              loading={!isIconAnimated && isAgentThinking}
              size={20}
              />

          <div style={{
            width: isIconAnimated || isAgentThinking ? '0px' : '50px',
            height: isIconAnimated || isAgentThinking ? '0px' : '50px',
            borderRadius: '50%',
            backgroundColor: '#F15950',
            transition: 'all 0.5s',
            position: 'absolute',
            left: '50%',
            top: '40',
            transform: isIconAnimated || isAgentThinking ? 'translate(-50%, 0) scale(0)' : 'translate(-50%, 0) scale(1)',
            transformOrigin: 'center center'
          }}></div>
          
        </div>
        <div ref={messagesEndRef} />
        {
          isVoiceMode ?
            <div className="chatMessageContainer flex">
              <div className="widgetMessageContainer">
                <div key="widget" className="chatMessage widgetMessage">
                  {chatHistory.findLast(chat => chat.type === 'widget') && renderWidget(chatHistory.findLast(chat => chat.type === 'widget')?.message)}
                </div>
              </div>
            </div>
          :
            chatHistory.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()).map((chat, index) => (
              <div key={index} className="chatMessageContainer flex">
                {chat.type === 'widget' ? (
                  <div className="widgetMessageContainer">
                    <div className={`chatMessage widgetMessage ${isVoiceMode ? 'hidden' : ''}`}>
                      {renderWidget(chat.message)}
                    </div>
                  </div>
                ) : chat.sender === 'user' ? (
                  <div className="userMessageContainer">
                    <div className={`chatMessage userMessage ${isVoiceMode ? 'hidden' : ''}`}>
                      {chat.message}
                    </div>
                  </div>
                ) : (
                  <div className="agentMessageContainer">
                    <div className={`chatMessage agentMessage ${isVoiceMode ? 'hidden' : ''}`}>
                      {chat.message}
                    </div>
                  </div>
                )}
              </div>
            ))
        }
      </div>
      <div className='inputContainer'>
        <div className='flex'>
          {
            isVoiceMode ?
            <div className="textInputContainer" >
              <div id='speechDetection' style={{ justifyContent: 'center' }}>
                <ScaleLoader
                  className="voiceIndicator"
                  color={"rgb(var(--foreground-rgb))"}
                  loading={isSpeechDetected}
                  radius={10}
                  height={20}
                  width={20}
                  speedMultiplier={2}
                />
                <ScaleLoader
                  className="voiceIndicator"
                  color={"rgb(var(--foreground-rgb))"}
                  loading={!isSpeechDetected}
                  radius={5}
                  height={7}
                  width={20}
                  speedMultiplier={0.00001}
                />
                <Image
                  className="micButton"
                  src={isRecording ? isDarkMode ? "/mic_on_white.svg" : "/mic_on.svg" : isDarkMode ? "/mic_off_white.svg" : "/mic_off.svg"}
                  width={50}
                  height={50}
                  alt="Microphone Icon"
                  onClick={handleRecordClick}
                  style={{ marginLeft: 'auto' }}
                />
              </div>
            </div>
          :
          <div className="textInputContainer">
            <textarea
              placeholder="Type your message..."
              className="flex-auto textInputBox"
              value={message}
              onChange={handleMessageChange}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault(); 
                  handleSendMessage();
                }
              }}
            />
            <Image
              src={isDarkMode ? "/send_white.svg" : "/send.svg"}
              width={35}
              height={35}
              alt="Send Message"
              className="sendButton"
              style={{float: 'right'}}
              onClick={handleSendMessage}
            />
          </div>
          }
        </div>   
        <div className='speechControls'>
          {NEXT_PUBLIC_UI_DEBUG_MODE && (
            <button className="modeButton" onClick={() => toggleVoiceMode()}>
              <Image
                src={isVoiceMode ? '/chat.svg' : '/mic_on.svg'} 
                width={20} 
                height={10} 
                alt="Microphone Icon"
              />
              <span>{isVoiceMode ? 'Toggle to text mode' : 'Toggle to audio mode'}</span>
            </button>
          )}
        </div>    
      </div>
    </main>
  );
}