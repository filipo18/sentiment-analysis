import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageSquare, Send } from "lucide-react";

interface ProductChatbotProps {
  selectedProduct: string;
  onProductSelect: (product: string) => void;
}

export const ProductChatbot = ({ selectedProduct, onProductSelect }: ProductChatbotProps) => {
  const [messages, setMessages] = useState([
    {
      type: "bot",
      content: "Hello! Which product would you like to perform sentiment analysis for? Tell me about your product launch or brand.",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    const userMessage = {
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    };
    
    const botResponse = {
      type: "bot",
      content: `Great! I'll help you analyze sentiment for "${inputValue}". You can now paste a Reddit thread link to get started with the analysis.`,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage, botResponse]);
    onProductSelect(inputValue);
    setInputValue("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  return (
    <Card className="p-6 shadow-card border-border/50 gradient-surface">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center">
          <MessageSquare className="w-5 h-5 text-primary-foreground" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Product Selection</h3>
          <Badge variant="beta" className="text-xs">
            Beta
          </Badge>
        </div>
      </div>
      
      <div className="space-y-4 h-64 overflow-y-auto mb-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg transition-smooth ${
                message.type === "user"
                  ? "gradient-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              <p className="text-sm">{message.content}</p>
              <span className="text-xs opacity-70 mt-1 block">
                {message.timestamp.toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Tell us about your product..."
          className="flex-1"
        />
        <Button onClick={handleSendMessage} size="sm" variant="hero" className="px-3">
          <Send className="w-4 h-4" />
        </Button>
      </div>
      
      {selectedProduct && (
        <div className="mt-4 p-3 gradient-accent rounded-lg">
          <p className="text-sm font-medium text-accent-foreground">
            Selected Product: {selectedProduct}
          </p>
        </div>
      )}
    </Card>
  );
};