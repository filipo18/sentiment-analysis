import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, Users, TrendingUp, MessageSquare, Activity } from "lucide-react";
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

interface AnalysisProgress {
  total_comments: number;
  analyzed_comments: number;
  unanalyzed_comments: number;
}

export const ProductDiscovery = () => {
  const [products, setProducts] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<DiscoveryResults | null>(null);
  const [selectedSubs, setSelectedSubs] = useState<Record<string, boolean>>({});
  const [analysisProgress, setAnalysisProgress] = useState<AnalysisProgress | null>(null);
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
    setSelectedSubs({});

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
        title: "Ingestion Complete",
        description: `Ingested ${data.comments_ingested || 0} comments successfully. ${data.comments_failed || 0} failed.`,
      });
      
      // Refresh analysis progress after ingestion
      await fetchAnalysisProgress();
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

  const fetchAnalysisProgress = async () => {
    try {
      const response = await fetch("http://localhost:8000/analyse-sentiment/progress");
      if (response.ok) {
        const data = await response.json();
        setAnalysisProgress(data);
      }
    } catch (error) {
      console.error("Failed to fetch analysis progress:", error);
    }
  };

  const handleAnalyzeSentiment = async () => {
    console.log("[UI] Analyze Sentiment clicked");
    setIsAnalyzing(true);
    
    // Start polling for progress
    const progressInterval = setInterval(fetchAnalysisProgress, 1000);
    
    try {
      const res = await fetch("http://localhost:8000/analyse-sentiment", {
        method: "POST",
      });
      const data = await res.json();
      console.log("[UI] /analyse-sentiment response:", data);
      toast({ title: "Analysis complete", description: `Updated: ${data.updated}` });
      
      // Fetch final progress
      await fetchAnalysisProgress();
    } catch (e) {
      console.error("[UI] analyse-sentiment failed", e);
      toast({ title: "Analysis failed", description: "See console for details", variant: "destructive" });
    } finally {
      setIsAnalyzing(false);
      clearInterval(progressInterval);
    }
  };

  // Poll for analysis progress when analyzing
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAnalyzing) {
      interval = setInterval(fetchAnalysisProgress, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAnalyzing]);

  // Fetch initial progress on component mount
  useEffect(() => {
    fetchAnalysisProgress();
  }, []);

  const handleToggleSub = (subreddit: string) => {
    setSelectedSubs(prev => ({ ...prev, [subreddit]: !prev[subreddit] }));
  };

  const handleIngestSelected = async () => {
    const chosen = Object.keys(selectedSubs).filter(k => selectedSubs[k]);
    if (chosen.length === 0) {
      toast({ title: "No subreddits selected", description: "Select at least one subreddit to ingest.", variant: "destructive" });
      return;
    }

    setIsIngesting(true);
    try {
      const productList = products
        .split(",")
        .map(p => p.trim())
        .filter(p => p.length > 0);

      const response = await fetch("http://localhost:8000/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ products: productList, subreddits: chosen }),
      });

      if (!response.ok) {
        const text = await response.text();
        console.error("[UI] /ingest failed:", response.status, text);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      toast({
        title: "Ingestion Complete",
        description: `Ingested ${data.comments_ingested || 0} comments successfully. ${data.comments_failed || 0} failed.`,
      });
      
      // Refresh analysis progress after ingestion
      await fetchAnalysisProgress();
    } catch (error) {
      console.error("Ingestion (selected) failed:", error);
      toast({
        title: "Ingestion Failed",
        description: "Failed to start ingestion for selected subreddits.",
        variant: "destructive",
      });
    } finally {
      setIsIngesting(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleDiscover();
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Input Section */}
      <Card className="w-full p-6 bg-background border border-border rounded-lg">
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
              disabled={isAnalyzing || !products.trim()}
              className="min-w-[160px]"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>Analyze Sentiment</>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Progress Section */}
      {analysisProgress && (
        <Card className="w-full p-6 bg-background border border-border rounded-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Analysis Progress
            </CardTitle>
            <CardDescription>
              Real-time status of comment sentiment analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-foreground">
                  {analysisProgress.total_comments}
                </div>
                <div className="text-sm text-muted-foreground">
                  Total Comments
                </div>
              </div>
              <div className="text-center p-4 bg-green-50 dark:bg-green-950/20 rounded-lg">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {analysisProgress.analyzed_comments}
                </div>
                <div className="text-sm text-muted-foreground">
                  Analyzed
                </div>
              </div>
              <div className="text-center p-4 bg-orange-50 dark:bg-orange-950/20 rounded-lg">
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {analysisProgress.unanalyzed_comments}
                </div>
                <div className="text-sm text-muted-foreground">
                  Pending
                </div>
              </div>
            </div>
            {analysisProgress.total_comments > 0 && (
              <div className="mt-4">
                <div className="flex justify-between text-sm text-muted-foreground mb-1">
                  <span>Progress</span>
                  <span>
                    {Math.round((analysisProgress.analyzed_comments / analysisProgress.total_comments) * 100)}%
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${(analysisProgress.analyzed_comments / analysisProgress.total_comments) * 100}%`
                    }}
                  ></div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {results && (
        <Card className="w-full p-6 bg-background border border-border rounded-lg">
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
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm text-muted-foreground">
                  Select subreddits to ingest, or use the generic Ingest button.
                </div>
                <Button onClick={handleIngestSelected} disabled={isIngesting} variant="outline">
                  {isIngesting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Ingesting...
                    </>
                  ) : (
                    <>Ingest Selected</>
                  )}
                </Button>
              </div>
            ) : null}
            {results.reddit && results.reddit.length > 0 ? (
              <div className="space-y-3">
                {results.reddit.map((channel, index) => (
                  <div
                    key={channel.channel_id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start gap-3 flex-1">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4"
                        checked={!!selectedSubs[channel.channel_id]}
                        onChange={() => handleToggleSub(channel.channel_id)}
                        aria-label={`Select ${channel.name}`}
                      />
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

