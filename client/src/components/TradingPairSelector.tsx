import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TradingPairSelectorProps {
  onAnalyze: (pair: string, timeframe: string) => void;
  isLoading?: boolean;
}

export default function TradingPairSelector({ onAnalyze, isLoading = false }: TradingPairSelectorProps) {
  const [selectedPair, setSelectedPair] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1h");
  const [customPair, setCustomPair] = useState("");

  // Mock popular pairs - in real app these would come from API
  const popularPairs = [
    "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", 
    "BNBUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "LTCUSDT"
  ];

  const timeframes = [
    { value: "1m", label: "1 Minute" },
    { value: "5m", label: "5 Minutes" },
    { value: "15m", label: "15 Minutes" },
    { value: "1h", label: "1 Hour" },
    { value: "4h", label: "4 Hours" },
    { value: "1d", label: "1 Day" },
    { value: "1w", label: "1 Week" }
  ];

  const handleAnalyze = () => {
    const pair = customPair || selectedPair;
    onAnalyze(pair, timeframe);
    console.log(`Analyzing ${pair} on ${timeframe} timeframe`);
  };

  const handleQuickSelect = (pair: string) => {
    setSelectedPair(pair);
    setCustomPair("");
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Trading Pair Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Popular Pairs */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">Popular Trading Pairs</label>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            {popularPairs.map((pair) => (
              <Button
                key={pair}
                variant={selectedPair === pair && !customPair ? "default" : "outline"}
                size="sm"
                onClick={() => handleQuickSelect(pair)}
                className="text-xs font-mono"
                data-testid={`button-pair-${pair.toLowerCase()}`}
              >
                {pair}
              </Button>
            ))}
          </div>
        </div>

        {/* Custom Pair Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground" htmlFor="custom-pair">
            Or enter custom pair
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              id="custom-pair"
              placeholder="e.g. ETHBTC, DOGEUSDT"
              value={customPair}
              onChange={(e) => setCustomPair(e.target.value.toUpperCase())}
              className="pl-10 font-mono"
              data-testid="input-custom-pair"
            />
          </div>
        </div>

        {/* Timeframe Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">Timeframe</label>
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger data-testid="select-timeframe">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeframes.map((tf) => (
                <SelectItem key={tf.value} value={tf.value}>
                  {tf.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Analyze Button */}
        <Button 
          onClick={handleAnalyze}
          disabled={isLoading || (!selectedPair && !customPair)}
          className="w-full" 
          size="lg"
          data-testid="button-analyze"
        >
          {isLoading ? "Analyzing..." : "Analyze Trading Signals"}
        </Button>
      </CardContent>
    </Card>
  );
}