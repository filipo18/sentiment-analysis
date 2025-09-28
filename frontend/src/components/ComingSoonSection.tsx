import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { BarChart3 } from "lucide-react";
import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
interface AttributeData {
  attribute: string;
  positive: number;
  negative: number;
  neutral: number;
  positivePercent?: number;
  negativePercent?: number;
  neutralPercent?: number;
}

export const ComingSoonSection = () => {
  const [attributeData, setAttributeData] = useState<AttributeData[]>([]);
  const [loading, setLoading] = useState(true);
  const [attributeCount, setAttributeCount] = useState([10]);
  const [showAttributePercentages, setShowAttributePercentages] = useState(false);

  const fetchAttributeData = async () => {
    try {
      const { data, error } = await supabase
        .from('main_reddit')
        .select('attribute_discussed, attribute_sentiment')
        .not('attribute_discussed', 'is', null)
        .not('attribute_sentiment', 'is', null);

      if (error) throw error;

      // Transform data for stacked bar chart
      const attributeMap: Record<string, AttributeData> = {};
      data.forEach(item => {
        const attr = item.attribute_discussed;
        const sentiment = item.attribute_sentiment;
        
        if (!attributeMap[attr]) {
          attributeMap[attr] = { attribute: attr, positive: 0, negative: 0, neutral: 0 };
        }
        attributeMap[attr][sentiment as keyof Omit<AttributeData, 'attribute'>]++;
      });

      const chartData = Object.values(attributeMap)
        .filter(item => item.positive > 0 || item.negative > 0 || item.neutral > 0) // Show attributes with any sentiment
        .filter(item => item.attribute !== "general") // Exclude "general" attribute
        .map(item => {
          const total = item.positive + item.negative + item.neutral;
          return {
            ...item,
            positivePercent: total > 0 ? Math.round((item.positive / total) * 100) : 0,
            negativePercent: total > 0 ? Math.round((item.negative / total) * 100) : 0,
            neutralPercent: total > 0 ? Math.round((item.neutral / total) * 100) : 0,
          };
        })
        .sort((a, b) => (b.positive + b.negative + b.neutral) - (a.positive + a.negative + a.neutral)) // Sort by total sentiment count
        .slice(0, attributeCount[0]); // Show dynamic number of attributes

      setAttributeData(chartData);
    } catch (error) {
      console.error('Error fetching attribute data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttributeData();
  }, [attributeCount]);

  const chartConfig = {
    positive: {
      label: "Positive",
      color: "hsl(142, 76%, 36%)", // Green
    },
    negative: {
      label: "Negative", 
      color: "hsl(0, 84%, 60%)", // Red
    },
    neutral: {
      label: "Neutral",
      color: "hsl(220, 70%, 50%)", // Blue
    },
  };

  return <section className="py-8 px-4">
      <div className="max-w-7xl mx-auto">
      <div className="w-full h-px bg-gray-800 mt-16 mb-8"></div>

        <div className="text-left mb-12">

          <h2 className="text-3xl font-bold mb-4">
            Track sentiment on key product attributes
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl">
            Identify attributes associated with a product and sentiment around each identified attribute
          </p>
        </div>

        {/* Attribute Chart */}
        <Card className="p-6 bg-background border border-border rounded-lg mb-12">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Sentiment by Product Attributes
              </CardTitle>
              <div className="flex items-center space-x-2">
                <Label htmlFor="attribute-toggle" className="text-sm">%</Label>
                <Switch
                  id="attribute-toggle"
                  checked={showAttributePercentages}
                  onCheckedChange={setShowAttributePercentages}
                />
                <Label htmlFor="attribute-toggle" className="text-sm">#</Label>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium">Number of attributes to display:</label>
                <span className="text-sm text-muted-foreground">{attributeCount[0]}</span>
              </div>
              <Slider
                value={attributeCount}
                onValueChange={setAttributeCount}
                min={1}
                max={20}
                step={1}
                className="w-full"
              />
            </div>
            {loading ? (
              <div className="h-96 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : (
              <ChartContainer config={chartConfig} className="h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={attributeData} 
                    margin={{ top: 20, right: 20, left: 60, bottom: 120 }}
                    barCategoryGap="10%"
                  >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis 
                      dataKey="attribute" 
                      angle={-45}
                      textAnchor="end"
                      height={120}
                      interval={0}
                      fontSize={14}
                      tick={{ fontSize: 14 }}
                      width={80}
                    />
                    <YAxis 
                      tick={{ fontSize: 14 }}
                      width={50}
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey={showAttributePercentages ? "positivePercent" : "positive"} stackId="a" fill="hsl(142, 76%, 36%)" name="Positive" />
                    <Bar dataKey={showAttributePercentages ? "neutralPercent" : "neutral"} stackId="a" fill="hsl(220, 70%, 50%)" name="Neutral" />
                    <Bar dataKey={showAttributePercentages ? "negativePercent" : "negative"} stackId="a" fill="hsl(0, 84%, 60%)" name="Negative" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

      </div>
    </section>;
};