import { useState } from 'preact/hooks';
import { ppfFutureValue } from '../../../lib/formulas/compound-growth';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import GrowthChart from '../ui/GrowthChart';

export default function PPFCalculator() {
  const [yearly, setYearly] = useState(150000);
  const [years, setYears] = useState(15);

  // PPF rate is currently 7.1% (Q1 FY 2025-26)
  const rate = 7.1;
  const result = ppfFutureValue(yearly, rate, years);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput id="yearly-deposit" label="Yearly Deposit" value={yearly} min={500} max={150000} step={500} prefix="₹" locale="en-IN" onChange={setYearly} />
        <SliderInput id="tenure" label="Tenure (minimum 15 years)" value={years} min={15} max={50} step={5} suffix=" Yr" onChange={setYears} />
        <div class="calc-note">Interest is at the current PPF rate of {rate}% a year, which the government sets every quarter.</div>
      </div>

      <div class="calc-answer">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Maturity value', value: result.totalValue, highlight: true },
            { label: 'Total deposited', value: result.investedAmount, seriesKey: 2 },
            { label: 'Interest earned', value: result.estimatedReturns },
          ]}
        />
      </div>

      <div class="calc-below">
        <GrowthChart currencyCode="INR" rows={result.yearlyBreakdown} title="How your PPF grows" valueLabel="PPF balance" investedLabel="Total deposited" />
      </div>
    </div>
  );
}
