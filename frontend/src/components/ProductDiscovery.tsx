import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, Users, TrendingUp, MessageSquare } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface DiscoverResponse {
  platform: string;
  channel_id: string;
  name: string;
  score: number;
  metrics: {
    mentions: number;
    avg_score: number;
    comments: number;
  };
}

interface DiscoveryResults {
  reddit: DiscoverResponse[];
}

export const ProductDiscovery = () => {
  const [products, setProducts] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [results, setResults] = useState<DiscoveryResults | null>(null);
  const { toast } = useToast();

  const handleDiscover = async () => {
    if (!products.trim()) {
      toast({
        title: "Error",
        description: "Please enter at least one product name",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setResults(null);

    try {
      const productList = products
        .split(",")
        .map(p => p.trim())
        .filter(p => p.length > 0);

      console.log("[UI] Calling /discover with:", productList);
      const response = await fetch("http://localhost:8000/discover", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          products: productList,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        console.error("[UI] /discover failed:", response.status, text);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: DiscoveryResults = await response.json();
      console.log("[UI] /discover response:", data);
      setResults(data);

      toast({
        title: "Discovery Complete",
        description: `Found ${data.reddit?.length || 0} relevant Reddit channels`,
      });
    } catch (error) {
      console.error("Discovery failed:", error);
      toast({
        title: "Discovery Failed",
        description: "Failed to discover channels. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleIngest = async () => {
    setIsIngesting(true);
    try {
      const productList = products
        .split(",")
        .map(p => p.trim())
        .filter(p => p.length > 0);

      const hasProducts = productList.length > 0;

      console.log("[UI] Calling /ingest with:", hasProducts ? productList : "<defaults>");
      const response = await fetch("http://localhost:8000/ingest", {
        method: "POST",
        headers: hasProducts ? { "Content-Type": "application/json" } : undefined,
        body: hasProducts ? JSON.stringify({ products: productList }) : undefined,
      });

      if (!response.ok) {
        const text = await response.text();
        console.error("[UI] /ingest failed:", response.status, text);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("[UI] /ingest response:", data);
      toast({
        title: "Ingestion Started",
        description: `Status: ${data.status}. Products: ${(data.products || []).join(", ")}`,
      });
    } catch (error) {
      console.error("Ingestion failed:", error);
      toast({
        title: "Ingestion Failed",
        description: "Failed to start ingestion. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsIngesting(false);
    }
  };

  const handleAnalyzeSentiment = async () => {
    console.log("[UI] Analyze Sentiment clicked");
    try {
      const res = await fetch("http://localhost:8000/analyse-sentiment", {
        method: "POST",
      });
      const data = await res.json();
      console.log("[UI] /analyse-sentiment response:", data);
      toast({ title: "Analysis complete", description: `Updated: ${data.updated}` });
    } catch (e) {
      console.error("[UI] analyse-sentiment failed", e);
      toast({ title: "Analysis failed", description: "See console for details", variant: "destructive" });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleDiscover();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Product Discovery
          </CardTitle>
          <CardDescription>
            Enter product names separated by commas to discover relevant Reddit channels
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="e.g., iPhone, Samsung Galaxy, Google Pixel"
              value={products}
              onChange={(e) => setProducts(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="flex-1"
            />
            <Button 
              onClick={handleDiscover} 
              disabled={isLoading || !products.trim()}
              className="min-w-[120px]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Discovering...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Discover
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={handleIngest}
              disabled={isIngesting || !products.trim()}
              className="min-w-[120px]"
            >
              {isIngesting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Ingesting...
                </>
              ) : (
                <>Ingest</>
              )}
            </Button>
            <Button
              variant="secondary"
              onClick={handleAnalyzeSentiment}
              disabled={!products.trim()}
              className="min-w-[160px]"
            >
              Analyze Sentiment
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Discovery Results
            </CardTitle>
            <CardDescription>
              Found {results.reddit?.length || 0} relevant Reddit channels
            </CardDescription>
          </CardHeader>
          <CardContent>
            {results.reddit && results.reddit.length > 0 ? (
              <div className="space-y-3">
                {results.reddit.map((channel, index) => (
                  <div
                    key={channel.channel_id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-lg">{channel.name}</h3>
                        <Badge variant="secondary" className="text-xs">
                          {channel.platform}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <TrendingUp className="h-4 w-4" />
                          <span>Score: {channel.score.toFixed(1)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <MessageSquare className="h-4 w-4" />
                          <span>{channel.metrics.mentions} mentions</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          <span>{channel.metrics.comments} comments</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        #{index + 1}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Avg Score: {channel.metrics.avg_score.toFixed(1)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No channels found for the specified products.</p>
                <p className="text-sm">Try different product names or check your spelling.</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
