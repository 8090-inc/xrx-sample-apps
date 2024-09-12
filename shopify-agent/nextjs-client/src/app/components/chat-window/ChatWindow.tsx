import styles from "./ChatWindow.module.css";
import Image from "next/image";
import { ChatMessage } from "../../types/chat";

interface ChatWindowProps {
  chatHistory: ChatMessage[];
  isVoiceMode: boolean;
  message: string;
  handleMessageChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSendMessage: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  chatHistory,
  isVoiceMode,
  message,
  handleMessageChange,
  handleSendMessage
}) => {
  return (
    <div className={styles.chatMainContainer}>
      <div>
        {chatHistory
          .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
          .map((chat, index) => (
            <div key={index} className="flex">
              {chat.type === "widget" ? null : chat.sender === "user" ? (
                <div className={styles.userMessageContainer}>
                  <div
                    className={`${styles.userMessage} 
                    } ${isVoiceMode ? "hidden" : ""}`}
                  >
                    {chat.message}
                  </div>
                </div>
              ) : (
                <div className={styles.agentMessageContainer}>
                  <div
                    className={`${styles.agentMessage} ${
                      isVoiceMode ? "hidden" : ""
                    }`}
                  >
                    {chat.message}
                  </div>
                </div>
              )}
            </div>
          ))}
      </div>
      <div className={styles.inputContainer}>
        <div className={styles.textInputContainer}>
          <textarea
            placeholder="Type your message..."
            className={styles.textInputBox}
            value={message}
            onChange={handleMessageChange}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSendMessage();
              }
            }}
          />
          <Image
            src={"/send.svg"}
            width={20}
            height={20}
            alt="Send Message"
            className={styles.sendButton}
            onClick={handleSendMessage}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
