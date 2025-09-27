import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, LineChart, Line, Tooltip, Cell } from "recharts";
import { supabase } from "@/integrations/supabase/client";
import { TrendingUp, BarChart3 } from "lucide-react";
export const SentimentDashboard = () => {
  const [sentimentData, setSentimentData] = useState<any[]>([]);
  const [timeSeriesData, setTimeSeriesData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPercentages, setShowPercentages] = useState(true);
  const [showTimeSeriesPercentages, setShowTimeSeriesPercentages] = useState(false);
  const fetchTimeSeriesData = async () => {
    try {
      const {
        data,
        error
      } = await supabase.from("main_reddit").select("comment_timestamp, comment_sentiment").not("comment_timestamp", "is", null).order("comment_timestamp", {
        ascending: false
      }).limit(1000);
      if (data && !error) {
        // Group by date and sentiment
        const dailyData: {
          [key: string]: {
            positive: number;
            negative: number;
            neutral: number;
          };
        } = {};
        data.forEach(item => {
          const date = new Date(item.comment_timestamp).toISOString().split('T')[0];
          const sentiment = item.comment_sentiment?.toLowerCase() || 'neutral';
          if (!dailyData[date]) {
            dailyData[date] = {
              positive: 0,
              negative: 0,
              neutral: 0
            };
          }
          if (sentiment === 'positive' || sentiment === 'negative' || sentiment === 'neutral') {
            dailyData[date][sentiment]++;
          }
        });

        // Convert to array and get last 7 days with percentages
        const timeSeriesArray = Object.entries(dailyData).map(([date, counts]) => {
          const total = counts.positive + counts.negative + counts.neutral;
          if (total === 0) {
            return {
              date,
              positive: 0,
              negative: 0,
              neutral: 0,
              positivePercent: 0,
              negativePercent: 0,
              neutralPercent: 0,
            };
          }
          
          // Calculate exact percentages
          const positivePercent = (counts.positive / total) * 100;
          const negativePercent = (counts.negative / total) * 100;
          const neutralPercent = (counts.neutral / total) * 100;
          
          // Round percentages ensuring they add up to 100
          const roundedPositive = Math.round(positivePercent);
          const roundedNegative = Math.round(negativePercent);
          const roundedNeutral = 100 - roundedPositive - roundedNegative;
          
          return {
            date,
            positive: counts.positive,
            negative: counts.negative,
            neutral: counts.neutral,
            positivePercent: roundedPositive,
            negativePercent: roundedNegative,
            neutralPercent: Math.max(0, roundedNeutral), // Ensure non-negative
          };
        }).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()).slice(-7);
        setTimeSeriesData(timeSeriesArray);
      }
    } catch (error) {
      console.error("Error fetching time series data:", error);
    }
  };
  const fetchSentimentData = async () => {
    try {
      // Fetch sentiment percentages
      const {
        data: sentimentResults
      } = await supabase.from("main_reddit").select("comment_sentiment");
      if (sentimentResults) {
        const sentimentCounts = sentimentResults.reduce((acc, item) => {
          const sentiment = item.comment_sentiment?.toLowerCase() || "neutral";
          acc[sentiment] = (acc[sentiment] || 0) + 1;
          return acc;
        }, {
          positive: 0,
          negative: 0,
          neutral: 0
        });
        const total = Object.values(sentimentCounts).reduce((sum: any, count: any) => sum + count, 0);
        const percentageData = [{
          sentiment: "Positive",
          percentage: Math.round(sentimentCounts.positive / total * 100),
          count: sentimentCounts.positive,
          color: "hsl(var(--positive))"
        }, {
          sentiment: "Negative",
          percentage: Math.round(sentimentCounts.negative / total * 100),
          count: sentimentCounts.negative,
          color: "hsl(var(--negative))"
        }, {
          sentiment: "Neutral",
          percentage: Math.round(sentimentCounts.neutral / total * 100),
          count: sentimentCounts.neutral,
          color: "hsl(var(--neutral))"
        }];
        setSentimentData(percentageData);
      }
    } catch (error) {
      console.error("Error fetching sentiment data:", error);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetchSentimentData();
    fetchTimeSeriesData();
  }, []);
  if (loading) {
    return <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
          </div>
        </div>
      </section>;
  }
  return <section className="py-16 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-left mb-12">
          <h2 className="text-3xl font-bold mb-4 gradient-primary bg-clip-text text-transparent">
            Sentiment Analysis
          </h2>
          <h3 className="text-2xl font-semibold mb-4 text-foreground">
            Sentiment over time
          </h3>
          <p className="text-muted-foreground">
            Real-time insights from Reddit conversations
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Sentiment Percentage Bar Chart */}
          <Card className="p-6 shadow-card border-border/50 gradient-surface">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Sentiment Distribution</h3>
                  <p className="text-sm text-muted-foreground">
                    Percentage breakdown of comment sentiments
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Label htmlFor="sentiment-toggle" className="text-sm">%</Label>
                <Switch
                  id="sentiment-toggle"
                  checked={showPercentages}
                  onCheckedChange={setShowPercentages}
                />
                <Label htmlFor="sentiment-toggle" className="text-sm">#</Label>
              </div>
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sentimentData}>
                  <XAxis dataKey="sentiment" axisLine={false} tickLine={false} tick={{
                  fill: "hsl(var(--muted-foreground))",
                  fontSize: 12
                }} />
                  <YAxis axisLine={false} tickLine={false} tick={{
                  fill: "hsl(var(--muted-foreground))",
                  fontSize: 12
                }} />
                  <Tooltip contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "0.5rem",
                  color: "hsl(var(--popover-foreground))"
                }} />
                  <Bar dataKey={showPercentages ? "percentage" : "count"} radius={4}>
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-3 gap-4 mt-6">
              {sentimentData.map(item => <div key={item.sentiment} className="text-center p-3 bg-muted/30 rounded-lg">
                  <div className="text-2xl font-bold" style={{
                color: item.color
              }}>
                    {showPercentages ? `${item.percentage}%` : item.count}
                  </div>
                  <div className="text-sm text-muted-foreground">{item.sentiment}</div>
                  <div className="text-xs text-muted-foreground">{item.count} comments</div>
                </div>)}
            </div>
          </Card>

          {/* Time Series Chart */}
          <Card className="p-6 shadow-card border-border/50 gradient-surface">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full gradient-accent flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-accent-foreground" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Daily Sentiment Trends</h3>
                  <p className="text-sm text-muted-foreground">
                    7-day sentiment progression
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Label htmlFor="timeseries-toggle" className="text-sm">%</Label>
                <Switch
                  id="timeseries-toggle"
                  checked={showTimeSeriesPercentages}
                  onCheckedChange={setShowTimeSeriesPercentages}
                />
                <Label htmlFor="timeseries-toggle" className="text-sm">#</Label>
              </div>
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeSeriesData}>
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{
                  fill: "hsl(var(--muted-foreground))",
                  fontSize: 12
                }} tickFormatter={value => new Date(value).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric'
                })} />
                  <YAxis axisLine={false} tickLine={false} tick={{
                  fill: "hsl(var(--muted-foreground))",
                  fontSize: 12
                }} />
                  <Tooltip contentStyle={{
                  backgroundColor: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "0.5rem",
                  color: "hsl(var(--popover-foreground))"
                }} />
                  <Line 
                    type="monotone" 
                    dataKey={showTimeSeriesPercentages ? "positivePercent" : "positive"} 
                    stroke="hsl(var(--positive))" 
                    strokeWidth={3} 
                    dot={{
                      fill: "hsl(var(--positive))",
                      strokeWidth: 0,
                      r: 4
                    }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey={showTimeSeriesPercentages ? "negativePercent" : "negative"} 
                    stroke="hsl(var(--negative))" 
                    strokeWidth={3} 
                    dot={{
                      fill: "hsl(var(--negative))",
                      strokeWidth: 0,
                      r: 4
                    }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey={showTimeSeriesPercentages ? "neutralPercent" : "neutral"} 
                    stroke="hsl(var(--neutral))" 
                    strokeWidth={3} 
                    dot={{
                      fill: "hsl(var(--neutral))",
                      strokeWidth: 0,
                      r: 4
                    }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-3 gap-4 mt-6">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-positive rounded-full" />
                <span className="text-sm">Positive</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-negative rounded-full" />
                <span className="text-sm">Negative</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-neutral rounded-full" />
                <span className="text-sm">Neutral</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>;
};