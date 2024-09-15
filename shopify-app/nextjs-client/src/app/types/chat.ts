export type ChatMessage = {
  sender: string;
  message: string;
  widget?: any;
  timestamp: Date;
  type?: string;
};
