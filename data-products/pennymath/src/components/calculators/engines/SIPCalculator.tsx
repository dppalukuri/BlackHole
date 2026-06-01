import { useState } from 'preact/hooks';
import { sipFutureValue } from '../../../lib/formulas/compound-growth';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';

interface SIPCalculatorProps {
  currency: { code: string; symbol: string };
  defaults?: {
    monthlyInvestment?: number;
    expectedReturn?: number;
    timePeriod?: number;
  };
}

export default function SIPCalculator({ currency, defaults }: SIPCalculatorProps) {
  const [monthly, setMonthly] = useState(defaults?.monthlyInvestment ?? 5000);
  const [rate, setRate] = useState(defaults?.expectedReturn ?? 12);
  const [years, setYears] = useState(defaults?.timePeriod ?? 10);

  const result = sipFutureValue(monthly, rate, years);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="monthly-investment"
          label="Monthly Investment"
          value={monthly}
          min={500}
          max={1000000}
          step={500}
          prefix={currency.symbol}
          onChange={setMonthly}
        />
        <SliderInput
          id="expected-return"
          label="Expected Return Rate (p.a.)"
          value={rate}
          min={1}
          max={30}
          step={0.5}
          suffix="%"
          onChange={setRate}
        />
        <SliderInput
          id="time-period"
          label="Time Period"
          value={years}
          min={1}
          max={40}
          step={1}
          suffix=" Yr"
          onChange={setYears}
        />
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode={currency.code}
          results={[
            { label: 'Invested Amount', value: result.investedAmount },
            { label: 'Est. Returns', value: result.estimatedReturns },
            { label: 'Total Value', value: result.totalValue, highlight: true },
          ]}
        />
        <DoughnutChart
          segments={[
            { label: 'Invested Amount', value: result.investedAmount, color: '#6366f1' },
            { label: 'Est. Returns', value: result.estimatedReturns, color: '#22c55e' },
          ]}
        />
      </div>
    </div>
  );
}
