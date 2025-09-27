import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link, ExternalLink } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

interface RedditAnalysisFormProps {
  redditUrl: string;
  onUrlChange: (url: string) => void;
}

export const RedditAnalysisForm = ({ redditUrl, onUrlChange }: RedditAnalysisFormProps) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { toast } = useToast();

  const handleAnalyze = async () => {
    if (!redditUrl) {
      toast({
        title: "URL Required",
        description: "Please enter a Reddit thread URL to analyze.",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    
    // Simulate analysis process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    toast({
      title: "Analysis Complete",
      description: "Sentiment analysis has been updated with new data.",
    });
    
    setIsAnalyzing(false);
  };

  return (
    <Card className="p-6 shadow-card border-border/50 gradient-surface h-fit">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
          <Link className="w-5 h-5 text-secondary-foreground" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Reddit Thread Analysis</h3>
          <p className="text-sm text-muted-foreground">
            Analyze sentiment from Reddit discussions
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="reddit-url" className="text-sm font-medium">
            Reddit Thread URL
          </Label>
          <Input
            id="reddit-url"
            value={redditUrl}
            onChange={(e) => onUrlChange(e.target.value)}
            placeholder="https://reddit.com/r/technology/comments/..."
            className="mt-1"
          />
        </div>

        <Button 
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          variant="accent"
          className="w-full transition-smooth"
        >
          {isAnalyzing ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              Analyzing Thread...
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <ExternalLink className="w-4 h-4" />
              Analyze Sentiment
            </div>
          )}
        </Button>

        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium text-sm mb-2">Sample Data Available</h4>
          <p className="text-xs text-muted-foreground">
            The dashboard below shows sentiment analysis from existing Reddit data.
            Submit a URL to add new analysis results.
          </p>
        </div>
      </div>
    </Card>
  );
};