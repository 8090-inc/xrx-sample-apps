"use client";
jsx;

import Image from "next/image";
import { useRef, useState, useEffect, useCallback } from "react"
import { jsx } from "react/jsx-runtime";
import { ScaleLoader, SyncLoader, HashLoader, PulseLoader } from "react-spinners";
import xRxClient, { ChatMessage } from "../../../xrx-core/react-xrx-client/src";
import { useMicVAD } from "@ricky0123/vad-react"

const NEXT_PUBLIC_ORCHESTRATOR_HOST = process.env.NEXT_PUBLIC_ORCHESTRATOR_HOST || "localhost";
const NEXT_PUBLIC_ORCHESTRATOR_PORT = process.env.NEXT_PUBLIC_ORCHESTRATOR_PORT || "8000";
const NEXT_PUBLIC_ORCHESTRATOR_PATH = process.env.NEXT_PUBLIC_ORCHESTRATOR_PATH || "/api/v1/ws";
const NEXT_PUBLIC_GREETING_FILENAME = process.env.NEXT_PUBLIC_GREETING_FILENAME || "greeting.mp3";
const NEXT_PUBLIC_UI_DEBUG_MODE = process.env.NEXT_PUBLIC_UI_DEBUG_MODE === "true";

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

  } = xRxClient({
    orchestrator_host: NEXT_PUBLIC_ORCHESTRATOR_HOST,
    orchestrator_port: NEXT_PUBLIC_ORCHESTRATOR_PORT,
    orchestrator_path: NEXT_PUBLIC_ORCHESTRATOR_PATH,
    greeting_filename: NEXT_PUBLIC_GREETING_FILENAME,
    orchestrator_ssl: false,
  });

  const [message, setMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  /* Voice Activity Detection */
  useMicVAD({
    startOnLoad: true,
    onSpeechStart: () => {
      console.log("User started talking");
      setIsUserSpeaking(true);
    },
    onSpeechEnd: () => {
      console.log("User stopped talking");
      setIsUserSpeaking(false);
    },
  })

  /* Dark mode */
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

  
  /* constantly scroll to the bottom of the chat */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }
  useEffect(() => {
    scrollToBottom()
  }, [chatHistory]);

  /* Render widget */
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

  /* Click Handlers */
  const handleStartClick = () => {
    startAgent();
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

  return (
    <main className="mainContainer" style={{ paddingTop: '2rem' }}>
      {/* Move iconContainer here */}
      <div
        className={`iconContainer flex ${!isVoiceMode ? 'hidden' : ''}`}
        style={{ marginTop: '2rem' }}
      >
        <SyncLoader
          color={"#F15950"}
          loading={isAgentSpeaking}
          size={20}
        />
        <PulseLoader
          color={"#F15950"}
          loading={!isAgentSpeaking && isAgentThinking}
          size={20}
        />
        <div
          style={{
            width: isAgentSpeaking || isAgentThinking ? '0px' : '50px',
            height: isAgentSpeaking || isAgentThinking ? '0px' : '50px',
            borderRadius: '50%',
            backgroundColor: '#F15950',
            transition: 'all 0.5s',
            position: 'absolute',
            left: '50%',
            top: '40',
            transform: isAgentSpeaking || isAgentThinking ? 'translate(-50%, 0) scale(0)' : 'translate(-50%, 0) scale(1)',
            transformOrigin: 'center center'
          }}
        ></div>
      </div>

      <div className="contentContainer">
        <div className="title flex-none">
          <h1>The Simple App</h1>
          <p className="subtitle">
            With the simple app, you can check the latest stock prices and what's the weather like around the world
          </p>
        </div>
        <div className="bentoGrid">
          <div className="gridItem">
            <Image
              src="/weather.svg"
              alt="Weather Icon"
              width={70}
              height={70}
              className="iconImage"
            />
            <p>"What's the weather like in Menlo Park?"</p>
          </div>
          <div className="gridItem">
            <Image
              src="/stock_news.svg"
              alt="Stock News Icon"
              width={70}
              height={70}
              className="iconImage"
            />
            <p>"What did Apple stock do today?"</p>
          </div>
        </div>
      </div>

      {showStartButton && (
        <div className="startButtonContainer">
          <button
            className="widget-button"
            style={{ padding: '10px 30px' }}
            onClick={handleStartClick}
          >
            Start
          </button>
        </div>
      )}

      <div className="chatContainer flex-auto" style={{ minHeight: '50vh', display: 'flex', flexDirection: 'column' }}>
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
      <div className='inputContainer' style={{ marginTop: 'auto' }}>
        <div className='flex'>
          {
            isVoiceMode ?
            <div className="textInputContainer" >
              <div id='speechDetection' style={{ justifyContent: 'center' }}>
                <ScaleLoader
                  className="voiceIndicator"
                  color={"rgb(var(--foreground-rgb))"}
                  loading={isUserSpeaking}
                  radius={10}
                  height={20}
                  width={20}
                  speedMultiplier={2}
                />
                <ScaleLoader
                  className="voiceIndicator"
                  color={"rgb(var(--foreground-rgb))"}
                  loading={!isUserSpeaking}
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