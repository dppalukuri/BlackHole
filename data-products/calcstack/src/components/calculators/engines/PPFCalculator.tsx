import { useState } from 'preact/hooks';
import { ppfFutureValue } from '../../../lib/formulas/compound-growth';
import SliderInput from '../ui/SliderInput';
import ResultCard from '../ui/ResultCard';
import DoughnutChart from '../ui/DoughnutChart';

export default function PPFCalculator() {
  const [yearly, setYearly] = useState(150000);
  const [years, setYears] = useState(15);

  // PPF rate is currently 7.1% (Q1 FY 2025-26)
  const rate = 7.1;
  const result = ppfFutureValue(yearly, rate, years);

  return (
    <div class="calculator-widget">
      <div class="calc-inputs">
        <SliderInput
          id="yearly-deposit"
          label="Yearly Deposit"
          value={yearly}
          min={500}
          max={150000}
          step={500}
          prefix="₹"
          onChange={setYearly}
        />
        <SliderInput
          id="tenure"
          label="Tenure (min 15 years)"
          value={years}
          min={15}
          max={50}
          step={5}
          suffix=" Yr"
          onChange={setYears}
        />

        <div class="gratuity-breakdown" style="margin-top: 0;">
          <p style="margin: 0; font-size: 0.9rem;">
            <strong>Current PPF Rate:</strong> {rate}% p.a. (set by government quarterly)
          </p>
        </div>
      </div>

      <div class="calc-results">
        <ResultCard
          currencyCode="INR"
          results={[
            { label: 'Total Deposited', value: result.investedAmount },
            { label: 'Interest Earned', value: result.estimatedReturns },
            { label: 'Maturity Value', value: result.totalValue, highlight: true },
          ]}
        />
        <DoughnutChart
          segments={[
            { label: 'Deposited', value: result.investedAmount, color: '#6366f1' },
            { label: 'Interest', value: result.estimatedReturns, color: '#22c55e' },
          ]}
        />
      </div>
    </div>
  );
}
