import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, MessageSquare, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface Comment {
  comment_id: number;
  brand_name: string;
  product_name: string;
  comment_text: string;
  comment_sentiment: string;
  comment_timestamp: string;
  thread_name: string;
  upvotes: number;
  attribute_discussed: string;
  attribute_sentiment: string;
  similarity_score: number;
}

interface SearchResponse {
  query: string;
  comments: Comment[];
  count: number;
}

interface QAResponse {
  answer: string;
  relevant_comments: Comment[];
  sources: number;
}

export const CommentSearch = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [qaQuery, setQaQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [qaResults, setQaResults] = useState<QAResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"search" | "qa">("search");

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/qa/search?query=${encodeURIComponent(searchQuery)}&limit=10`);
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!qaQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/qa/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: qaQuery,
          limit: 5,
        }),
      });
      const data = await response.json();
      setQaResults(data);
    } catch (error) {
      console.error("Q&A failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case "positive":
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case "negative":
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case "positive":
        return "bg-green-100 text-green-800 border-green-200";
      case "negative":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <section className="py-16 px-4 bg-background">
      <div className="max-w-7xl mx-auto">
        {/* Dark separator line */}
        <div className="w-full h-px bg-gray-800 mb-8"></div>
        
        <div className="text-left mb-8">
          <h2 className="text-3xl font-bold mb-4">
            Search & Ask Questions About Comments
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl">
            Find relevant comments using semantic search or ask natural language questions about your data
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-6">
          <Button
            variant={activeTab === "search" ? "default" : "outline"}
            onClick={() => setActiveTab("search")}
            className="flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Search Comments
          </Button>
          <Button
            variant={activeTab === "qa" ? "default" : "outline"}
            onClick={() => setActiveTab("qa")}
            className="flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            Ask Questions
          </Button>
        </div>

        {/* Search Tab */}
        {activeTab === "search" && (
          <div className="space-y-6">
            <div className="flex gap-4">
              <Input
                placeholder="Search for comments about battery life, design, price..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                className="flex-1"
              />
              <Button onClick={handleSearch} disabled={loading}>
                {loading ? "Searching..." : "Search"}
              </Button>
            </div>

            {searchResults && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold">Search Results</h3>
                  <Badge variant="secondary">{searchResults.count} comments found</Badge>
                </div>
                
                <div className="grid gap-4">
                  {searchResults.comments.map((comment) => (
                    <Card key={comment.comment_id} className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{comment.brand_name}</Badge>
                          {comment.product_name && (
                            <Badge variant="outline">{comment.product_name}</Badge>
                          )}
                          <Badge className={getSentimentColor(comment.comment_sentiment)}>
                            {getSentimentIcon(comment.comment_sentiment)}
                            <span className="ml-1">{comment.comment_sentiment}</span>
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {comment.upvotes} upvotes
                        </div>
                      </div>
                      
                      <p className="text-sm mb-2">{comment.comment_text}</p>
                      
                      {comment.thread_name && (
                        <p className="text-xs text-muted-foreground">
                          From: {comment.thread_name}
                        </p>
                      )}
                      
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-muted-foreground">
                          {new Date(comment.comment_timestamp).toLocaleDateString()}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {Math.round(comment.similarity_score * 100)}% match
                        </Badge>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Q&A Tab */}
        {activeTab === "qa" && (
          <div className="space-y-6">
            <div className="flex gap-4">
              <Input
                placeholder="What do people think about battery life? How is the camera quality?"
                value={qaQuery}
                onChange={(e) => setQaQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleAskQuestion()}
                className="flex-1"
              />
              <Button onClick={handleAskQuestion} disabled={loading}>
                {loading ? "Thinking..." : "Ask"}
              </Button>
            </div>

            {qaResults && (
              <div className="space-y-4">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-3">Answer</h3>
                  <p className="text-sm leading-relaxed">{qaResults.answer}</p>
                  <div className="mt-3 flex items-center gap-2">
                    <Badge variant="secondary">{qaResults.sources} sources</Badge>
                  </div>
                </Card>

                {qaResults.relevant_comments.length > 0 && (
                  <div className="space-y-4">
                    <h4 className="text-md font-semibold">Supporting Comments</h4>
                    <div className="grid gap-4">
                      {qaResults.relevant_comments.map((comment) => (
                        <Card key={comment.comment_id} className="p-4">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{comment.brand_name}</Badge>
                              {comment.product_name && (
                                <Badge variant="outline">{comment.product_name}</Badge>
                              )}
                              <Badge className={getSentimentColor(comment.comment_sentiment)}>
                                {getSentimentIcon(comment.comment_sentiment)}
                                <span className="ml-1">{comment.comment_sentiment}</span>
                              </Badge>
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {comment.upvotes} upvotes
                            </div>
                          </div>
                          
                          <p className="text-sm mb-2">{comment.comment_text}</p>
                          
                          {comment.thread_name && (
                            <p className="text-xs text-muted-foreground">
                              From: {comment.thread_name}
                            </p>
                          )}
                          
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs text-muted-foreground">
                              {new Date(comment.comment_timestamp).toLocaleDateString()}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {Math.round(comment.similarity_score * 100)}% match
                            </Badge>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
