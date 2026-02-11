# Pricing Automation Frontend Module

## Overview
Complete frontend implementation for the Pricing Automation module, including interactive price simulators, KU calculators, and pricing strategy management.

## Files Created

### Core Module Files
- `frontend/src/modules/pricing/types.ts` - TypeScript type definitions
- `frontend/src/modules/pricing/hooks.ts` - React Query hooks for API calls

### Components
- `frontend/src/modules/pricing/components/PricingDashboard.tsx` - Main pricing dashboard
- `frontend/src/modules/pricing/components/PriceSimulator.tsx` - Interactive price/royalty calculator
- `frontend/src/modules/pricing/components/KUCalculator.tsx` - Kindle Unlimited revenue calculator
- `frontend/src/modules/pricing/components/StrategyCards.tsx` - Pricing strategy cards
- `frontend/src/modules/pricing/components/PriceHistory.tsx` - Price change history chart
- `frontend/src/modules/pricing/components/RoyaltyBreakdown.tsx` - Royalty breakdown visualization

### Pages
- `frontend/src/app/(dashboard)/pricing/page.tsx` - Main pricing page
- `frontend/src/app/(dashboard)/pricing/simulator/page.tsx` - Price simulator page
- `frontend/src/app/(dashboard)/pricing/loading.tsx` - Loading skeleton

### UI Components
- `frontend/src/components/ui/slider.tsx` - Radix UI slider component
- `frontend/src/components/ui/label.tsx` - Radix UI label component

### Tests
- `frontend/src/app/(dashboard)/pricing/__tests__/page.test.tsx` - Page tests

## Required Package Installation

Before running, install the missing Radix UI slider package:

```bash
cd frontend
npm install @radix-ui/react-slider
```

## Features

### 1. Price Simulator
- Interactive sliders for price adjustment
- Real-time royalty calculation (35% and 70% tiers)
- Elasticity modeling for sales projections
- Breakeven analysis
- Recommended price points

### 2. KU Calculator
- Compare KU exclusive vs. wide distribution revenue
- KENP page rate calculations
- Monthly and annual projections
- Detailed revenue breakdowns
- Smart recommendations

### 3. Pricing Strategies
- Visual strategy cards (Competitive, Value-Based, Penetration, Dynamic, Promotional)
- Active rules management
- Strategy recommendations

### 4. Price History
- Historical price change visualization with Recharts
- Dual-axis chart (price + sales)
- Summary statistics

### 5. Royalty Breakdown
- Bar chart showing royalties at different price points
- Tier visualization (35% vs. 70%)
- Sweet spot analysis

## API Integration

All components use React Query hooks from `hooks.ts`:
- `useSimulatePrice()` - POST /api/v1/pricing/simulate
- `useKUCalculator()` - POST /api/v1/pricing/ku-calculator
- `usePricingRules()` - GET /api/v1/pricing/rules
- `useCompetitorPrices()` - GET /api/v1/pricing/competitors/{bookId}

## Testing

Run tests:
```bash
cd frontend
npm test pricing
```

## Design Decisions

1. **Sliders + Number Inputs**: Both UI controls for accessibility and precision
2. **Mock Data**: Price history uses mock data as placeholder (backend endpoint not yet implemented)
3. **Recharts**: Leverages existing recharts dependency for consistent charting
4. **Responsive Design**: Mobile-first with Tailwind CSS grid layouts
5. **Error States**: Graceful degradation with empty state messaging

## Next Steps

1. Install `@radix-ui/react-slider` package
2. Connect price history to real backend endpoint when available
3. Add book selector dropdown to filter by specific books
4. Implement A/B test management UI
5. Add promotion scheduling calendar view
