import { Badge } from "@/components/ui/badge";

export const HeroSection = () => {
  return <section className="relative py-20 px-4 overflow-hidden">
      
      <div className="relative max-w-7xl mx-auto text-left">
        <h1 className="text-4xl lg:text-6xl font-bold text-foreground mb-4">PulseIQ</h1>
        
        <p className="text-xl lg:text-2xl text-muted-foreground mb-8 max-w-4xl leading-relaxed">User sentiment analysis empowering growth and marketing strategies for consumer products</p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-start items-start">
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="w-2 h-2 bg-positive rounded-full" />
            <span>Identify most relevant sources to extract consumer sentiment from</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="w-2 h-2 bg-accent rounded-full" />
            <span>Classify consumer sentiment with Natural Language Processing</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="w-2 h-2 bg-primary rounded-full" />
            <span>Extract insights from structured outputs</span>
          </div>
        </div>
      </div>
    </section>;
};