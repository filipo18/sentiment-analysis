import { HeroSection } from "@/components/HeroSection";
import { SentimentDashboard } from "@/components/SentimentDashboard";
import { ComingSoonSection } from "@/components/ComingSoonSection";
import { ProductDiscovery } from "@/components/ProductDiscovery";

const Index = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <HeroSection />

      {/* Product Discovery Section */}
      <section className="py-16 bg-background">
        <div className="container mx-auto px-4">
          <ProductDiscovery />
        </div>
      </section>

      {/* Dashboard 1: Sentiment Analysis */}
      <SentimentDashboard />

      {/* Dashboard 2: Coming Soon */}
      <ComingSoonSection />
    </div>
  );
};

export default Index;